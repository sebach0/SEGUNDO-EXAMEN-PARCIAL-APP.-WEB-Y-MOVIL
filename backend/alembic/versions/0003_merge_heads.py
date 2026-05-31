"""Une ramas Alembic: emergencias ciclo2 fase1 + columnas técnico."""

from __future__ import annotations

from typing import Sequence, Union

revision: str = "0003_merge_heads"
down_revision: Union[str, tuple[str, ...], None] = (
    "0002_ciclo2_fase1_emergencias",
    "0002_tecnico_documento_disponibilidad",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Sin cambios de esquema: solo convergencia de heads."""
    pass


def downgrade() -> None:
    pass
