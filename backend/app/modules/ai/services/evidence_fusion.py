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

# Vocabulario ampliado con jerga latinoamericana, formas conjugadas y frases comunes
_DAMAGE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "CHOQUE": (
        "choque", "colision", "accidente", "impacto", "abollad", "golpe",
        "rayon", "rayó", "rayón", "chocó", "topé", "tope", "estrellé",
        "estrello", "volcó", "volco", "volcado", "volcó", "se vino encima",
        "me chocaron", "chocaron", "chocamos", "airbag", "se activó el airbag",
        "daño en la carrocería", "abolladura", "lado abollado", "golpe fuerte",
        "impactó", "impacto fuerte", "choque por detras", "rearend",
        "carambola", "se salió de la vía", "salio de la via", "descarrilamiento",
    ),
    "VIDRIOS_ROTOS": (
        "vidrio", "parabrisas", "ventana rota", "cristal", "espejo roto",
        "espejo", "luna delantera", "luna rota", "vidrio quebrad",
        "vidrio roto", "se quebró el vidrio", "se quebro", "cristal roto",
        "lunas rotas", "ventanilla rota", "parabrisas quebrado",
        "parabrisas roto", "espejo lateral", "espejo retrovisor",
    ),
    "LLANTA_PINCHADA": (
        "llanta", "neumatico", "neumático", "pinchad", "goma", "rueda",
        "desinflad", "se reventó", "se revento", "ponchad", "ponchó",
        "poncho", "se ponchó", "reventada", "ponchadura", "goma baja",
        "goma pinchada", "sin aire", "le falta aire", "llanta baja",
        "sin llanta", "se fue la goma", "llantazo", "llanta reventada",
        "rueda pinchada", "rueda reventada", "goma reventada",
        "me quedé sin llanta", "se reventó la goma",
        "llanta desinflada", "neumático pinchado",
    ),
    "FUGA_LIQUIDO": (
        "fuga", "aceite", "liquido", "gote", "derrame",
        "pierde aceite", "aceite en el piso", "charco de aceite",
        "manchas de aceite", "fuga de aceite", "pierde liquido",
        "sale líquido", "sale liquido", "liquido en el piso",
        "gotea aceite", "manchas en el piso", "pierde agua",
        "fuga de agua", "sale agua", "refrigerante",
        "anticongelante", "líquido debajo", "chorro de liquido",
    ),
    "SOBRECALENTAMIENTO": (
        "sobrecalent", "temperatura alta", "humo",
        "se calentó", "recalentado", "vapor", "humeando",
        "agua hirviendo", "temperatura en rojo", "indicador de temp",
        "tablero marca temperatura", "vapores", "humo blanco",
        "humo del capó", "sale vapor", "indicador sube",
        "temperatura subió", "indicador en rojo", "se calentó el motor",
        "motor caliente", "recalentó", "overheating",
    ),
    "BATERIA": (
        "bateria", "batería", "no enciende", "no prende", "arranque",
        "descargad", "tablero", "no arranca", "sin corriente",
        "no da", "no responde", "batería muerta", "bateria muerta",
        "sin batería", "luces no encienden", "alternador",
        "cable muerto", "se fue la corriente", "cortocircuito",
        "no da corriente", "no tiene carga", "se descargó",
        "descargó la batería", "sin energía", "no hay luz",
        "cargador de batería", "batería descargada",
        "no arranca el motor", "motor no prende", "starter",
        "motor de arranque", "enciende pero se apaga",
    ),
    "FALLA_MOTOR": (
        "motor", "check engine", "vibracion", "vibración", "apago",
        "frenó de golpe", "correa", "transmision", "caja",
        "ruido raro", "hace ruido", "está vibrando",
        "traquetea", "se paró", "se apagó", "se murió el motor",
        "no tiene fuerza", "se ahoga", "pierde fuerza",
        "caja de velocidades", "embrague", "clutch", "diferencial",
        "fallo mecánico", "falla mecanica", "problema mecánico",
        "se quedó parado", "perdió potencia", "el motor hace ruido",
        "ruido en el motor", "golpeteo en el motor",
        "se para el motor", "motor falla", "luz del motor encendida",
        "se apagó el motor", "motor se detiene",
    ),
}

_CRITICAL_LABELS = {"CHOQUE", "FUGA_LIQUIDO"}
_HIGH_LABELS = {"SOBRECALENTAMIENTO", "FALLA_MOTOR"}

# Frases de múltiples palabras que requieren coincidencia exacta de subcadena
_PHRASE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "BATERIA": ("no arranca", "no enciende", "no prende", "batería muerta",
                "bateria muerta", "sin corriente", "no da carga"),
    "LLANTA_PINCHADA": ("se reventó la goma", "se ponchó la llanta",
                        "llanta desinflada", "goma baja"),
    "SOBRECALENTAMIENTO": ("agua hirviendo", "humo del capó", "temperatura en rojo",
                           "se calentó el motor"),
    "FALLA_MOTOR": ("check engine", "se apagó el motor", "perdió potencia",
                    "ruido en el motor", "se quedó parado"),
    "CHOQUE": ("se vino encima", "choque por detras", "salió de la vía",
               "volcó el auto", "se activó el airbag"),
}


def _severity_for(label: str, confidence: float) -> SeverityLevel:
    if label in _CRITICAL_LABELS and confidence >= 0.40:
        return SeverityLevel.CRITICA
    if label in _HIGH_LABELS and confidence >= 0.40:
        return SeverityLevel.ALTA
    if confidence >= 0.65:
        return SeverityLevel.ALTA
    if confidence >= 0.40:
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


def _match_label(label: str, norm_text: str) -> bool:
    """Devuelve True si cualquier keyword (simple o frase) del label aparece en norm_text."""
    for keyword in _DAMAGE_KEYWORDS.get(label, ()):
        if normalize_for_match(keyword) in norm_text:
            return True
    for phrase in _PHRASE_KEYWORDS.get(label, ()):
        if normalize_for_match(phrase) in norm_text:
            return True
    return False


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

    for label in _DAMAGE_KEYWORDS:
        # Texto
        matched_text_kw: str | None = None
        for keyword in list(_DAMAGE_KEYWORDS[label]) + list(_PHRASE_KEYWORDS.get(label, ())):
            nk = normalize_for_match(keyword)
            if nk and nk in text_norm:
                matched_text_kw = keyword
                break
        if matched_text_kw:
            raw_scores[label] += _TEXT_WEIGHT
            reasons[label].append(f"texto menciona '{matched_text_kw}'")
            support[label].text.append(DamageEvidenceItem(evidencia_id="txt-1", score=0.75))

        # Audio
        matched_audio_kw: str | None = None
        for keyword in list(_DAMAGE_KEYWORDS[label]) + list(_PHRASE_KEYWORDS.get(label, ())):
            nk = normalize_for_match(keyword)
            if nk and nk in audio_norm:
                matched_audio_kw = keyword
                break
        if matched_audio_kw:
            raw_scores[label] += _AUDIO_WEIGHT
            reasons[label].append(f"audio menciona '{matched_audio_kw}'")
            support[label].audio.append(DamageEvidenceItem(evidencia_id="aud-1", score=0.70))

        # Bonus: coincidencia tanto en texto como en audio → mayor confianza
        if matched_text_kw and matched_audio_kw:
            raw_scores[label] += 0.10
            reasons[label].append("confirmado en texto y audio")

    image_weight = _IMAGE_WEIGHT / max(1, len(vision_items))
    for evidence_id, finding in vision_items:
        norm_finding = normalize_for_match(finding)
        for label in _DAMAGE_KEYWORDS:
            matched_vision_kw: str | None = None
            for keyword in list(_DAMAGE_KEYWORDS[label]) + list(_PHRASE_KEYWORDS.get(label, ())):
                nk = normalize_for_match(keyword)
                if nk and nk in norm_finding:
                    matched_vision_kw = keyword
                    break
            if matched_vision_kw:
                raw_scores[label] += image_weight
                reasons[label].append(f"imagen reporta '{finding}'")
                support[label].image.append(
                    DamageEvidenceItem(evidencia_id=evidence_id, score=min(1.0, image_weight * 2.0))
                )

    damages: list[DamagePrediction] = []
    for label, score in raw_scores.items():
        confidence = max(0.0, min(1.0, score))
        if confidence < 0.25:
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

    text_minimiza = any(
        normalize_for_match(x) in text_norm
        for x in ("sin daño", "sin dano", "sin golpe", "no tiene daño", "no hay daño",
                   "parece bien", "esta bien", "no es nada grave")
    )
    if text_minimiza and any(d.confidence >= 0.50 for d in damages):
        conflict_notes.append("texto minimiza el daño pero otras evidencias reportan daño relevante")
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
        elif d.label in {"LLANTA_PINCHADA"}:
            score_by_category[IncidentCategory.LLANTA] += d.confidence
        elif d.label == "BATERIA":
            score_by_category[IncidentCategory.BATERIA] += d.confidence
        elif d.label in {"FALLA_MOTOR", "SOBRECALENTAMIENTO", "FUGA_LIQUIDO"}:
            score_by_category[IncidentCategory.MOTOR] += d.confidence
        elif d.label == "VIDRIOS_ROTOS":
            # Vidrios rotos → probablemente choque
            score_by_category[IncidentCategory.CHOQUE] += d.confidence * 0.85
        else:
            score_by_category[IncidentCategory.OTROS] += d.confidence * 0.8

    best_cat = max(score_by_category, key=lambda c: score_by_category[c])
    total = sum(score_by_category.values())
    confidence = max(0.45, min(0.95, score_by_category[best_cat] / max(1.0, total) * 1.1))
    return best_cat, round(confidence, 2)
