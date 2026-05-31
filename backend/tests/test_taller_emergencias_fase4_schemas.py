"""Schemas fase 4 taller emergencias (sin BD)."""
from __future__ import annotations

import unittest
from decimal import Decimal

from app.modules.atencion.taller_emergencias.schemas import ResumenComisionesRead


class TestTallerEmergenciasFase4Schemas(unittest.TestCase):
    def test_resumen_comisiones_read(self) -> None:
        m = ResumenComisionesRead(
            taller_id=1,
            total_registros=2,
            total_servicios=Decimal("100.00"),
            total_comision=Decimal("10.00"),
            total_neto=Decimal("90.00"),
        )
        self.assertEqual(m.taller_id, 1)


if __name__ == "__main__":
    unittest.main()
