# Extracción por reglas sobre texto transcrito (IA1 complemento).
from __future__ import annotations

import re
from dataclasses import dataclass

from app.modules.ai.text_normalize import normalize_for_match


@dataclass(frozen=True)
class AudioExtractResult:
    keywords: list[str]
    tipo_problema_mencionado: str | None
    urgencia_percibida: str
    contexto_breve: str


_BATERIA = (
    "batería",
    "bateria",
    "no enciende",
    "no prende",
    "arranque",
    "tablero",
    "luces apagadas",
    "descargad",
)
_LLANTA = (
    "llanta",
    "neumático",
    "neumatico",
    "pinchad",
    "goma",
    "rueda",
    "desinflad",
)
_CHOQUE = (
    "choque",
    "accidente",
    "impacto",
    "colision",
    "colisión",
    "golpe",
    "abollad",
    "airbag",
)
_MOTOR = (
    "motor",
    "sobrecalent",
    "temperatura",
    "humo",
    "fuga de aceite",
    "aceite",
    "check engine",
)
_URGENTE = (
    "urgente",
    "grave",
    "atrapad",
    "herid",
    "carretera",
    "autopista",
    "peligro",
    "incendio",
)


def extract_from_transcription(transcripcion: str) -> AudioExtractResult:
    t = normalize_for_match(transcripcion)
    if not t:
        return AudioExtractResult(
            keywords=[],
            tipo_problema_mencionado=None,
            urgencia_percibida="desconocida",
            contexto_breve="",
        )

    hits: list[str] = []
    for label, patterns in (
        ("batería", _BATERIA),
        ("llanta", _LLANTA),
        ("choque", _CHOQUE),
        ("motor", _MOTOR),
    ):
        for p in patterns:
            if normalize_for_match(p) in t:
                hits.append(label)
                break

    tipo: str | None = None
    if "choque" in hits:
        tipo = "choque"
    elif "motor" in hits:
        tipo = "motor"
    elif "llanta" in hits:
        tipo = "llanta"
    elif "batería" in hits:
        tipo = "batería"

    urg = "media"
    for u in _URGENTE:
        if normalize_for_match(u) in t:
            urg = "alta"
            break

    # contexto: primera oración o hasta 160 chars
    one = re.split(r"[.!?]\s+", transcripcion.strip())
    ctx = (one[0] if one else transcripcion)[:160].strip()

    kw_unique: list[str] = []
    seen: set[str] = set()
    for token in re.split(r"\s+", t):
        token = re.sub(r"^[^\w]+|[^\w]+$", "", token)
        if len(token) >= 4 and token not in seen:
            for p in _BATERIA + _LLANTA + _CHOQUE + _MOTOR:
                if p in token or token in p:
                    seen.add(token)
                    kw_unique.append(token)
                    break
        if len(kw_unique) >= 8:
            break

    return AudioExtractResult(
        keywords=kw_unique[:12],
        tipo_problema_mencionado=tipo,
        urgencia_percibida=urg,
        contexto_breve=ctx,
    )
