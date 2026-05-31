# Scoring de talleres candidatos sin GenAI (IA6).
from __future__ import annotations

import math
from app.modules.ai.schemas import (
    AssignmentRankIn,
    AssignmentRankOut,
    IncidentCategory,
    PriorityLevel,
    TallerCandidatoScore,
)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlamb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlamb / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1 - a)))
    return r * c


def _specialty_match(categoria: IncidentCategory, especialidad_nombres: list[str]) -> float:
    joined = " ".join(n.lower() for n in especialidad_nombres if n)
    if categoria == IncidentCategory.MOTOR and any(
        x in joined for x in ("motor", "mecánica", "mecanica", "diagn")
    ):
        return 1.0
    if categoria == IncidentCategory.BATERIA and any(
        x in joined for x in ("electri", "bater", "diagn")
    ):
        return 1.0
    if categoria == IncidentCategory.LLANTA and any(
        x in joined for x in ("llanta", "neum", "goma", "rued")
    ):
        return 1.0
    if categoria == IncidentCategory.CHOQUE and any(
        x in joined for x in ("carrocer", "chapa", "pint", "colis")
    ):
        return 1.0
    return 0.35


def _priority_weight(p: PriorityLevel) -> float:
    return {
        PriorityLevel.ALTA: 1.0,
        PriorityLevel.MEDIA: 0.65,
        PriorityLevel.BAJA: 0.4,
        PriorityLevel.REVISION_MANUAL: 0.55,
    }.get(p, 0.5)


def rank_talleres(
    body: AssignmentRankIn,
    taller_rows: list[dict],
) -> AssignmentRankOut:
    """
    taller_rows: dicts con keys taller_id, nombre_comercial, ciudad, latitud, longitud,
    pendientes_bandeja (int), especialidad_nombres (list[str]).
    """
    ilat = float(body.incident_lat)
    ilng = float(body.incident_lng)
    pw = _priority_weight(body.nivel_prioridad)
    ciudad_inc = (body.ciudad_incidente or "").strip().lower()

    scored: list[TallerCandidatoScore] = []
    for row in taller_rows:
        tid = int(row["taller_id"])
        nombre = str(row["nombre_comercial"])
        ciudad = str(row.get("ciudad") or "")
        plat = row.get("latitud")
        plng = row.get("longitud")
        pend = int(row.get("pendientes_bandeja") or 0)
        specs: list[str] = list(row.get("especialidad_nombres") or [])

        if plat is not None and plng is not None:
            dist = _haversine_km(ilat, ilng, float(plat), float(plng))
            prox_score = max(0.0, 1.0 - min(dist / 80.0, 1.0))
        elif ciudad_inc and ciudad.lower() == ciudad_inc:
            prox_score = 0.55
            dist = None
        else:
            prox_score = 0.25
            dist = None

        carga_score = max(0.0, 1.0 - min(pend / 25.0, 1.0))
        spec = _specialty_match(body.categoria, specs)

        score = (
            0.38 * prox_score
            + 0.22 * carga_score
            + 0.22 * spec
            + 0.18 * pw
        )
        detalle = {
            "proximidad": round(prox_score, 3),
            "carga_bandeja": pend,
            "especialidad": round(spec, 3),
            "prioridad_peso": pw,
        }
        if dist is not None:
            detalle["distancia_km"] = round(dist, 2)

        scored.append(
            TallerCandidatoScore(
                taller_id=tid,
                nombre_comercial=nombre,
                score=round(score, 4),
                detalle=detalle,
            )
        )

    scored.sort(key=lambda x: x.score, reverse=True)
    best_id = scored[0].taller_id if scored else None
    return AssignmentRankOut(candidatos=scored, mejor_taller_id=best_id)
