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
            (
                "batería", "bateria", "no enciende", "no prende", "arranque",
                "tablero", "descargad", "no arranca", "sin corriente",
                "batería muerta", "bateria muerta", "no da carga",
                "luces no encienden", "alternador", "se descargó",
                "sin batería", "motor no arranca", "starter",
                "no tiene carga", "cortocircuito", "cable muerto",
                "enciende pero se apaga",
            ),
        ),
        (
            IncidentCategory.LLANTA,
            (
                "llanta", "neumático", "neumatico", "pinchad", "goma",
                "rueda", "desinflad", "se reventó", "ponchad", "ponchó",
                "reventada", "ponchadura", "goma baja", "llanta baja",
                "sin llanta", "llantazo", "llanta reventada",
                "se revento la goma", "neumático desinflado",
                "goma reventada", "rueda reventada",
            ),
        ),
        (
            IncidentCategory.CHOQUE,
            (
                "choque", "accidente", "golpe", "abollad", "impacto",
                "colision", "colisión", "rayón", "rayon", "estrellé",
                "volteo", "volcó", "volco", "topé", "airbag",
                "chocó", "me chocaron", "daño en la carrocería",
                "choque por detras", "salió de la vía",
                "se activó el airbag", "carambola", "volcado",
            ),
        ),
        (
            IncidentCategory.MOTOR,
            (
                "motor", "humo", "calient", "aceite", "temperatura",
                "check engine", "sobrecalent", "fuga", "vibra",
                "traquetea", "ruido raro", "se apagó", "se paró",
                "no tiene fuerza", "se ahoga", "perdió potencia",
                "correa", "transmision", "caja de cambios", "embrague",
                "clutch", "diferencial", "falla mecanica", "fallo mecánico",
                "luz del motor", "recalentado", "agua hirviendo",
                "refrigerante", "anticongelante", "vapor del motor",
                "pierde aceite", "gotea aceite",
            ),
        ),
    ]

    for cat, keys in rules:
        for k in keys:
            nk = normalize_for_match(k)
            if nk and nk in text:
                scores[cat] += 1.0

    if sum(scores.values()) == 0:
        scores[IncidentCategory.OTROS] = 0.4
    return scores


def _vision_boost(hallazgos: list[str]) -> dict[IncidentCategory, float]:
    boost: dict[IncidentCategory, float] = {c: 0.0 for c in IncidentCategory}
    joined = normalize_for_match(" ".join(hallazgos))

    choque_signals = ("choque", "impacto", "abollad", "lateral", "frente", "yolo",
                      "colision", "volcad", "daño", "dano", "abolladura", "golpe")
    if any(normalize_for_match(x) in joined for x in choque_signals):
        boost[IncidentCategory.CHOQUE] += 1.2

    llanta_signals = ("llanta", "neumatico", "rueda", "pinchad", "goma", "reventad")
    if any(normalize_for_match(x) in joined for x in llanta_signals):
        boost[IncidentCategory.LLANTA] += 1.2

    bateria_signals = ("bateria", "tablero", "starter", "arranque")
    if any(normalize_for_match(x) in joined for x in bateria_signals):
        boost[IncidentCategory.BATERIA] += 1.0

    motor_signals = ("motor", "capo", "cofre", "humo", "aceite", "temperatura", "vapor")
    if any(normalize_for_match(x) in joined for x in motor_signals):
        boost[IncidentCategory.MOTOR] += 1.0

    # Personas + vehículo en escena → probable choque
    if "persona" in joined and any(x in joined for x in ("vehiculo", "coche", "camion", "auto")):
        boost[IncidentCategory.CHOQUE] += 0.6

    return boost


def classify_incident(body: IncidentClassifyIn) -> IncidentClassifyOut:
    damages, requires_manual_review, conflict_notes = fuse_incident_evidence(
        texto_cliente=body.texto_cliente,
        transcripcion_audio=body.transcripcion_audio,
        transcripciones_audio=body.transcripciones_audio,
        hallazgos_vision=body.hallazgos_vision,
        hallazgos_vision_por_imagen=body.hallazgos_vision_por_imagen,
    )

    def _build_fuentes() -> list[str]:
        f: list[str] = []
        if body.texto_cliente and body.texto_cliente.strip():
            f.append(FuenteInferencia.TEXTO.value)
        if (body.transcripcion_audio and body.transcripcion_audio.strip()) or body.transcripciones_audio:
            f.append(FuenteInferencia.AUDIO.value)
        if body.hallazgos_vision or body.hallazgos_vision_por_imagen:
            f.append(FuenteInferencia.IMAGEN.value)
        return f or [FuenteInferencia.TEXTO.value]

    if damages:
        cat, conf = pick_primary_category(damages)
        return IncidentClassifyOut(
            categoria=cat,
            confianza=conf,
            fuentes=_build_fuentes(),
            damages=damages,
            requires_manual_review=requires_manual_review,
            conflict_notes=conflict_notes,
        )

    # Fallback: reglas sobre texto + audio fusionados
    text = _norm(body.texto_cliente) + " " + _norm(body.transcripcion_audio)
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
            fuentes=_build_fuentes(),
        )

    sorted_vals = sorted(scores.values(), reverse=True)
    top = sorted_vals[0] if sorted_vals else 0
    runner = sorted_vals[1] if len(sorted_vals) > 1 else 0
    margin = top - runner

    # Confianza más generosa con vocabulario ampliado
    conf = 0.48 + 0.10 * min(top, 5) + 0.07 * min(margin, 4)
    conf = max(0.42, min(0.92, conf))

    if margin < 0.5 and top > 0:
        conf *= 0.88

    cat = best if best_val > 0 else IncidentCategory.OTROS
    return IncidentClassifyOut(
        categoria=cat,
        confianza=round(conf, 2),
        fuentes=_build_fuentes(),
    )
