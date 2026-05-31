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

    if any(
        normalize_for_match(x) in vision_joined
        for x in ("choque", "impacto", "abollad", "colision", "yolo", "daño", "dano")
    ):
        motivos.append("hallazgo visual de posible choque o daño estructural")

    if body.categoria == IncidentCategory.CHOQUE:
        motivos.append("categoría incidente: choque")

    if "persona" in vision_joined and ("vehiculo" in vision_joined or "coche" in vision_joined):
        motivos.append("visión: personas y vehículo detectados (modelo YOLO); valorar interacción / accidente")

    if any(normalize_for_match(x) in text for x in ("accidente", "choque", "volcad", "herid", "atrapad")):
        motivos.append("texto o audio menciona accidente o riesgo")

    if any(normalize_for_match(x) in text + ref for x in ("carretera", "autopista", "ruta", "peaje", "km ")):
        motivos.append("ubicación o relato sugiere vía rápida / carretera")

    if any(normalize_for_match(x) in text for x in ("urgente", "grave", "incendio", "explosion")):
        motivos.append("lenguaje de alto riesgo")

    if "FUGA_LIQUIDO" in damage_labels:
        motivos.append("fusión multimodal detecta posible fuga de líquido")
    if "CHOQUE" in damage_labels and ("VIDRIOS_ROTOS" in damage_labels or "LLANTA_PINCHADA" in damage_labels):
        motivos.append("incidente compuesto con múltiples daños relevantes")

    if len(motivos) >= 2:
        return IncidentPrioritizeOut(
            nivel_prioridad=PriorityLevel.ALTA,
            motivo=motivos,
            score=round(max(0.7, top_damage_confidence), 2),
            damages_considerados=damage_labels,
        )

    if motivos:
        return IncidentPrioritizeOut(
            nivel_prioridad=PriorityLevel.ALTA,
            motivo=motivos,
            score=round(max(0.6, top_damage_confidence), 2),
            damages_considerados=damage_labels,
        )

    # Ambigüedad: categoría OTROS y poco texto
    if body.categoria == IncidentCategory.OTROS and len(text.strip()) < 12:
        return IncidentPrioritizeOut(
            nivel_prioridad=PriorityLevel.REVISION_MANUAL,
            motivo=["descripción muy breve y categoría indeterminada"],
            score=0.35,
            damages_considerados=damage_labels,
        )

    if requires_manual_review:
        return IncidentPrioritizeOut(
            nivel_prioridad=PriorityLevel.REVISION_MANUAL,
            motivo=["evidencias multimodales conflictivas; revisar manualmente"],
            score=round(max(0.4, top_damage_confidence), 2),
            damages_considerados=damage_labels,
        )

    if body.categoria in (IncidentCategory.BATERIA, IncidentCategory.LLANTA):
        return IncidentPrioritizeOut(
            nivel_prioridad=PriorityLevel.MEDIA,
            motivo=["tipo de fallo habitualmente no inmediato"],
            score=round(max(0.45, top_damage_confidence), 2),
            damages_considerados=damage_labels,
        )

    if body.categoria == IncidentCategory.MOTOR:
        return IncidentPrioritizeOut(
            nivel_prioridad=PriorityLevel.MEDIA,
            motivo=["posible fallo mecánico; validar síntomas"],
            score=round(max(0.5, top_damage_confidence), 2),
            damages_considerados=damage_labels,
        )

    return IncidentPrioritizeOut(
        nivel_prioridad=PriorityLevel.BAJA,
        motivo=["sin señales de urgencia extrema"],
        score=round(max(0.2, top_damage_confidence), 2),
        damages_considerados=damage_labels,
    )
