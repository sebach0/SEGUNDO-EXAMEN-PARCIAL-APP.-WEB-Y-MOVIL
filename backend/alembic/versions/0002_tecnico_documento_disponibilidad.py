"""Añade documento_identidad y disponibilidad a tecnicos (portal taller ciclo 1)."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_tecnico_documento_disponibilidad"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tecnicos",
        sa.Column("documento_identidad", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "tecnicos",
        sa.Column("disponibilidad", sa.String(length=120), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tecnicos", "disponibilidad")
    op.drop_column("tecnicos", "documento_identidad")
