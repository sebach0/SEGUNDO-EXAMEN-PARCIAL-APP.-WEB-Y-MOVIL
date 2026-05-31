"""Línea base: esquema ya aplicado por init.sql (Docker) o entorno existente.

Las migraciones siguientes (0002_…) describen solo cambios incrementales.
En una BD creada con init.sql, ejecutar una vez: alembic stamp 0001_baseline

"""
from typing import Sequence, Union

revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Sin DDL: el esquema inicial lo define backend/migrations/init.sql."""
    pass


def downgrade() -> None:
    pass
