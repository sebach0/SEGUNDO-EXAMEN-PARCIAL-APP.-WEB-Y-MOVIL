"""
Puerto de integración con pasarela de pago (CU20).

- Hoy: `PasarelaSimulada` confirma cobros sin red externa.
- Futuro: implementar `PasarelaStripe`, `PasarelaQrBancario`, etc. con el mismo contrato
  y configurar el proveedor vía `app.core.config.Settings`.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol
import uuid


@dataclass(frozen=True)
class ResultadoCobro:
    exitoso: bool
    referencia_externa: str
    metadata: dict[str, Any]
    mensaje_error: str | None = None


class PasarelaPagoPort(Protocol):
    """Contrato para integrar una pasarela real (redirect, 3DS, webhooks, etc.)."""

    async def ejecutar_cobro(
        self,
        *,
        pago_id: int,
        solicitud_id: int,
        monto: Decimal,
        moneda: str,
        metodo: str,
    ) -> ResultadoCobro: ...


class PasarelaSimulada:
    """Simula aprobación inmediata; genera referencia única para trazabilidad y conciliación."""

    proveedor: str = "SIMULADO"

    async def ejecutar_cobro(
        self,
        *,
        pago_id: int,
        solicitud_id: int,
        monto: Decimal,
        moneda: str,
        metodo: str,
    ) -> ResultadoCobro:
        ref = f"SIM-{uuid.uuid4().hex[:24].upper()}"
        meta: dict[str, Any] = {
            "pago_id": pago_id,
            "solicitud_id": solicitud_id,
            "monto": str(monto),
            "moneda": moneda,
            "metodo": metodo,
            "simulado": True,
        }
        return ResultadoCobro(exitoso=True, referencia_externa=ref, metadata=meta, mensaje_error=None)
