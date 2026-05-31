# Normalización para comparar texto sin depender de mayúsculas / acentos débiles.
from __future__ import annotations

import re
import unicodedata


def strip_accents(s: str) -> str:
    """Convierte á→a, ñ permanece como n+tilde descompuesto → mejor dejar ñ: NFD quita tilde de ñ a n+◌̃."""
    decomposed = unicodedata.normalize("NFD", s)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def normalize_for_match(s: str | None) -> str:
    """
    Texto comparable entre sí: Unicode NFKC, sin marcas diacríticas, casefold, espacios colapsados.
    Así "Motor", "MOTOR", "motor" y "MoToR" coinciden; "Colisión" vs "colision" también.
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = strip_accents(s)
    s = s.casefold()
    s = re.sub(r"\s+", " ", s).strip()
    return s


def contains_normalized(haystack: str | None, needle: str | None) -> bool:
    """¿`needle` aparece como subcadena en `haystack` tras normalizar ambos?"""
    if not haystack or not needle:
        return False
    return normalize_for_match(needle) in normalize_for_match(haystack)
