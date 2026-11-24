"""Hoja de contacto para el control de calidad: 8 fotogramas de cada vídeo en una sola imagen.

    python engine/contact_sheet.py output/011-*/video.mp4 [más vídeos...]

Escribe contact.jpg junto a cada vídeo (4 columnas x 2 filas, con la marca de tiempo).
"""
from __future__ import annotations

import glob
import io
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import FFMPEG, font  # noqa: E402

TW, TH, N = 270, 480, 8


def frame_at(video: Path, t: float, tw: int = TW, th: int = TH) -> Image.Image:
    out = subprocess.run([FFMPEG, "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                          "-vf", f"scale={tw}:{th}", "-f", "image2pipe", "-vcodec", "png", "-"],
                         capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(out)).convert("RGB")


def sheet(video: Path, n: int = N) -> Path:
    _frames, secs = imageio_ffmpeg.count_frames_and_secs(str(video))
    first = subprocess.run([FFMPEG, "-v", "error", "-i", str(video), "-frames:v", "1", "-f", "image2pipe",
                            "-vcodec", "png", "-"], capture_output=True, check=True).stdout
    w0, h0 = Image.open(io.BytesIO(first)).size
    tw, th = (TW, TH) if h0 >= w0 else (480, 270)  # vertical (Short) u horizontal (documental)
    cols = 4
    rows = (n + cols - 1) // cols
    times = [0.7] + [secs * (i + 0.5) / (n - 1) for i in range(1, n - 1)] + [max(0.0, secs - 1.0)]
    img = Image.new("RGB", (tw * cols, th * rows), (0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font("bold", 22)
    for i, t in enumerate(times):
        x, y = (i % cols) * tw, (i // cols) * th
        img.paste(frame_at(video, t, tw, th), (x, y))
        lab = f"{int(t // 60)}:{t % 60:04.1f}" if secs >= 60 else f"{t:4.1f}s"
        d.rectangle([x, y, x + 20 + 13 * len(lab), y + 30], fill=(0, 0, 0))
        d.text((x + 6, y + 2), lab, font=f, fill=(255, 210, 63))
    out = video.with_name("contact.jpg")
    img.save(out, quality=88)
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    n = N
    if args and args[0].startswith("--n="):  # p. ej. --n=16 para documentales
        n, args = int(args[0][4:]), args[1:]
    for pattern in args:
        for p in sorted(glob.glob(pattern)) or [pattern]:
            print(sheet(Path(p), n))
