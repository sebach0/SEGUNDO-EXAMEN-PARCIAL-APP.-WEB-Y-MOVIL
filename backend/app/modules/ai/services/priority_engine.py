# Priorización por reglas (IA5).
from __future__ import annotations

from app.modules.ai.schemas import (
    IncidentCategory,
    PriorityLevel,
    IncidentPrioritizeIn,
    IncidentPrioritizeOut,
)
from app.modules.ai.services.evidence_fusion import fuse_incident_evidence
from app.modules.ai.text_normalize import normalize_for_match


def _norm(s: str | None) -> str:
    return normalize_for_match(s)


def prioritize(body: IncidentPrioritizeIn) -> IncidentPrioritizeOut:
    motivos: list[str] = []
    joined_audio = " ".join(
        a for a in [body.transcripcion_audio or "", *body.transcripciones_audio] if a and a.strip()
    )
    text = _norm(body.texto_cliente) + " " + _norm(joined_audio)
    ref = _norm(body.direccion_referencia)

    all_hallazgos = list(body.hallazgos_vision)
    for group in body.hallazgos_vision_por_imagen:
        all_hallazgos.extend(group)
    vision_joined = normalize_for_match(" ".join(all_hallazgos))

    damages, requires_manual_review, _ = fuse_incident_evidence(
        texto_cliente=body.texto_cliente,
        transcripcion_audio=body.transcripcion_audio,
        transcripciones_audio=body.transcripciones_audio,
        hallazgos_vision=body.hallazgos_vision,
        hallazgos_vision_por_imagen=body.hallazgos_vision_por_imagen,
    )
    damage_labels = [d.label for d in damages]
    top_damage_confidence = max((d.confidence for d in damages), default=0.0)

    # ── Señales visuales de choque o daño estructural ──────────────────────────
    vision_choque_signals = (
        "choque", "impacto", "abollad", "colision", "daño", "dano",
        "volcad", "volcó", "yolo", "lateral roto", "frente roto",
    )
    if any(normalize_for_match(x) in vision_joined for x in vision_choque_signals):
        motivos.append("hallazgo visual de posible choque o daño estructural")

    # ── Categoría de choque confirmada ────────────────────────────────────────
    if body.categoria == IncidentCategory.CHOQUE:
        motivos.append("incidente clasificado como choque")

    # ── Personas en escena (posible accidente con heridos) ────────────────────
    if "persona" in vision_joined and any(
        x in vision_joined for x in ("vehiculo", "coche", "camion", "auto")
    ):
        motivos.append("visión detecta personas y vehículo; posible accidente con heridos")

    # ── Señales de accidente / riesgo en texto o audio ────────────────────────
    riesgo_signals = (
        "accidente", "choque", "volcad", "volcó", "herid", "atrapad",
        "no puedo salir", "atrapado", "herido", "heridos", "lesionad",
        "me estrellé", "volcamos", "chocamos", "nos chocaron",
    )
    if any(normalize_for_match(x) in text for x in riesgo_signals):
        motivos.append("texto o audio menciona accidente o personas con riesgo")

    # ── Ubicación peligrosa (vía rápida, carretera) ───────────────────────────
    via_rapida = (
        "carretera", "autopista", "ruta", "peaje", "km ", "kilómetro",
        "kilometro", "doble via", "doble vía", "vía principal", "anillo",
        "avenida principal", "troncal",
    )
    if any(normalize_for_match(x) in text + " " + ref for x in via_rapida):
        motivos.append("ubicación o relato sugiere vía de alta velocidad")

    # ── Lenguaje de urgencia extrema ──────────────────────────────────────────
    urgencia_extrema = (
        "urgente", "urgentísimo", "grave", "gravísimo", "incendio",
        "explosión", "explosion", "fuego", "llamas", "humo denso",
        "no puedo respirar", "desmayad", "inconsciente", "sangre",
    )
    if any(normalize_for_match(x) in text for x in urgencia_extrema):
        motivos.append("lenguaje de alto riesgo o emergencia crítica")

    # ── Peligro en carretera nocturno o clima adverso ────────────────────────
    noche_lluvia = ("noche", "oscuro", "lluvia", "lloviendo", "neblina", "hielo", "resbaloso")
    if any(normalize_for_match(x) in text + " " + ref for x in noche_lluvia):
        motivos.append("condición adversa: noche, lluvia o visibilidad reducida")

    # ── Daños compuestos del motor de fusión ─────────────────────────────────
    if "FUGA_LIQUIDO" in damage_labels:
        motivos.append("fusión multimodal detecta fuga de líquido (riesgo de incendio)")
    if "CHOQUE" in damage_labels and (
        "VIDRIOS_ROTOS" in damage_labels
        or "LLANTA_PINCHADA" in damage_labels
        or "FUGA_LIQUIDO" in damage_labels
    ):
        motivos.append("incidente compuesto: choque con daños adicionales")

    if "SOBRECALENTAMIENTO" in damage_labels:
        motivos.append("motor sobrecalentado; riesgo de daño permanente o incendio")

    # ── Lógica de prioridad ────────────────────────────────────────────────────
    if len(motivos) >= 2:
        return IncidentPrioritizeOut(
            nivel_prioridad=PriorityLevel.ALTA,
            motivo=motivos,
            score=round(max(0.72, top_damage_confidence), 2),
            damages_considerados=damage_labels,
        )

    if motivos:
        return IncidentPrioritizeOut(
            nivel_prioridad=PriorityLevel.ALTA,
            motivo=motivos,
            score=round(max(0.62, top_damage_confidence), 2),
            damages_considerados=damage_labels,
        )

    # Descripción muy vaga
    if body.categoria == IncidentCategory.OTROS and len(text.strip()) < 15:
        return IncidentPrioritizeOut(
            nivel_prioridad=PriorityLevel.REVISION_MANUAL,
            motivo=["descripción muy breve y problema sin categorizar; verificar con el cliente"],
            score=0.35,
            damages_considerados=damage_labels,
        )

    if requires_manual_review:
        return IncidentPrioritizeOut(
            nivel_prioridad=PriorityLevel.REVISION_MANUAL,
            motivo=["evidencias multimodales con señales contradictorias; revisar manualmente"],
            score=round(max(0.40, top_damage_confidence), 2),
            damages_considerados=damage_labels,
        )

    if body.categoria in (IncidentCategory.BATERIA, IncidentCategory.LLANTA):
        return IncidentPrioritizeOut(
            nivel_prioridad=PriorityLevel.MEDIA,
            motivo=["tipo de fallo normalmente no crítico; requiere asistencia en carretera"],
            score=round(max(0.45, top_damage_confidence), 2),
            damages_considerados=damage_labels,
        )

    if body.categoria == IncidentCategory.MOTOR:
        return IncidentPrioritizeOut(
            nivel_prioridad=PriorityLevel.MEDIA,
            motivo=["falla mecánica detectada; validar síntomas antes de asignar técnico"],
            score=round(max(0.50, top_damage_confidence), 2),
            damages_considerados=damage_labels,
        )

    return IncidentPrioritizeOut(
        nivel_prioridad=PriorityLevel.BAJA,
        motivo=["sin señales de urgencia extrema según la información disponible"],
        score=round(max(0.20, top_damage_confidence), 2),
        damages_considerados=damage_labels,
    )
