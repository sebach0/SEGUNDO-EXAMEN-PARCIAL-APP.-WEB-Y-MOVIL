from app.modules.ai.services.incident_classifier import classify_incident
from app.modules.ai.schemas import IncidentCategory, IncidentClassifyIn
from app.modules.ai.text_normalize import contains_normalized, normalize_for_match


def test_normalize_casefold_motor():
    assert normalize_for_match("Motor") == normalize_for_match("motor")
    assert normalize_for_match("MOTOR") == normalize_for_match("MoToR")
    assert "motor" in normalize_for_match("falla de Motor")


def test_normalize_accents():
    assert normalize_for_match("Colisión") == normalize_for_match("colision")
    assert contains_normalized("Hubo una COLISIÓN", "colision")


def test_classify_ignores_case():
    out = classify_incident(
        IncidentClassifyIn(
            texto_cliente="Fallo de MOTOR y humo",
            transcripcion_audio=None,
            hallazgos_vision=[],
        )
    )
    assert out.categoria == IncidentCategory.MOTOR
