"""Narración con voces neuronales + marcas de tiempo por palabra.

Proveedor por defecto: edge-tts (voces neuronales de Microsoft, sin clave).
Para producción comercial se recomienda Azure AI Speech (mismas voces, uso
comercial con licencia y nivel gratuito mensual). Ver README.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path

import edge_tts


async def _synth(text: str, voice: str, rate: str, pitch: str, out_mp3: Path) -> list:
    comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch,
                                boundary="WordBoundary")
    words = []
    with open(out_mp3, "wb") as fh:
        async for ch in comm.stream():
            if ch["type"] == "audio":
                fh.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append({"start": ch["offset"] / 1e7,
                              "dur": ch["duration"] / 1e7,
                              "text": ch["text"]})
    return words


def synth(text: str, voice: str, rate: str, pitch: str, cache_dir: Path) -> tuple[Path, list]:
    """Sintetiza (con caché) y devuelve (ruta_mp3, palabras)."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(f"{voice}|{rate}|{pitch}|{text}".encode()).hexdigest()[:16]
    mp3 = cache_dir / f"{key}.mp3"
    meta = cache_dir / f"{key}.json"
    if mp3.exists() and meta.exists() and mp3.stat().st_size > 0:
        return mp3, json.loads(meta.read_text(encoding="utf-8"))
    last_err = None
    for _ in range(3):
        try:
            words = asyncio.run(_synth(text, voice, rate, pitch, mp3))
            if mp3.stat().st_size == 0 or not words:
                raise RuntimeError("TTS vacío")
            meta.write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
            return mp3, words
        except Exception as e:  # red inestable: reintentar
            last_err = e
    raise RuntimeError(f"Fallo TTS: {last_err}")
