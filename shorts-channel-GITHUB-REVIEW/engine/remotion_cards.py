"""Tarjetas animadas con Remotion (opcional).

Renderiza las tarjetas de un Short (stat, timeline, title, compare, steps) con el proyecto Remotion de
config.json -> remotion.dir, como secuencia PNG con fondo transparente. El motor pone cada
fotograma sobre su propio fondo y encima sus capas de siempre (subtítulos, sello, fuente).

Si Remotion está desactivado, no está instalado o falla, no pasa nada: el motor usa sus
tarjetas Pillow de siempre y el vídeo se genera igual.
"""
from __future__ import annotations

import json
import math
import shutil
import subprocess
from pathlib import Path

from PIL import Image

from common import FPS, H, W

CARD_KINDS = ("stat", "timeline", "title", "compare", "steps", "skull")
FIELDS = {
    "skull": ("entry", "exit", "region", "note"),
    "stat": ("value", "prefix", "suffix", "label", "thousands", "count"),
    "timeline": ("points", "active"),
    "title": ("text",),
    "compare": ("title", "items", "highlight"),
    "steps": ("title", "items"),
}
TAIL = 0.35  # el fundido al plano siguiente (0,12 s; 0,32 s en estilo documental) sigue mostrando la tarjeta


def frames_needed(seg) -> int:
    return math.ceil((seg.v_end - seg.v_start + TAIL) * FPS) + 1


def _cli(proj: Path) -> Path | None:
    """Ejecutable local de Remotion (nunca npx: podría intentar descargar y quedarse esperando)."""
    for name in ("remotion.cmd", "remotion"):
        p = proj / "node_modules" / ".bin" / name
        if p.exists():
            return p
    return None


def _png_ok(p: Path) -> bool:
    try:
        with Image.open(p) as im:
            im.verify()
        with Image.open(p) as im:
            return im.size == (W, H)
    except Exception:  # noqa: BLE001
        return False


def attach(segs: list, cfg: dict, work_dir: Path, log=print) -> bool:
    """Asigna seg.remo_frames (lista de PNG) a cada tarjeta. Devuelve True si se usó Remotion."""
    rc = cfg.get("remotion") or {}
    if not rc.get("enabled"):
        return False
    cards = [(i, s) for i, s in enumerate(segs) if s.kind in CARD_KINDS]
    if not cards:
        return False
    proj = Path(rc.get("dir", ""))
    cli = _cli(proj)
    if not (proj / "src" / "index.ts").exists() or not cli:
        log("  Remotion no disponible: se usan las tarjetas Pillow")
        return False
    reel, offsets, total = [], [], 0
    for i, s in cards:
        n = frames_needed(s)
        item = {"kind": s.kind, "frames": n}
        item.update({k: s.visual[k] for k in FIELDS[s.kind] if k in s.visual})
        reel.append(item)
        offsets.append((i, total, n))
        total += n
    out = work_dir / "frames"
    out.mkdir(parents=True, exist_ok=True)
    props = work_dir / "props.json"
    # El tamaño se lee en tiempo de ejecución: build.py lo cambia para el formato largo (1920x1080)
    props.write_text(json.dumps({"cards": reel, "width": W, "height": H}, ensure_ascii=False), encoding="utf-8")
    cmd = [str(cli), "render", "src/index.ts", "CardsReel", str(out),
           "--sequence", "--image-format=png", f"--props={props}", "--log=error"]

    def fail(msg: str) -> bool:
        shutil.rmtree(out, ignore_errors=True)  # no dejar PNG parciales durante el render
        log(f"  Remotion falló ({msg}): se usan las tarjetas Pillow")
        return False

    try:
        proc = subprocess.Popen(cmd, cwd=proj, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, encoding="utf-8", errors="replace")
    except Exception as e:  # noqa: BLE001
        return fail(f"{type(e).__name__}: {str(e)[:200]}")
    try:
        sout, serr = proc.communicate(timeout=int(rc.get("timeout", 900)))
    except subprocess.TimeoutExpired:
        # remotion.cmd lanza node y Chrome: en Windows hay que cerrar todo el árbol de procesos
        try:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True, timeout=30)
        except Exception:  # noqa: BLE001
            pass
        try:
            proc.communicate(timeout=30)
        except Exception:  # noqa: BLE001
            proc.kill()
        return fail("tiempo agotado")
    frames = sorted(out.glob("*.png"))
    if proc.returncode != 0 or len(frames) != total:
        return fail(f"código {proc.returncode}, {len(frames)}/{total} fotogramas: {(serr or sout)[-300:]}")
    if not (_png_ok(frames[0]) and _png_ok(frames[-1])):
        return fail("fotogramas con tamaño o formato inesperado")
    for i, start, n in offsets:
        segs[i].remo_frames = frames[start:start + n]
    log(f"  Tarjetas animadas con Remotion: {len(cards)} ({total} fotogramas)")
    return True
