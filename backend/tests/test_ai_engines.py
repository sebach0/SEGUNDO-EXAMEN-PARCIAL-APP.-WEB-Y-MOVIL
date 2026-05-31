# Tests unitarios — motores de reglas IA (sin inferencia externa).
from decimal import Decimal

from app.modules.ai.schemas import (
    AssignmentRankIn,
    IncidentCategory,
    IncidentClassifyIn,
    IncidentPrioritizeIn,
    PriorityLevel,
    StructuredSummaryIn,
    UbicacionResumenIn,
)
from app.modules.ai.services.assignment_scorer import rank_talleres
from app.modules.ai.services.audio_extract import extract_from_transcription
from app.modules.ai.services.incident_classifier import classify_incident
from app.modules.ai.services.priority_engine import prioritize
from app.modules.ai.services.structured_summary import build_structured_summary


def test_audio_extract_battery():
    r = extract_from_transcription("mi auto no enciende y creo que es batería")
    assert "batería" in r.tipo_problema_mencionado or r.tipo_problema_mencionado == "batería"
    assert r.urgencia_percibida in ("media", "alta")


def test_classify_battery():
    out = classify_incident(
        IncidentClassifyIn(
            texto_cliente="no enciende, creo que es la batería",
            transcripcion_audio=None,
            hallazgos_vision=[],
        )
    )
    assert out.categoria == IncidentCategory.BATERIA
    assert "texto" in out.fuentes


def test_classify_vision_choque_boost():
    out = classify_incident(
        IncidentClassifyIn(
            texto_cliente="algo pasó con el auto",
            transcripcion_audio=None,
            hallazgos_vision=["posible choque lateral"],
        )
    )
    assert out.categoria == IncidentCategory.CHOQUE
    assert "imagen" in out.fuentes


def test_classify_compound_incident_multi_damage():
    out = classify_incident(
        IncidentClassifyIn(
            texto_cliente="sufri un choque, se rompieron los vidrios y la llanta quedó pinchada",
            transcripcion_audio="estoy en la autopista, choque fuerte y no puedo mover el auto",
            transcripciones_audio=["también hay vidrio en el piso"],
            hallazgos_vision_por_imagen=[
                ["posible choque frontal", "vidrio roto en parabrisas"],
                ["llanta pinchada delantera"],
            ],
        )
    )
    labels = {d.label for d in out.damages}
    assert out.categoria == IncidentCategory.CHOQUE
    assert "CHOQUE" in labels
    assert "VIDRIOS_ROTOS" in labels
    assert "LLANTA_PINCHADA" in labels


def test_prioritize_road_and_crash():
    out = prioritize(
        IncidentPrioritizeIn(
            texto_cliente="choque en carretera",
            transcripcion_audio=None,
            hallazgos_vision=["daño visible lateral"],
            categoria=IncidentCategory.CHOQUE,
            direccion_referencia="km 12 carretera a Oruro",
        )
    )
    assert out.nivel_prioridad == PriorityLevel.ALTA
    assert out.score is not None


def test_prioritize_compound_damage_considered():
    out = prioritize(
        IncidentPrioritizeIn(
            texto_cliente="choque con vidrios rotos y llanta pinchada",
            transcripcion_audio="urgente, no puedo mover el auto",
            hallazgos_vision_por_imagen=[
                ["choque lateral"],
                ["vidrio roto", "llanta pinchada"],
            ],
            categoria=IncidentCategory.CHOQUE,
            direccion_referencia="autopista sur km 12",
        )
    )
    assert out.nivel_prioridad == PriorityLevel.ALTA
    assert "CHOQUE" in out.damages_considerados
    assert "VIDRIOS_ROTOS" in out.damages_considerados
    assert out.score and out.score >= 0.6


def test_structured_summary_ficha():
    out = build_structured_summary(
        StructuredSummaryIn(
            texto_cliente="no enciende",
            transcripcion_audio=None,
            hallazgos_vision=[],
            categoria=IncidentCategory.BATERIA,
            ubicacion=UbicacionResumenIn(
                latitud=Decimal("-16.5"),
                longitud=Decimal("-68.1"),
                direccion_referencia="Estacionamiento",
            ),
        )
    )
    assert "BATERIA" in out.resumen or "batería" in out.resumen.lower()
    assert out.ficha.ubicacion_valida is True
    assert out.ficha.tipo_problema == IncidentCategory.BATERIA


def test_structured_summary_includes_compound_damages():
    out = build_structured_summary(
        StructuredSummaryIn(
            texto_cliente="choque con vidrio roto",
            transcripciones_audio=["la llanta está pinchada también"],
            hallazgos_vision_por_imagen=[["choque frontal"], ["vidrio roto", "llanta pinchada"]],
            categoria=IncidentCategory.CHOQUE,
            ubicacion=UbicacionResumenIn(latitud=Decimal("-16.5"), longitud=Decimal("-68.1")),
        )
    )
    assert "Daños detectados" in out.resumen
    assert "CHOQUE" in out.danos_detectados


def test_assignment_rank_order():
    body = AssignmentRankIn(
        incident_lat=Decimal("-16.49"),
        incident_lng=Decimal("-68.12"),
        categoria=IncidentCategory.BATERIA,
        nivel_prioridad=PriorityLevel.MEDIA,
        ciudad_incidente="La Paz",
    )
    rows = [
        {
            "taller_id": 1,
            "nombre_comercial": "A",
            "ciudad": "La Paz",
            "latitud": -16.489,
            "longitud": -68.119,
            "pendientes_bandeja": 2,
            "especialidad_nombres": ["Electricidad"],
        },
        {
            "taller_id": 2,
            "nombre_comercial": "B",
            "ciudad": "La Paz",
            "latitud": -16.6,
            "longitud": -68.2,
            "pendientes_bandeja": 20,
            "especialidad_nombres": [],
        },
    ]
    out = rank_talleres(body, rows)
    assert out.mejor_taller_id == 1
    assert out.candidatos[0].score >= out.candidatos[1].score
