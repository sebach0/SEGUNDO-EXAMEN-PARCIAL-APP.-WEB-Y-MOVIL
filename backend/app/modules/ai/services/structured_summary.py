# Ficha y resumen determinísticos sin LLM (IA4).
from __future__ import annotations

from app.modules.ai.schemas import (
    FichaIncidente,
    IncidentCategory,
    StructuredSummaryIn,
    StructuredSummaryOut,
)
from app.modules.ai.services.evidence_fusion import fuse_incident_evidence, pick_primary_category


def build_structured_summary(body: StructuredSummaryIn) -> StructuredSummaryOut:
    joined_audio = " ".join(
        a for a in [body.transcripcion_audio or "", *body.transcripciones_audio] if a and a.strip()
    )
    all_hallazgos = list(body.hallazgos_vision)
    for group in body.hallazgos_vision_por_imagen:
        all_hallazgos.extend(group)
    damages, requires_manual_review, conflict_notes = fuse_incident_evidence(
        texto_cliente=body.texto_cliente,
        transcripcion_audio=body.transcripcion_audio,
        transcripciones_audio=body.transcripciones_audio,
        hallazgos_vision=body.hallazgos_vision,
        hallazgos_vision_por_imagen=body.hallazgos_vision_por_imagen,
    )
    inferred_cat, _ = pick_primary_category(damages)
    cat = body.categoria or inferred_cat or IncidentCategory.OTROS
    textos = " ".join(
        x
        for x in (body.texto_cliente or "", joined_audio)
        if x
    ).strip()

    ubi = body.ubicacion
    ubicacion_valida = bool(
        ubi and ubi.latitud is not None and ubi.longitud is not None
    )
    evid_audio = bool(joined_audio.strip())
    evid_img = bool(all_hallazgos)

    incert = "BAJA"
    if cat == IncidentCategory.OTROS:
        incert = "ALTA"
    elif not textos and not evid_audio:
        incert = "MEDIA"
    elif not ubicacion_valida:
        incert = "MEDIA"

    ficha = FichaIncidente(
        tipo_problema=cat,
        ubicacion_valida=ubicacion_valida,
        evidencia_audio=evid_audio,
        evidencia_imagen=evid_img,
        incertidumbre=incert,
    )

    partes: list[str] = []
    if textos:
        partes.append(f"Cliente indica: {textos[:280]}{'…' if len(textos) > 280 else ''}")
    elif evid_audio:
        partes.append("Hay relato en audio transcrito disponible para el taller.")
    else:
        partes.append("Descripción textual limitada.")

    partes.append(f"Clasificación automática del problema: {cat.value}.")

    if all_hallazgos:
        partes.append("Evidencia fotográfica: " + "; ".join(all_hallazgos[:5]) + ".")

    if damages:
        partes.append(
            "Daños detectados: "
            + ", ".join(f"{d.label} ({d.severity.value})" for d in damages[:4])
            + "."
        )

    if ubi and ubi.direccion_referencia:
        partes.append(f"Referencia de ubicación: {ubi.direccion_referencia[:200]}.")
    elif ubicacion_valida:
        partes.append("Ubicación GPS registrada.")
    else:
        partes.append("Ubicación GPS no confirmada en los datos recibidos.")

    if incert == "ALTA":
        partes.append("Prioridad sugerida: revisión humana por alta incertidumbre.")
    elif incert == "MEDIA":
        partes.append("Prioridad sugerida: validar detalles con el cliente si es posible.")
    if requires_manual_review:
        partes.append("Conflicto multimodal detectado: validar manualmente antes de asignar.")
    if conflict_notes:
        partes.append("Conflictos: " + "; ".join(conflict_notes[:2]) + ".")

    resumen = " ".join(partes)
    return StructuredSummaryOut(
        resumen=resumen,
        ficha=ficha,
        danos_detectados=[d.label for d in damages],
    )
