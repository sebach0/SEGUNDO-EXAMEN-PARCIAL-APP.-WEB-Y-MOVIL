# app/core/database.py
# =========================================================
# Configuración de SQLAlchemy asíncrono con asyncpg
# Provee: engine, sessionmaker y dependencia get_db
# =========================================================
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


# ── Motor asíncrono ────────────────────────────────────────
# pool_pre_ping=True: verifica conexiones antes de usarlas (evita errores por timeout)
# echo=False en producción, True en desarrollo para ver SQL en consola
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# ── Session factory ────────────────────────────────────────
# expire_on_commit=False: evita errores al acceder atributos después del commit
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Base declarativa para todos los modelos ────────────────
class Base(DeclarativeBase):
    pass


# ── Dependencia FastAPI ────────────────────────────────────
# Uso: async def endpoint(db: AsyncSession = Depends(get_db))
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
