# FastAPI mínimo: STT (faster-whisper) + VAD (Silero) + visión MVP (nitidez OpenCV).
from __future__ import annotations

import io
import logging
import os
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np
import soundfile as sf
import torch
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:
    pass

_log = logging.getLogger(__name__)

app = FastAPI(title="AI Inference — Emergencias", version="0.1.0")

_whisper_model = None
_vad_bundle: tuple | None = None
# Cache por ruta de pesos (detect o classify).
_yolo_models: dict[str, object] = {}

# COCO (inglés) → etiqueta legible en español para la API del taller.
_COCO_ES: dict[str, str] = {
    "person": "persona",
    "car": "automóvil",
    "truck": "camión",
    "bus": "autobús",
    "motorcycle": "motocicleta",
    "bicycle": "bicicleta",
    "train": "tren",
    "boat": "embarcación",
    "airplane": "avión",
    "traffic light": "semáforo",
    "fire hydrant": "hidrante",
    "stop sign": "señal de stop",
    "parking meter": "parquímetro",
    "bench": "banco",
    "bird": "pájaro",
    "cat": "gato",
    "dog": "perro",
    "horse": "caballo",
    "sheep": "oveja",
    "cow": "vaca",
    "elephant": "elefante",
    "bear": "oso",
    "zebra": "cebra",
    "giraffe": "jirafa",
}

_VEHICLE = frozenset({"car", "truck", "bus", "motorcycle", "train"})


def _whisper():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel

        size = os.environ.get("WHISPER_MODEL_SIZE", "small")
        _log.info("Cargando WhisperModel %s (CPU int8)...", size)
        _whisper_model = WhisperModel(size, device="cpu", compute_type="int8")
    return _whisper_model


def _silero():
    global _vad_bundle
    if _vad_bundle is None:
        _log.info("Cargando Silero VAD (torch.hub)...")
        model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            onnx=False,
            trust_repo=True,
        )
        _vad_bundle = (model, utils)
    return _vad_bundle


def _ffmpeg_to_wav_16k_mono(src: str, dst: str) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            src,
            "-ar",
            "16000",
            "-ac",
            "1",
            dst,
        ],
        check=True,
    )


def _get_yolo(model_path: str):
    if model_path not in _yolo_models:
        from ultralytics import YOLO

        _log.info("Cargando YOLO desde %s", model_path)
        _yolo_models[model_path] = YOLO(model_path)
    return _yolo_models[model_path]


def _yolo_classify(img_bgr: np.ndarray, model_path: str) -> tuple[list[str], list[dict], str | None]:
    """Modelo entrenado en Colab (clasificación por carpetas / YOLOv8-cls)."""
    try:
        m = _get_yolo(model_path)
        imgsz = int(os.environ.get("YOLO_IMGSZ", "224"))
        res = m.predict(source=img_bgr, verbose=False, imgsz=imgsz)[0]
    except Exception:
        _log.exception("Fallo YOLO classify")
        return [], [], os.path.basename(model_path)

    probs = getattr(res, "probs", None)
    names = getattr(res, "names", None) or {}
    if probs is None:
        return [], [], os.path.basename(model_path)

    def _f(x) -> float:
        if x is None:
            return 0.0
        if hasattr(x, "item"):
            return float(x.item())
        return float(x)

    top1_i = int(probs.top1)
    top1_name = str(names.get(top1_i, str(top1_i)))
    top1_conf = _f(getattr(probs, "top1conf", None))

    def _as_int_list(v) -> list[int]:
        if v is None:
            return []
        if isinstance(v, (list, tuple)):
            return [int(x) for x in v]
        v = getattr(v, "cpu", lambda: v)()
        v = getattr(v, "numpy", lambda: v)()
        if hasattr(v, "tolist"):
            v = v.tolist()
        return [int(x) for x in (v if isinstance(v, (list, tuple)) else [v])]

    def _as_float_list(v) -> list[float]:
        if v is None:
            return []
        if isinstance(v, (list, tuple)):
            return [float(x) for x in v]
        v = getattr(v, "cpu", lambda: v)()
        v = getattr(v, "numpy", lambda: v)()
        if hasattr(v, "tolist"):
            v = v.tolist()
        return [float(x) for x in (v if isinstance(v, (list, tuple)) else [v])]

    t5 = getattr(probs, "top5", None)
    t5c = getattr(probs, "top5conf", None)
    idxs = _as_int_list(t5) if t5 is not None else [top1_i]
    cfs = _as_float_list(t5c) if t5c is not None else [top1_conf]
    if not idxs:
        idxs = [top1_i]
    if not cfs:
        cfs = [top1_conf]

    objetos: list[dict] = []
    for j, cid in enumerate(idxs[:5]):
        cf = _f(cfs[j]) if j < len(cfs) else 0.0
        nm = str(names.get(int(cid), str(cid)))
        objetos.append({"etiqueta": nm, "confianza": round(cf, 3)})

    hallazgos = [f"clasificación imagen (modelo propio): {top1_name}"]
    return hallazgos, objetos, os.path.basename(model_path)


def _yolo_detect_coco(img_bgr: np.ndarray, model_path: str) -> tuple[list[str], list[dict], str | None]:
    """
    Detección con YOLOv8 preentrenado (COCO). Contexto personas/vehículos.
    """
    try:
        m = _get_yolo(model_path)
        conf_th = float(os.environ.get("YOLO_CONF", "0.35"))
        res = m.predict(
            source=img_bgr,
            verbose=False,
            conf=conf_th,
            imgsz=int(os.environ.get("YOLO_IMGSZ", "640")),
        )[0]
    except Exception:
        _log.exception("Fallo inferencia YOLO detect")
        return [], [], os.path.basename(model_path)

    if res.boxes is None or len(res.boxes) == 0:
        return [], [], os.path.basename(model_path)

    names: dict[int, str] = res.names  # type: ignore[assignment]
    hallazgos: list[str] = []
    objetos: list[dict] = []
    coco_keys: set[str] = set()

    for b in res.boxes:
        cid = int(b.cls.item())
        key = names.get(cid, str(cid))
        cf = float(b.conf.item())
        coco_keys.add(key)
        etiqueta = _COCO_ES.get(key, key)
        objetos.append({"etiqueta": etiqueta, "confianza": round(cf, 3)})

    if "person" in coco_keys:
        hallazgos.append("detección YOLO: persona visible en la escena")
    if coco_keys & _VEHICLE:
        hallazgos.append("detección YOLO: vehículo motorizado visible")
    if "person" in coco_keys and (coco_keys & _VEHICLE):
        hallazgos.append(
            "detección YOLO: personas y vehículo en la misma imagen (contexto de posible incidente)"
        )

    ckpt = getattr(m, "ckpt_path", None)
    modelo = os.path.basename(str(ckpt)) if ckpt else os.path.basename(model_path)
    return hallazgos, objetos, modelo


def _yolo_run(img_bgr: np.ndarray) -> tuple[list[str], list[dict], str | None]:
    if os.environ.get("YOLO_ENABLED", "true").lower() in ("0", "false", "no"):
        return [], [], None
    try:
        from ultralytics import YOLO  # noqa: F401
    except Exception as e:
        _log.warning("ultralytics no disponible: %s", e)
        return [], [], None

    model_path = os.environ.get("YOLO_MODEL", "yolov8n.pt")
    task = os.environ.get("YOLO_TASK", "detect").strip().lower()

    if task == "classify":
        return _yolo_classify(img_bgr, model_path)
    return _yolo_detect_coco(img_bgr, model_path)


def _wav_to_tensor_16k(path: str) -> torch.Tensor:
    wav, sr = sf.read(path, always_2d=True)
    wav = wav.mean(axis=1).astype(np.float32)
    if sr != 16000:
        raise ValueError(f"Sample rate inesperado: {sr}")
    return torch.from_numpy(wav)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-inference"}


@app.post("/internal/audio/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    raw = await file.read()
    if not raw:
        raise HTTPException(400, detail="Archivo vacío.")

    suffix = Path(file.filename or "audio.bin").suffix or ".bin"
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, f"in{suffix}")
        wav_path = os.path.join(tmp, "in_16k.wav")
        with open(src, "wb") as f:
            f.write(raw)
        try:
            _ffmpeg_to_wav_16k_mono(src, wav_path)
        except subprocess.CalledProcessError as e:
            raise HTTPException(400, detail="No se pudo decodificar el audio (ffmpeg).") from e

        wav_tensor = _wav_to_tensor_16k(wav_path)
        vad_model, utils = _silero()
        get_speech_timestamps = utils[0]
        timestamps = get_speech_timestamps(
            wav_tensor,
            vad_model,
            sampling_rate=16000,
            threshold=0.5,
            min_speech_duration_ms=250,
            max_speech_duration_s=float("inf"),
        )
        rms = float(torch.sqrt((wav_tensor**2).mean()).item())
        has_voice = len(timestamps) > 0 or rms > 0.012

        if not has_voice:
            return {
                "text": "",
                "confidence": 0.12,
                "vad_has_voice": False,
                "language": "es",
            }

        model = _whisper()
        segments, info = model.transcribe(
            wav_path,
            language="es",
            beam_size=3,
            vad_filter=False,
        )
        parts: list[str] = []
        logprobs: list[float] = []
        for seg in segments:
            parts.append(seg.text.strip())
            if seg.avg_logprob is not None:
                logprobs.append(float(seg.avg_logprob))
        text = " ".join(p for p in parts if p).strip()
        if not text:
            conf = 0.25
        elif logprobs:
            conf = max(0.2, min(0.98, 1.0 + sum(logprobs) / max(len(logprobs), 1) / 3.0))
        else:
            conf = 0.75 if text else 0.3

        return {
            "text": text,
            "confidence": round(conf, 3),
            "vad_has_voice": has_voice,
            "language": getattr(info, "language", "es"),
        }


@app.post("/internal/vision/analyze")
async def analyze_image(file: UploadFile = File(...)):
    raw = await file.read()
    if not raw:
        raise HTTPException(400, detail="Archivo vacío.")

    nparr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        try:
            pil = Image.open(io.BytesIO(raw)).convert("RGB")
            img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        except Exception as e:
            raise HTTPException(400, detail="Imagen no válida.") from e

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F).var()
    mean_brightness = float(gray.mean())

    if lap < 40:
        claridad = "BAJA"
        conf = 0.45
        hallazgos = ["imagen poco clara o borrosa"]
    elif lap < 120:
        claridad = "MEDIA"
        conf = 0.65
        hallazgos = []
    else:
        claridad = "ALTA"
        conf = 0.72
        hallazgos = []

    if mean_brightness < 45:
        hallazgos.append("escena muy oscura")
        conf *= 0.9

    edges = cv2.Canny(gray, 80, 160)
    edge_ratio = float((edges > 0).mean())
    if edge_ratio > 0.18 and claridad != "BAJA":
        hallazgos.append("posible daño o detalle estructural visible (heurística bordes)")
        conf = min(0.85, conf + 0.05)

    yolo_hallazgos, objetos_detectados, modelo_path = _yolo_run(img)
    if yolo_hallazgos:
        for h in yolo_hallazgos:
            if h not in hallazgos:
                hallazgos.append(h)
        conf = min(0.92, conf + 0.04 * min(len(yolo_hallazgos), 3))

    return {
        "hallazgos": hallazgos,
        "claridad_imagen": claridad,
        "confianza": round(max(0.25, min(0.92, conf)), 2),
        "objetos_detectados": objetos_detectados,
        "modelo_deteccion": modelo_path,
    }
#si