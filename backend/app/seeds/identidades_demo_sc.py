# -*- coding: utf-8 -*-
"""Identidades y datos por defecto del seed local — Santa Cruz de la Sierra, Bolivia.

Dominio `*.sc-demo.test` (RFC 2606, entorno de prueba). Teléfonos +591 7… con 8 dígitos
locales plausibles (bloque reservado para desarrollo, no son líneas públicas reales).

Contraseña única corta para cuentas demo; sobreescribible con variables SEED_* en .env.
"""
from __future__ import annotations

import unicodedata
from decimal import Decimal

# --- Común -----------------------------------------------------------------
CIUDAD_SANTA_CRUZ = "Santa Cruz de la Sierra"
DEMO_PASSWORD = "scdemo1"

# Centro ciudad (incidentes demo, mapas)
GEO_SC_CENTRO_LAT = Decimal("-17.783493")
GEO_SC_CENTRO_LNG = Decimal("-63.182129")

# Taller principal — zona Equipetrol / Av. Monseñor Rivero
TALLER_PRINCIPAL_LAT = Decimal("-17.7612")
TALLER_PRINCIPAL_LNG = Decimal("-63.1944")

# Segundo taller (misma ciudad, zona norte / 4to anillo, competencia local)
TALLER_SECUNDARIO_LAT = Decimal("-17.7320")
TALLER_SECUNDARIO_LNG = Decimal("-63.1650")

# --- Admin -----------------------------------------------------------------
ADMIN_EMAIL = "patricio.mendez@sc-demo.test"
ADMIN_PASSWORD = DEMO_PASSWORD
ADMIN_TELEFONO = "+59177010010"
ADMIN_NOMBRES = "Patricio"
ADMIN_APELLIDOS = "Méndez"
ADMIN_USERNAME = "admin"

# --- Cliente principal (app móvil cliente) ---------------------------------
CLIENTE_EMAIL = "carlos.vega@sc-demo.test"
CLIENTE_PASSWORD = DEMO_PASSWORD
CLIENTE_TELEFONO = "+59177010011"
CLIENTE_NOMBRES = "Carlos"
CLIENTE_APELLIDOS = "Vega"
CLIENTE_CIUDAD = CIUDAD_SANTA_CRUZ
CLIENTE_DIRECCION = "Barrio Equipetrol, a cuadras del Cristo — casa con portón verde"

# --- Taller principal + responsable ----------------------------------------
TALLER_EMAIL = "luis.rivera@sc-demo.test"
TALLER_PASSWORD = DEMO_PASSWORD
TALLER_TELEFONO = "+59177010012"
TALLER_RESPONSABLE_NOMBRES = "Luis"
TALLER_RESPONSABLE_APELLIDOS = "Rivera"
TALLER_NOMBRE_COMERCIAL = "Mecánica Express Rivero"
TALLER_CIUDAD = CIUDAD_SANTA_CRUZ
TALLER_DIRECCION = "Av. Monseñor Rivero 1521, entre 2º y 3er anillo, Santa Cruz"
TALLER_DESCRIPCION = "Mecánica general, auxilio vial y taller móvil de guardia en Santa Cruz."

# --- Técnico ---------------------------------------------------------------
TECNICO_EMAIL = "marco.salas@sc-demo.test"
TECNICO_PASSWORD = DEMO_PASSWORD
TECNICO_TELEFONO = "+59177010013"
TECNICO_NOMBRES = "Marco"
TECNICO_APELLIDOS = "Salas"

# --- Segundo taller (multi-taller / bandeja) -------------------------------
TALLER2_EMAIL = "rodrigo.torrez@sc-demo.test"
TALLER2_PASSWORD = DEMO_PASSWORD
TALLER2_TELEFONO = "+59177010014"
TALLER2_RESPONSABLE_NOMBRES = "Rodrigo"
TALLER2_RESPONSABLE_APELLIDOS = "Torrez"
TALLER2_NOMBRE_COMERCIAL = "Auxilio Vial 4to Anillo SC"
TALLER2_CIUDAD = CIUDAD_SANTA_CRUZ
TALLER2_DIRECCION = "Radial 27 casi 4to anillo, Galpón 12, zona norte"
TALLER2_DESCRIPCION = "Grúa liviana, cambio de batería y asistencia en ruta en Santa Cruz."

# --- Stress visual: más clientes (nombres comunes BO / SC) -----------------
STRESS_EMAIL_DOMAIN = "lista.sc-demo.test"
STRESS_PASSWORD = DEMO_PASSWORD

_STRESS_PERSONAS: tuple[tuple[str, str], ...] = (
    ("Valentina", "Suárez"),
    ("Diego", "Camacho"),
    ("Fernanda", "Quiroga"),
    ("José Luis", "Aguilera"),
    ("Andrea", "Peña"),
    ("Ricardo", "Villanueva"),
    ("María Elena", "Rojas"),
    ("Gabriel", "Ortiz"),
)


def _slug_ascii(s: str) -> str:
    nk = unicodedata.normalize("NFKD", s)
    base = "".join(c for c in nk if not unicodedata.combining(c))
    return base.lower().replace(" ", "").replace("'", "")


def stress_cliente_email(i: int) -> str:
    """i en 1..N — email único por índice y nombre."""
    nom, ape = _STRESS_PERSONAS[(i - 1) % len(_STRESS_PERSONAS)]
    return f"{_slug_ascii(nom)}.{_slug_ascii(ape)}.{i:02d}@{STRESS_EMAIL_DOMAIN}"


def stress_cliente_telefono(i: int) -> str:
    """+591 7702 1xxx — ocho dígitos locales; distinto al bloque 770100xx principal."""
    return f"+59177021{i:03d}"


def stress_cliente_nombres_apellidos(i: int) -> tuple[str, str]:
    nom, ape = _STRESS_PERSONAS[(i - 1) % len(_STRESS_PERSONAS)]
    return nom, ape


STRESS_BARRIOS_SC: tuple[str, ...] = (
    "Equipetrol",
    "Urbari",
    "Piraí",
    "Palermo norte",
    "2do anillo",
    "Los Tuses",
    "4to anillo norte",
    "Zona Sur — Urubó",
)
