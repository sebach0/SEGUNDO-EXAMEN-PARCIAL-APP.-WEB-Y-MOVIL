# Contratos API — módulos IA 1–6
from __future__ import annotations

from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class IncidentCategory(str, Enum):
    BATERIA = "BATERIA"
    LLANTA = "LLANTA"
    CHOQUE = "CHOQUE"
    MOTOR = "MOTOR"
    OTROS = "OTROS"


class PriorityLevel(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"
    REVISION_MANUAL = "REVISION_MANUAL"


class ImageClarity(str, Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"


class FuenteInferencia(str, Enum):
    TEXTO = "texto"
    AUDIO = "audio"
    IMAGEN = "imagen"


class SeverityLevel(str, Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"


class DamageEvidenceItem(BaseModel):
    evidencia_id: str
    score: float = Field(..., ge=0.0, le=1.0)


class DamageEvidenceSupport(BaseModel):
    image: list[DamageEvidenceItem] = Field(default_factory=list)
    audio: list[DamageEvidenceItem] = Field(default_factory=list)
    text: list[DamageEvidenceItem] = Field(default_factory=list)


class DamageConflict(BaseModel):
    has_conflict: bool = False
    details: list[str] = Field(default_factory=list)


class DamagePrediction(BaseModel):
    label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    severity: SeverityLevel
    evidence_support: DamageEvidenceSupport = Field(default_factory=DamageEvidenceSupport)
    reasons: list[str] = Field(default_factory=list)
    conflict: DamageConflict = Field(default_factory=DamageConflict)


# --- IA1 audio ---
class AudioTranscribeResponse(BaseModel):
    transcripcion: str
    keywords: list[str] = Field(default_factory=list)
    confianza: float = Field(..., ge=0.0, le=1.0)
    tipo_problema_mencionado: str | None = None
    urgencia_percibida: str | None = None
    contexto_breve: str | None = None


# --- IA2 classify ---
class IncidentClassifyIn(BaseModel):
    texto_cliente: str | None = None
    transcripcion_audio: str | None = None
    transcripciones_audio: list[str] = Field(default_factory=list)
    hallazgos_vision: list[str] = Field(default_factory=list)
    hallazgos_vision_por_imagen: list[list[str]] = Field(default_factory=list)


class IncidentClassifyOut(BaseModel):
    categoria: IncidentCategory
    confianza: float = Field(..., ge=0.0, le=1.0)
    fuentes: list[str] = Field(default_factory=list)
    damages: list[DamagePrediction] = Field(default_factory=list)
    requires_manual_review: bool = False
    conflict_notes: list[str] = Field(default_factory=list)


# --- IA3 image (API pública) ---
class DeteccionObjeto(BaseModel):
    """Salida de detector preentrenado (p. ej. YOLO/COCO) en el worker de inferencia."""

    etiqueta: str
    confianza: float = Field(..., ge=0.0, le=1.0)


class ImageAnalyzeResponse(BaseModel):
    hallazgos: list[str] = Field(default_factory=list)
    claridad_imagen: ImageClarity
    confianza: float = Field(..., ge=0.0, le=1.0)
    objetos_detectados: list[DeteccionObjeto] = Field(
        default_factory=list,
        description="Clases COCO (etiqueta en español) con confianza por caja.",
    )
    modelo_deteccion: str | None = Field(
        None, description="Identificador del modelo usado, p. ej. yolov8n."
    )


class ImageAnalyzeItem(BaseModel):
    evidencia_id: str
    resultado: ImageAnalyzeResponse


class ImageAnalyzeBatchResponse(BaseModel):
    imagenes: list[ImageAnalyzeItem] = Field(default_factory=list)
    hallazgos_consolidados: list[str] = Field(default_factory=list)
    claridad_promedio: ImageClarity
    confianza_promedio: float = Field(..., ge=0.0, le=1.0)


# --- IA4 structured summary ---
class UbicacionResumenIn(BaseModel):
    latitud: Decimal | None = None
    longitud: Decimal | None = None
    direccion_referencia: str | None = None


class StructuredSummaryIn(BaseModel):
    texto_cliente: str | None = None
    transcripcion_audio: str | None = None
    transcripciones_audio: list[str] = Field(default_factory=list)
    hallazgos_vision: list[str] = Field(default_factory=list)
    hallazgos_vision_por_imagen: list[list[str]] = Field(default_factory=list)
    categoria: IncidentCategory | None = None
    ubicacion: UbicacionResumenIn | None = None


class FichaIncidente(BaseModel):
    tipo_problema: IncidentCategory
    ubicacion_valida: bool
    evidencia_audio: bool
    evidencia_imagen: bool
    incertidumbre: str = Field(..., description="BAJA | MEDIA | ALTA")


class StructuredSummaryOut(BaseModel):
    resumen: str
    ficha: FichaIncidente
    danos_detectados: list[str] = Field(default_factory=list)


# --- IA5 priority ---
class IncidentPrioritizeIn(BaseModel):
    texto_cliente: str | None = None
    transcripcion_audio: str | None = None
    transcripciones_audio: list[str] = Field(default_factory=list)
    hallazgos_vision: list[str] = Field(default_factory=list)
    hallazgos_vision_por_imagen: list[list[str]] = Field(default_factory=list)
    categoria: IncidentCategory | None = None
    direccion_referencia: str | None = None


class IncidentPrioritizeOut(BaseModel):
    nivel_prioridad: PriorityLevel
    motivo: list[str] = Field(default_factory=list)
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    damages_considerados: list[str] = Field(default_factory=list)


# --- IA6 assignment ---
class AssignmentRankIn(BaseModel):
    incident_lat: Decimal = Field(..., ge=Decimal("-90"), le=Decimal("90"))
    incident_lng: Decimal = Field(..., ge=Decimal("-180"), le=Decimal("180"))
    categoria: IncidentCategory
    nivel_prioridad: PriorityLevel
    ciudad_incidente: str | None = Field(
        None, description="Ciudad del incidente para matching con taller sin coords"
    )


class TallerCandidatoScore(BaseModel):
    taller_id: int
    nombre_comercial: str
    score: float
    detalle: dict = Field(default_factory=dict)


class AssignmentRankOut(BaseModel):
    candidatos: list[TallerCandidatoScore]
    mejor_taller_id: int | None = None
