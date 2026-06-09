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
    "batería", "bateria", "no enciende", "no prende", "arranque",
    "tablero", "luces apagadas", "descargad", "no arranca",
    "batería muerta", "bateria muerta", "sin corriente",
    "alternador", "cortocircuito", "starter", "no tiene carga",
    "se descargó", "motor no arranca",
)
_LLANTA = (
    "llanta", "neumático", "neumatico", "pinchad", "goma",
    "rueda", "desinflad", "se reventó", "ponchad", "ponchó",
    "llantazo", "llanta reventada", "goma baja", "goma reventada",
    "se revento la goma",
)
_CHOQUE = (
    "choque", "accidente", "impacto", "colision", "colisión",
    "golpe", "abollad", "airbag", "volcó", "volco", "volcad",
    "estrellé", "chocó", "chocamos", "nos chocaron",
    "se salió de la vía", "salió de la via",
)
_MOTOR = (
    "motor", "sobrecalent", "temperatura", "humo", "fuga de aceite",
    "aceite", "check engine", "vibra", "traquetea", "se apagó",
    "se paró", "perdió potencia", "se ahoga", "correa", "embrague",
    "clutch", "refrigerante", "recalentado", "agua hirviendo",
    "vapor", "pierde aceite", "gotea aceite", "falla mecanica",
)
_URGENTE = (
    "urgente", "urgentísimo", "urgentisimo", "grave", "gravísimo",
    "atrapad", "herid", "carretera", "autopista", "peligro",
    "incendio", "explosión", "explosion", "fuego", "llamas",
    "no puedo salir", "inconsciente", "desmayad", "sangre",
    "volcamos", "volcó", "me estrellé", "personas heridas",
    "niños", "nino", "bebé", "bebe atrapado",
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

    # contexto: primera oración o hasta 200 chars
    sentences = re.split(r"[.!?]\s+", transcripcion.strip())
    ctx = (sentences[0] if sentences else transcripcion)[:200].strip()

    all_patterns = _BATERIA + _LLANTA + _CHOQUE + _MOTOR
    kw_unique: list[str] = []
    seen: set[str] = set()
    for token in re.split(r"\s+", t):
        token = re.sub(r"^[^\w]+|[^\w]+$", "", token)
        if len(token) >= 4 and token not in seen:
            for p in all_patterns:
                np = normalize_for_match(p)
                if np and (np in token or token in np):
                    seen.add(token)
                    kw_unique.append(token)
                    break
        if len(kw_unique) >= 12:
            break

    return AudioExtractResult(
        keywords=kw_unique[:12],
        tipo_problema_mencionado=tipo,
        urgencia_percibida=urg,
        contexto_breve=ctx,
    )
