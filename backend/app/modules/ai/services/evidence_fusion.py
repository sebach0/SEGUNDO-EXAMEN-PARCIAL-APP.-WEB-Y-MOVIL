from __future__ import annotations

from collections import defaultdict

from app.modules.ai.schemas import (
    DamageConflict,
    DamageEvidenceItem,
    DamageEvidenceSupport,
    DamagePrediction,
    IncidentCategory,
    SeverityLevel,
)
from app.modules.ai.text_normalize import normalize_for_match

_TEXT_WEIGHT = 0.30
_AUDIO_WEIGHT = 0.25
_IMAGE_WEIGHT = 0.45

_DAMAGE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "CHOQUE": ("choque", "colision", "accidente", "impacto", "abollad", "golpe"),
    "VIDRIOS_ROTOS": ("vidrio", "parabrisas", "ventana rota", "cristal", "espejo roto"),
    "LLANTA_PINCHADA": ("llanta", "neumatico", "pinchad", "goma", "rueda", "desinflad"),
    "FUGA_LIQUIDO": ("fuga", "aceite", "liquido", "gote", "derrame"),
    "SOBRECALENTAMIENTO": ("sobrecalent", "temperatura alta", "humo"),
    "BATERIA": ("bateria", "no enciende", "arranque", "descargad", "tablero"),
    "FALLA_MOTOR": ("motor", "check engine", "vibracion", "apago"),
}

_CRITICAL_LABELS = {"CHOQUE", "FUGA_LIQUIDO"}
_HIGH_LABELS = {"SOBRECALENTAMIENTO", "FALLA_MOTOR"}


def _severity_for(label: str, confidence: float) -> SeverityLevel:
    if label in _CRITICAL_LABELS and confidence >= 0.45:
        return SeverityLevel.CRITICA
    if label in _HIGH_LABELS and confidence >= 0.45:
        return SeverityLevel.ALTA
    if confidence >= 0.70:
        return SeverityLevel.ALTA
    if confidence >= 0.45:
        return SeverityLevel.MEDIA
    return SeverityLevel.BAJA


def _merge_audio(base_audio: str | None, audios: list[str]) -> str:
    parts = []
    if base_audio and base_audio.strip():
        parts.append(base_audio.strip())
    parts.extend(a.strip() for a in audios if a and a.strip())
    return " ".join(parts).strip()


def _flatten_vision(
    hallazgos_vision: list[str],
    hallazgos_por_imagen: list[list[str]],
) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for idx, group in enumerate(hallazgos_por_imagen, start=1):
        for h in group:
            if h and h.strip():
                items.append((f"img-{idx}", h))
    for h in hallazgos_vision:
        if h and h.strip():
            items.append(("img-0", h))
    return items


def fuse_incident_evidence(
    *,
    texto_cliente: str | None,
    transcripcion_audio: str | None,
    transcripciones_audio: list[str],
    hallazgos_vision: list[str],
    hallazgos_vision_por_imagen: list[list[str]],
) -> tuple[list[DamagePrediction], bool, list[str]]:
    text_norm = normalize_for_match(texto_cliente)
    audio_joined = _merge_audio(transcripcion_audio, transcripciones_audio)
    audio_norm = normalize_for_match(audio_joined)
    vision_items = _flatten_vision(hallazgos_vision, hallazgos_vision_por_imagen)

    raw_scores: dict[str, float] = defaultdict(float)
    reasons: dict[str, list[str]] = defaultdict(list)
    support: dict[str, DamageEvidenceSupport] = defaultdict(DamageEvidenceSupport)

    for label, keywords in _DAMAGE_KEYWORDS.items():
        for keyword in keywords:
            nk = normalize_for_match(keyword)
            if nk and nk in text_norm:
                raw_scores[label] += _TEXT_WEIGHT
                reasons[label].append(f"texto menciona '{keyword}'")
                support[label].text.append(DamageEvidenceItem(evidencia_id="txt-1", score=0.75))
                break
        for keyword in keywords:
            nk = normalize_for_match(keyword)
            if nk and nk in audio_norm:
                raw_scores[label] += _AUDIO_WEIGHT
                reasons[label].append(f"audio menciona '{keyword}'")
                support[label].audio.append(DamageEvidenceItem(evidencia_id="aud-1", score=0.70))
                break

    image_weight = _IMAGE_WEIGHT / max(1, len(vision_items))
    for evidence_id, finding in vision_items:
        norm_finding = normalize_for_match(finding)
        for label, keywords in _DAMAGE_KEYWORDS.items():
            for keyword in keywords:
                nk = normalize_for_match(keyword)
                if nk and nk in norm_finding:
                    raw_scores[label] += image_weight
                    reasons[label].append(f"imagen reporta '{finding}'")
                    support[label].image.append(
                        DamageEvidenceItem(evidencia_id=evidence_id, score=min(1.0, image_weight * 2.0))
                    )
                    break

    damages: list[DamagePrediction] = []
    for label, score in raw_scores.items():
        confidence = max(0.0, min(1.0, score))
        if confidence < 0.30:
            continue
        damages.append(
            DamagePrediction(
                label=label,
                confidence=round(confidence, 2),
                severity=_severity_for(label, confidence),
                evidence_support=support[label],
                reasons=list(dict.fromkeys(reasons[label]))[:5],
                conflict=DamageConflict(has_conflict=False, details=[]),
            )
        )

    damages.sort(key=lambda d: d.confidence, reverse=True)
    conflict_notes: list[str] = []
    requires_manual_review = False

    if not damages:
        return [], False, []

    if text_norm and ("sin dano" in text_norm or "sin dano visible" in text_norm) and any(
        d.confidence >= 0.55 for d in damages
    ):
        conflict_notes.append("texto minimiza el daño, pero otras evidencias reportan daño relevante")
        requires_manual_review = True

    if len(damages) >= 3 and all(d.confidence < 0.55 for d in damages[:3]):
        conflict_notes.append("múltiples daños con confianza media-baja; requiere validación humana")
        requires_manual_review = True

    if conflict_notes:
        for damage in damages:
            damage.conflict = DamageConflict(has_conflict=True, details=conflict_notes)

    return damages, requires_manual_review, conflict_notes


def pick_primary_category(damages: list[DamagePrediction]) -> tuple[IncidentCategory, float]:
    if not damages:
        return IncidentCategory.OTROS, 0.35

    score_by_category: dict[IncidentCategory, float] = defaultdict(float)
    for d in damages:
        if d.label == "CHOQUE":
            score_by_category[IncidentCategory.CHOQUE] += d.confidence
        elif d.label == "LLANTA_PINCHADA":
            score_by_category[IncidentCategory.LLANTA] += d.confidence
        elif d.label == "BATERIA":
            score_by_category[IncidentCategory.BATERIA] += d.confidence
        elif d.label in {"FALLA_MOTOR", "SOBRECALENTAMIENTO", "FUGA_LIQUIDO"}:
            score_by_category[IncidentCategory.MOTOR] += d.confidence
        else:
            score_by_category[IncidentCategory.OTROS] += d.confidence * 0.8

    best_cat = max(score_by_category, key=lambda c: score_by_category[c])
    confidence = max(0.4, min(0.95, score_by_category[best_cat] / max(1.0, len(damages))))
    return best_cat, round(confidence, 2)
