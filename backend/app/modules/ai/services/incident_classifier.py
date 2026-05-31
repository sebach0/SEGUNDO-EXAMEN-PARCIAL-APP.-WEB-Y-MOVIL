# Clasificación híbrida texto + transcripción + hallazgos visión (IA2).
from __future__ import annotations

from app.modules.ai.schemas import FuenteInferencia, IncidentCategory, IncidentClassifyIn, IncidentClassifyOut
from app.modules.ai.services.evidence_fusion import fuse_incident_evidence, pick_primary_category
from app.modules.ai.text_normalize import normalize_for_match


def _norm(s: str | None) -> str:
    return normalize_for_match(s)


def _score_category(text: str) -> dict[IncidentCategory, float]:
    scores: dict[IncidentCategory, float] = {c: 0.0 for c in IncidentCategory}
    if not text:
        return scores

    rules: list[tuple[IncidentCategory, tuple[str, ...]]] = [
        (
            IncidentCategory.BATERIA,
            ("batería", "bateria", "no enciende", "no prende", "arranque", "tablero", "descargad"),
        ),
        (
            IncidentCategory.LLANTA,
            ("llanta", "neumático", "neumatico", "pinchad", "goma", "desinflad", "rueda"),
        ),
        (
            IncidentCategory.CHOQUE,
            ("choque", "accidente", "golpe", "abollad", "impacto", "colision", "colisión", "rayón"),
        ),
        (
            IncidentCategory.MOTOR,
            ("motor", "humo", "calient", "aceite", "temperatura", "check engine"),
        ),
    ]
    for cat, keys in rules:
        for k in keys:
            if normalize_for_match(k) in text:
                scores[cat] += 1.0

    if sum(scores.values()) == 0:
        scores[IncidentCategory.OTROS] = 0.4
    return scores


def _vision_boost(hallazgos: list[str]) -> dict[IncidentCategory, float]:
    boost: dict[IncidentCategory, float] = {c: 0.0 for c in IncidentCategory}
    joined = normalize_for_match(" ".join(hallazgos))
    if any(normalize_for_match(x) in joined for x in ("choque", "impacto", "abollad", "lateral", "frente", "yolo")):
        boost[IncidentCategory.CHOQUE] += 1.2
    if any(normalize_for_match(x) in joined for x in ("llanta", "neumatico", "rueda", "pinchad")):
        boost[IncidentCategory.LLANTA] += 1.2
    if any(normalize_for_match(x) in joined for x in ("bateria", "tablero")):
        boost[IncidentCategory.BATERIA] += 1.0
    if "motor" in joined or "capo" in joined or "cofre" in joined:
        boost[IncidentCategory.MOTOR] += 0.8
    if "persona" in joined and ("vehiculo" in joined or "coche" in joined or "camion" in joined):
        boost[IncidentCategory.CHOQUE] += 0.5
    return boost


def classify_incident(body: IncidentClassifyIn) -> IncidentClassifyOut:
    damages, requires_manual_review, conflict_notes = fuse_incident_evidence(
        texto_cliente=body.texto_cliente,
        transcripcion_audio=body.transcripcion_audio,
        transcripciones_audio=body.transcripciones_audio,
        hallazgos_vision=body.hallazgos_vision,
        hallazgos_vision_por_imagen=body.hallazgos_vision_por_imagen,
    )

    if damages:
        cat, conf = pick_primary_category(damages)
        fuentes: list[str] = []
        if body.texto_cliente and body.texto_cliente.strip():
            fuentes.append(FuenteInferencia.TEXTO.value)
        if (body.transcripcion_audio and body.transcripcion_audio.strip()) or body.transcripciones_audio:
            fuentes.append(FuenteInferencia.AUDIO.value)
        if body.hallazgos_vision or body.hallazgos_vision_por_imagen:
            fuentes.append(FuenteInferencia.IMAGEN.value)
        return IncidentClassifyOut(
            categoria=cat,
            confianza=conf,
            fuentes=fuentes or [FuenteInferencia.TEXTO.value],
            damages=damages,
            requires_manual_review=requires_manual_review,
            conflict_notes=conflict_notes,
        )

    text = _norm(body.texto_cliente) + " " + _norm(body.transcripcion_audio)
    fuentes: list[str] = []
    if body.texto_cliente and body.texto_cliente.strip():
        fuentes.append(FuenteInferencia.TEXTO.value)
    if body.transcripcion_audio and body.transcripcion_audio.strip():
        fuentes.append(FuenteInferencia.AUDIO.value)
    if body.hallazgos_vision:
        fuentes.append(FuenteInferencia.IMAGEN.value)

    scores = _score_category(text)
    vb = _vision_boost(body.hallazgos_vision)
    for c in IncidentCategory:
        scores[c] += vb.get(c, 0.0)

    best = max(scores, key=lambda k: scores[k])
    best_val = scores[best]
    if best_val <= 0 and not body.hallazgos_vision:
        return IncidentClassifyOut(
            categoria=IncidentCategory.OTROS,
            confianza=0.35,
            fuentes=fuentes or [FuenteInferencia.TEXTO.value],
        )

    second = sorted(scores.values(), reverse=True)
    top = second[0] if second else 0
    runner = second[1] if len(second) > 1 else 0
    margin = top - runner
    conf = 0.45 + 0.12 * min(top, 4) + 0.08 * min(margin, 3)
    conf = max(0.4, min(0.95, conf))

    if margin < 0.25 and top > 0:
        conf *= 0.85

    cat = best if best_val > 0 else IncidentCategory.OTROS
    return IncidentClassifyOut(categoria=cat, confianza=round(conf, 2), fuentes=fuentes)
