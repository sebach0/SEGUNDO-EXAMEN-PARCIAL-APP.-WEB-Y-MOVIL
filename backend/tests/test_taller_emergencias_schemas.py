"""Validaciones Pydantic del módulo taller_emergencias (sin BD)."""
from __future__ import annotations

import unittest

from pydantic import ValidationError

from app.modules.atencion.taller_emergencias.schemas import (
    AsignarTecnicoIn,
    RechazarBandejaIn,
    TallerDisponibilidadUpdateIn,
)


class TestTallerEmergenciasSchemas(unittest.TestCase):
    def test_rechazar_motivo_min_length(self) -> None:
        with self.assertRaises(ValidationError):
            RechazarBandejaIn(motivo_rechazo="ab")

    def test_rechazar_motivo_ok(self) -> None:
        m = RechazarBandejaIn(motivo_rechazo="No disponemos de grúa")
        self.assertEqual(m.motivo_rechazo, "No disponemos de grúa")

    def test_disponibilidad_capacidad_rango(self) -> None:
        with self.assertRaises(ValidationError):
            TallerDisponibilidadUpdateIn(capacidad_maxima_diaria=0)

    def test_asignar_tecnico_id_positivo(self) -> None:
        with self.assertRaises(ValidationError):
            AsignarTecnicoIn(tecnico_id=0)


if __name__ == "__main__":
    unittest.main()
