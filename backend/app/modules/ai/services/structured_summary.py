# Ficha y resumen determinísticos sin LLM (IA4).
from __future__ import annotations

from app.modules.ai.schemas import (
    FichaIncidente,
    IncidentCategory,
    StructuredSummaryIn,
    StructuredSummaryOut,
)
from app.modules.ai.services.evidence_fusion import fuse_incident_evidence, pick_primary_category

_CAT_LABELS: dict[IncidentCategory, str] = {
    IncidentCategory.BATERIA: "Problema de batería / arranque",
    IncidentCategory.LLANTA: "Llanta pinchada / desinflada",
    IncidentCategory.CHOQUE: "Choque o accidente",
    IncidentCategory.MOTOR: "Falla mecánica / motor",
    IncidentCategory.OTROS: "Problema no identificado",
}

_DAMAGE_LABELS: dict[str, str] = {
    "CHOQUE": "choque o golpe",
    "VIDRIOS_ROTOS": "vidrios rotos",
    "LLANTA_PINCHADA": "llanta pinchada",
    "FUGA_LIQUIDO": "fuga de líquido",
    "SOBRECALENTAMIENTO": "sobrecalentamiento",
    "BATERIA": "falla de batería",
    "FALLA_MOTOR": "falla mecánica",
}

_SEVERITY_LABELS: dict[str, str] = {
    "CRITICA": "crítica",
    "ALTA": "alta",
    "MEDIA": "media",
    "BAJA": "baja",
}

_RECOMENDACIONES: dict[IncidentCategory, str] = {
    IncidentCategory.BATERIA: (
        "Verificar nivel de carga de la batería y estado del alternador. "
        "Traer equipo de arranque auxiliar o batería de reemplazo."
    ),
    IncidentCategory.LLANTA: (
        "Llevar llanta de repuesto o equipo de reparación de pinchazos. "
        "Confirmar posición del vehículo antes de desplazarse."
    ),
    IncidentCategory.CHOQUE: (
        "Evaluar daños estructurales y verificar estado de ocupantes. "
        "Documentar el incidente fotográficamente al llegar."
    ),
    IncidentCategory.MOTOR: (
        "No forzar el arranque si hay humo o temperatura elevada. "
        "Llevar herramientas de diagnóstico OBD2 y revisar fluidos al llegar."
    ),
    IncidentCategory.OTROS: (
        "Contactar al cliente para obtener más detalles antes de desplazarse. "
        "Llevar kit de herramientas general."
    ),
}


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
    cat_label = _CAT_LABELS.get(cat, cat.value)

    texto_cliente = (body.texto_cliente or "").strip()
    audio_texto = joined_audio.strip()
    todos_textos = " ".join(x for x in (texto_cliente, audio_texto) if x).strip()

    ubi = body.ubicacion
    ubicacion_valida = bool(ubi and ubi.latitud is not None and ubi.longitud is not None)
    evid_audio = bool(audio_texto)
    evid_img = bool(all_hallazgos)

    # Incertidumbre
    incert = "BAJA"
    if cat == IncidentCategory.OTROS and not todos_textos:
        incert = "ALTA"
    elif cat == IncidentCategory.OTROS:
        incert = "MEDIA"
    elif not todos_textos and not evid_img:
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

    # 1 — Relato del cliente
    if texto_cliente:
        extracto = texto_cliente[:300] + ("…" if len(texto_cliente) > 300 else "")
        partes.append(f"El cliente reporta: «{extracto}»")
    elif audio_texto:
        extracto = audio_texto[:300] + ("…" if len(audio_texto) > 300 else "")
        partes.append(f"Relato por audio: «{extracto}»")
    else:
        partes.append("El cliente no proporcionó descripción textual detallada.")

    # 2 — Diagnóstico automático
    partes.append(f"Problema identificado: {cat_label}.")

    # 3 — Daños detectados (con labels legibles)
    if damages:
        damage_desc = ", ".join(
            f"{_DAMAGE_LABELS.get(d.label, d.label)} (severidad {_SEVERITY_LABELS.get(d.severity.value, d.severity.value)})"
            for d in damages[:4]
        )
        partes.append(f"Daños detectados por análisis multimodal: {damage_desc}.")

    # 4 — Evidencia visual
    if all_hallazgos:
        hallazgos_desc = "; ".join(all_hallazgos[:4])
        partes.append(f"Análisis visual detectó: {hallazgos_desc}.")

    # 5 — Ubicación
    if ubi and ubi.direccion_referencia:
        partes.append(f"Ubicación del cliente: {ubi.direccion_referencia[:200]}.")
    elif ubicacion_valida:
        partes.append("El cliente compartió su ubicación GPS.")
    else:
        partes.append("Ubicación GPS no disponible; confirmar dirección con el cliente.")

    # 6 — Recomendación para el taller
    rec = _RECOMENDACIONES.get(cat)
    if rec:
        partes.append(f"Recomendación: {rec}")

    # 7 — Alertas de incertidumbre o conflicto
    if incert == "ALTA":
        partes.append("⚠ Alta incertidumbre: se recomienda contactar al cliente antes de desplazarse.")
    elif incert == "MEDIA":
        partes.append("⚠ Incertidumbre media: validar detalles con el cliente si es posible.")

    if requires_manual_review:
        partes.append("⚠ Conflicto entre evidencias: revisar manualmente antes de asignar técnico.")
    if conflict_notes:
        partes.append("Nota: " + "; ".join(conflict_notes[:2]) + ".")

    resumen = " ".join(partes)
    return StructuredSummaryOut(
        resumen=resumen,
        ficha=ficha,
        danos_detectados=[d.label for d in damages],
    )
