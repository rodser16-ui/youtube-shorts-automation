"""Utilidades compartidas del motor de Shorts.

Multicanal: el código es uno solo (ROOT). Los datos de cada canal (config.json, guiones, vídeos,
cola, credenciales, marca, informes) viven en DATA:
  * sin variable de entorno  -> DATA = ROOT  (Ciencia con Pruebas, exactamente como siempre)
  * $env:SHORTS_CHANNEL="hidden-wonders" -> DATA = ROOT/channels/hidden-wonders
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import ImageFont

ROOT = Path(__file__).resolve().parent.parent
CHANNEL = os.environ.get("SHORTS_CHANNEL", "").strip()
DATA = ROOT / "channels" / CHANNEL if CHANNEL else ROOT
if CHANNEL and not (DATA / "config.json").exists():
    raise SystemExit(f"Canal desconocido: {CHANNEL} (no existe {DATA / 'config.json'})")
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1080, 1920, 30
SR = 48000  # frecuencia de muestreo del audio final

# Textos que aparecen en pantalla o en la descripción. Los valores por defecto son los de
# Ciencia con Pruebas; cada canal puede cambiarlos en config.json -> "strings".
DEFAULT_STRINGS = {
    "stamp": "PRUEBA", "source": "FUENTE", "number": "Nº",
    "sources_heading": "📚 Fuentes:", "images_heading": "🖼️ Imágenes (dominio público / licencia libre):",
    "synthetic_marker": "sintétic",  # palabra que el control de calidad busca en el aviso de IA
}


def load_config() -> dict:
    cfg = json.loads((DATA / "config.json").read_text(encoding="utf-8"))
    cfg["strings"] = {**DEFAULT_STRINGS, **cfg.get("strings", {})}
    cfg["channel"].setdefault("language", "es")
    return cfg


_font_cache: dict = {}


def font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    """kind: 'anton' | 'black' | 'extrabold' | 'bold' | 'semibold' (Montserrat)."""
    key = (kind, size)
    if key in _font_cache:
        return _font_cache[key]
    fdir = ROOT / "assets" / "fonts"
    if kind == "anton":
        f = ImageFont.truetype(str(fdir / "Anton-Regular.ttf"), size)
    else:
        f = ImageFont.truetype(str(fdir / "Montserrat-VF.ttf"), size)
        name = {"black": b"Black", "extrabold": b"ExtraBold", "bold": b"Bold",
                "semibold": b"SemiBold"}[kind]
        f.set_variation_by_name(name)
    _font_cache[key] = f
    return f


def decode_audio(path: Path) -> np.ndarray:
    """Decodifica cualquier audio a float32 mono a SR Hz."""
    cmd = [FFMPEG, "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1",
           "-ar", str(SR), "-"]
    out = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
