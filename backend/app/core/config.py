# app/core/config.py
# =========================================================
# Configuración central (pydantic-settings).
# Prioridad: variables de entorno del proceso > `.env` en la raíz del repo (única fuente).
# =========================================================
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.seeds import identidades_demo_sc as _seed_sc

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_REPO_ROOT = _BACKEND_DIR.parent


def _env_files() -> tuple[str, ...]:
    """Solo el `.env` en la raíz del repositorio (Compose y dev local usan el mismo archivo)."""
    p = _REPO_ROOT / ".env"
    return (str(p),) if p.is_file() else ()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files() or None,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator(
        "API_PUBLIC_URL",
        "APP_PUBLIC_URL",
        "EVIDENCIAS_PUBLIC_BASE_URL",
        "AI_INFERENCE_BASE_URL",
        "STRIPE_SECRET_KEY",
        "STRIPE_PUBLISHABLE_KEY",
        "SMTP_USER",
        "SMTP_PASSWORD",
        mode="before",
    )
    @classmethod
    def _empty_str_to_none(cls, v: object) -> object:
        if isinstance(v, str) and not v.strip():
            return None
        return v

    # ── API ──────────────────────────────────────────────
    API_PREFIX: str = "/api"
    PROJECT_NAME: str = "Plataforma Inteligente de Emergencias Vehiculares"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API REST para gestión de emergencias vehiculares — Ciclo 1"

    # ── Base de datos ─────────────────────────────────────
    DATABASE_URL: str  # postgresql+asyncpg://user:pass@host:port/db

    # ── Seguridad / JWT ───────────────────────────────────
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── CORS (lista separada por coma; solo .env / entorno, sin default en código) ───────
    CORS_ORIGINS: str

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # ── Entorno ────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # ── Seed admin (desarrollo; nunca activar en prod sin control explícito) ──
    # Valores por defecto: `app/seeds/identidades_demo_sc.py` (Santa Cruz, BO; dominio *.sc-demo.test).
    SEED_ADMIN_ON_START: bool = False
    SEED_ADMIN_EMAIL: str | None = _seed_sc.ADMIN_EMAIL
    SEED_ADMIN_PASSWORD: str | None = _seed_sc.ADMIN_PASSWORD
    SEED_ADMIN_TELEFONO: str | None = _seed_sc.ADMIN_TELEFONO
    SEED_ADMIN_NOMBRES: str = _seed_sc.ADMIN_NOMBRES
    SEED_ADMIN_APELLIDOS: str = _seed_sc.ADMIN_APELLIDOS
    SEED_ADMIN_USERNAME: str | None = _seed_sc.ADMIN_USERNAME

    # ── Seed cliente demo (app móvil / portal cliente) ─────────
    SEED_CLIENTE_ON_START: bool = False
    SEED_CLIENTE_EMAIL: str | None = _seed_sc.CLIENTE_EMAIL
    SEED_CLIENTE_PASSWORD: str | None = _seed_sc.CLIENTE_PASSWORD
    SEED_CLIENTE_TELEFONO: str | None = _seed_sc.CLIENTE_TELEFONO
    SEED_CLIENTE_NOMBRES: str = _seed_sc.CLIENTE_NOMBRES
    SEED_CLIENTE_APELLIDOS: str = _seed_sc.CLIENTE_APELLIDOS
    SEED_CLIENTE_CIUDAD: str | None = _seed_sc.CLIENTE_CIUDAD
    SEED_CLIENTE_DIRECCION: str | None = _seed_sc.CLIENTE_DIRECCION

    # ── Seed taller demo (portal taller / responsable) ───────
    SEED_TALLER_ON_START: bool = False
    SEED_TALLER_EMAIL: str | None = _seed_sc.TALLER_EMAIL
    SEED_TALLER_PASSWORD: str | None = _seed_sc.TALLER_PASSWORD
    SEED_TALLER_TELEFONO: str | None = _seed_sc.TALLER_TELEFONO
    SEED_TALLER_RESPONSABLE_NOMBRES: str = _seed_sc.TALLER_RESPONSABLE_NOMBRES
    SEED_TALLER_RESPONSABLE_APELLIDOS: str = _seed_sc.TALLER_RESPONSABLE_APELLIDOS
    SEED_TALLER_NOMBRE_COMERCIAL: str = _seed_sc.TALLER_NOMBRE_COMERCIAL
    SEED_TALLER_CIUDAD: str = _seed_sc.TALLER_CIUDAD
    SEED_TALLER_DIRECCION: str = _seed_sc.TALLER_DIRECCION
    SEED_TALLER_DESCRIPCION: str | None = _seed_sc.TALLER_DESCRIPCION

    # ── Seed técnico demo (app móvil técnico; requiere un taller) ─
    SEED_TECNICO_ON_START: bool = False
    SEED_TECNICO_EMAIL: str | None = _seed_sc.TECNICO_EMAIL
    SEED_TECNICO_PASSWORD: str | None = _seed_sc.TECNICO_PASSWORD
    SEED_TECNICO_TELEFONO: str | None = _seed_sc.TECNICO_TELEFONO
    SEED_TECNICO_NOMBRES: str = _seed_sc.TECNICO_NOMBRES
    SEED_TECNICO_APELLIDOS: str = _seed_sc.TECNICO_APELLIDOS

    # ── Seed datos demo Santa Cruz (emergencias, bandeja, pagos/comisiones) ──
    # En `python -m app.seeds` siempre se ejecuta con require_enabled_flag=False.
    # En arranque del backend solo si está en True (evitar sorpresas en prod).
    SEED_DEMO_SANTA_CRUZ_ON_START: bool = False

    # ── Seed demo “media prioridad”: notificaciones, chat, ai_payload, disponibilidad, 2º taller ──
    # Misma convención que Santa Cruz: CLI con require_enabled_flag=False; arranque solo si True.
    SEED_DEMO_MEDIA_PRIORIDAD_ON_START: bool = False
    SEED_TALLER2_EMAIL: str | None = _seed_sc.TALLER2_EMAIL
    SEED_TALLER2_PASSWORD: str | None = _seed_sc.TALLER2_PASSWORD
    SEED_TALLER2_TELEFONO: str | None = _seed_sc.TALLER2_TELEFONO
    SEED_TALLER2_RESPONSABLE_NOMBRES: str = _seed_sc.TALLER2_RESPONSABLE_NOMBRES
    SEED_TALLER2_RESPONSABLE_APELLIDOS: str = _seed_sc.TALLER2_RESPONSABLE_APELLIDOS
    SEED_TALLER2_NOMBRE_COMERCIAL: str = _seed_sc.TALLER2_NOMBRE_COMERCIAL
    SEED_TALLER2_CIUDAD: str = _seed_sc.TALLER2_CIUDAD
    SEED_TALLER2_DIRECCION: str = _seed_sc.TALLER2_DIRECCION
    SEED_TALLER2_DESCRIPCION: str | None = _seed_sc.TALLER2_DESCRIPCION

    # ── Seed stress visual (catálogos extra + clientes listados; no crítico para flujos demo) ──
    SEED_STRESS_VISUAL_ON_START: bool = False
    SEED_STRESS_CLIENT_PASSWORD: str | None = _seed_sc.STRESS_PASSWORD

    # ── Pagos CU20 — simulación local; desactivar autocmpletar para flujo tipo pasarela (2 pasos) ──
    PAGO_SIMULADO_AUTOCOMPLETE: bool = True
    PAGO_PROVEEDOR_DEFAULT: str = "SIMULADO"
    # Stripe (opcional). Nunca reutilices el nombre SECRET_KEY aquí: en FastAPI es el JWT.
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_PUBLISHABLE_KEY: str | None = None

    @property
    def stripe_enabled(self) -> bool:
        return bool(self.STRIPE_SECRET_KEY and self.STRIPE_SECRET_KEY.strip())

    # ── Firebase Cloud Messaging (CU19) — opcional; ruta al JSON de cuenta de servicio ──
    FCM_ENABLED: bool = False
    FIREBASE_CREDENTIALS_PATH: str | None = None  # ej. firebase-credentials.json (relativo a backend/)
    # Alternativa para Render/cloud: contenido JSON completo del service account como variable de entorno.
    FIREBASE_CREDENTIALS_JSON: str | None = None

    @property
    def firebase_credentials_file(self) -> Path | None:
        if not self.FIREBASE_CREDENTIALS_PATH:
            return None
        p = Path(self.FIREBASE_CREDENTIALS_PATH)
        if p.is_file():
            return p
        cand = _BACKEND_DIR / self.FIREBASE_CREDENTIALS_PATH
        if cand.is_file():
            return cand
        return None

    # ── Correo (MailHog en Docker: SMTP 1025, UI 8025) ─────────
    EMAIL_ENABLED: bool = True
    # Si true, un fallo SMTP hace fallar la petición (recomendado en producción).
    EMAIL_STRICT: bool = False
    SMTP_HOST: str
    SMTP_PORT: int = 1025
    SMTP_TIMEOUT_SECONDS: int = 15
    SMTP_USE_TLS: bool = False
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    MAIL_FROM: str
    # URL base pública del API (enlaces en correos). Obligatorio en `.env` (IP o dominio del servidor).
    EMAIL_LINK_BASE_URL: str
    # URL pública del SPA (Angular). Definir en `.env`.
    FRONTEND_PUBLIC_URL: str
    # Atajos de despliegue (IP elástica / dominio): si están definidos, tienen prioridad sobre las dos anteriores.
    API_PUBLIC_URL: str | None = None
    APP_PUBLIC_URL: str | None = None

    # ── Cotizaciones — traslado del técnico al incidente (Bs por km) ──
    COTIZACION_TARIFA_TRASLADO_BS_KM: float = 5.0

    # ── Servicio de inferencia IA (contenedor Docker ai-inference) ──
    AI_ENABLED: bool = False
    AI_INFERENCE_BASE_URL: str | None = None
    AI_INFERENCE_TIMEOUT_S: float = 120.0
    AI_MAX_AUDIO_BYTES: int = 15 * 1024 * 1024
    AI_MAX_IMAGE_BYTES: int = 12 * 1024 * 1024
    # Si true, no llama al worker: útil en tests o sin contenedor IA.
    AI_INFERENCE_STUB: bool = False

    # Evidencias CU13/CU14 — subida directa al API (multipart). URL pública del fichero (IA / taller).
    # Si es None, se usa API_PUBLIC_URL o el Host de cada petición. En Docker interno a veces conviene
    # fijar EVIDENCIAS_PUBLIC_BASE_URL al origen alcanzable desde otros servicios.
    EVIDENCIAS_PUBLIC_BASE_URL: str | None = None
    EVIDENCIA_MAX_UPLOAD_BYTES: int = 15 * 1024 * 1024

    @property
    def api_public_base_url(self) -> str:
        """Base pública del API (emails, etc.): `API_PUBLIC_URL` o `EMAIL_LINK_BASE_URL`."""
        u = (self.API_PUBLIC_URL or self.EMAIL_LINK_BASE_URL or "").strip()
        return u.rstrip("/")

    @property
    def app_public_base_url(self) -> str:
        """URL pública del front (SPA Angular): `APP_PUBLIC_URL` o `FRONTEND_PUBLIC_URL`."""
        u = (self.APP_PUBLIC_URL or self.FRONTEND_PUBLIC_URL or "").strip()
        return u.rstrip("/")

    @property
    def evidencias_upload_dir(self) -> Path:
        return _BACKEND_DIR / "uploads" / "evidencias"

    # ── Backup automático ──────────────────────────────────────────────────────
    BACKUP_AUTO_ENABLED: bool = True
    BACKUP_INTERVAL_HOURS: int = 24
    BACKUP_MAX_FILES: int = 7
    BACKUP_DIR: str = "/app/backups"

    @property
    def backup_dir_path(self) -> Path:
        p = Path(self.BACKUP_DIR)
        return p if p.is_absolute() else _BACKEND_DIR / self.BACKUP_DIR


settings = Settings()
