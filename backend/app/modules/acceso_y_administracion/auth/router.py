# app/modules/auth/router.py
import html as html_module

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_user_permisos
from app.core.security import decode_token
from app.modules.acceso_y_administracion.auth import service
from app.modules.acceso_y_administracion.auth.schemas import (
    LoginRequest,
    MeResponse,
    RestablecerPasswordIn,
    SolicitarRecuperacionIn,
    TokenResponse,
)
from app.modules.acceso_y_administracion.roles.models import Rol, UsuarioRol
from app.modules.acceso_y_administracion.usuarios.models import Usuario

auth_router = APIRouter(prefix="/auth", tags=["Autenticación"])


@auth_router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Inicia sesión con email y contraseña. Devuelve access + refresh token."""
    return await service.login(body.email, body.password, db, request)


@auth_router.post(
    "/solicitar-recuperacion-contrasena", status_code=status.HTTP_204_NO_CONTENT
)
async def solicitar_recuperacion_contrasena(
    body: SolicitarRecuperacionIn,
    db: AsyncSession = Depends(get_db),
):
    """Envía correo con enlace (MailHog en dev). Respuesta uniforme por privacidad."""
    await service.solicitar_recuperacion_contrasena(body.email, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@auth_router.post("/restablecer-contrasena", status_code=status.HTTP_204_NO_CONTENT)
async def restablecer_contrasena(
    body: RestablecerPasswordIn,
    db: AsyncSession = Depends(get_db),
):
    """Consume token de un solo uso y fija nueva contraseña."""
    await service.restablecer_contrasena_con_token(body.token, body.password, db)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@auth_router.get("/verificar-email", response_class=HTMLResponse)
async def verificar_email(
    token: str = Query(..., min_length=10),
    db: AsyncSession = Depends(get_db),
):
    """Activa cuenta (PENDIENTE → ACTIVO). Enlace enviado al registrarse."""
    from app.modules.acceso_y_administracion.auth.email_tokens import consumir_token_verificar_email

    user = await consumir_token_verificar_email(db, token)
    if user is None:
        return HTMLResponse(
            content=(
                "<!DOCTYPE html><html lang='es'><meta charset='utf-8'><title>Enlace inválido</title>"
                "<body style='font-family:sans-serif;padding:2rem'>"
                "<h1>Enlace inválido o expirado</h1>"
                "<p>Si ya verificaste antes, abre la app o el portal e inicia sesión. "
                "Si el enlace caducó, vuelve a registrarte o solicita ayuda.</p></body></html>"
            ),
            status_code=400,
        )
    fe = settings.app_public_base_url
    nombre = html_module.escape((user.nombres or "").strip() or "Usuario")
    login_taller = f"{fe}/taller"
    login_taller_registro = f"{fe}/taller/registro"
    return HTMLResponse(
        content=(
            "<!DOCTYPE html><html lang='es'><meta charset='utf-8'><title>Cuenta verificada</title>"
            "<body style='font-family:sans-serif;padding:2rem;max-width:36rem;line-height:1.55'>"
            "<h1>Cuenta verificada</h1>"
            f"<p>Hola <strong>{nombre}</strong>, tu correo quedó confirmado.</p>"
            "<p><strong>App móvil (cliente):</strong> vuelve a la aplicación e inicia sesión con tu correo y contraseña.</p>"
            f"<p><strong>Portal web taller:</strong> "
            f'<a href="{login_taller}">iniciar sesión</a> '
            f"(si registraste un taller; acceso en <code>{login_taller}</code>).</p>"
            f'<p style="font-size:0.9rem;color:#444">¿Aún no completaste el alta del taller? '
            f'<a href="{login_taller_registro}">Registro taller</a>.</p>'
            "</body></html>"
        ),
        status_code=200,
    )


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cierra la sesión actual invalidando el token en BD."""
    auth_header = request.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "")
    try:
        payload = decode_token(token)
        jti = payload.get("jti")
    except JWTError:
        raise HTTPException(status_code=400, detail="Token inválido")
    await service.logout(current_user.id, jti, db, request)


@auth_router.get("/me", response_model=MeResponse)
async def me(
    user_and_perms: tuple = Depends(get_current_user_permisos),
    db: AsyncSession = Depends(get_db),
):
    """Devuelve el usuario autenticado con sus roles y permisos."""
    user, permisos = user_and_perms
    roles_result = await db.execute(
        select(Rol.nombre)
        .join(UsuarioRol, UsuarioRol.rol_id == Rol.id)
        .where(UsuarioRol.usuario_id == user.id)
    )
    roles = [r for (r,) in roles_result.fetchall()]
    return MeResponse(
        id=user.id,
        nombres=user.nombres,
        apellidos=user.apellidos,
        email=user.email,
        username=user.username,
        roles=roles,
        permisos=permisos,
    )
