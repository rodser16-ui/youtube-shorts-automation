"""Construye Shorts a partir de guiones JSON.

Uso:
    python engine/build.py content/scripts/001-*.json
    python engine/build.py --all            (solo los que aún no tienen vídeo)
    python engine/build.py --all --force    (rehace todos)
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import images  # noqa: E402
import remotion_cards  # noqa: E402
import render  # noqa: E402
import tts  # noqa: E402
from common import DATA, ROOT, decode_audio, load_config  # noqa: E402

GAP = 0.20  # silencio entre frases (s)


def _rel(p: Path) -> Path:
    try:
        return p.relative_to(DATA)
    except ValueError:  # salida de pruebas fuera del canal
        return p


def build_description(script: dict, credits: list[dict], cfg: dict) -> str:
    parts = [script["description"].strip(), ""]
    if script.get("sources"):
        parts.append(cfg["strings"]["sources_heading"])
        parts += [f"• {s}" for s in script["sources"]]
        parts.append("")
    seen, cred_lines = set(), []
    for c in credits:
        if c["page"] in seen:
            continue
        seen.add(c["page"])
        cred_lines.append(f"• {c['title'].replace('File:', '')} — {c['author']} — {c['license']} — {c['page']}")
    if cred_lines:
        parts.append(cfg["strings"]["images_heading"])
        parts += cred_lines
        parts.append("")
    parts.append(cfg["channel"]["disclosure"])
    parts.append("")
    parts.append(" ".join(script.get("hashtags", [])))
    desc = "\n".join(parts)
    return desc[:4900]


def build(script_path: Path, force: bool = False, out_root: Path | None = None) -> Path:
    cfg = load_config()
    script = json.loads(script_path.read_text(encoding="utf-8"))
    out_dir = (out_root or DATA / "output") / f"{script['id']}-{script['slug']}"
    mp4 = out_dir / "video.mp4"
    if mp4.exists() and (out_dir / "meta.json").exists() and not force:
        print(f"= {_rel(mp4)} ya existe")
        return mp4
    if not script.get("segments"):
        raise ValueError("El guion no tiene segmentos")
    # Formato: "short" (vertical 1080x1920, por defecto) o "long" (horizontal 1920x1080, documentales)
    fmt = script.get("format", "short")
    size = (1920, 1080) if fmt == "long" else (1080, 1920)
    render.W, render.H = size
    remotion_cards.W, remotion_cards.H = size
    t0 = time.time()
    cache = ROOT / "assets" / "cache"
    voice = script.get("voice", cfg["voice"]["name"])
    rate = script.get("rate", cfg["voice"]["rate"])
    pitch = script.get("pitch", cfg["voice"]["pitch"])
    segs, credits = [], []
    gap = float(script.get("gap", GAP))  # pausa entre frases (los guiones B usan menos)
    cursor = 0.05
    for i, sd in enumerate(script["segments"]):
        # cada frase puede ajustar ritmo y tono (narración más expresiva: gancho más grave, clímax más vivo)
        mp3, words = tts.synth(sd["text"], voice, sd.get("rate", rate), sd.get("pitch", pitch), cache / "tts")
        aud = decode_audio(mp3)
        vis = sd.get("visual", {})
        seg = render.Seg(text=sd["text"], visual=vis, audio=aud, words=words)
        seg.a_start = cursor
        seg.kind = vis.get("kind", "image")
        seg.motion = vis.get("motion", ["zoom_in", "pan_lr", "zoom_out", "pan_rl"][i % 4])
        seg.focus = tuple(vis.get("focus", (0.5, 0.45)))
        # recorta silencio final del TTS usando las marcas de palabra
        if words:
            end = words[-1]["start"] + words[-1]["dur"] + 0.08
            aud = aud[: int(end * 48000)]
            seg.audio = aud
        cursor += len(aud) / 48000 + gap
        segs.append(seg)
    total = cursor - gap + script.get("tail", 0.6)
    for i, seg in enumerate(segs):
        seg.v_start = 0.0 if i == 0 else seg.a_start - 0.10
    for i, seg in enumerate(segs):
        seg.v_end = segs[i + 1].v_start if i + 1 < len(segs) else total
    # Imágenes
    star = None
    last_img = None
    for i, seg in enumerate(segs):
        img_spec = seg.visual.get("image")
        img_path = None
        if img_spec:
            img_path, cred = images.fetch(img_spec, cache / "img")
            credits.append(cred)
            last_img = img_path
        if seg.kind == "image":
            if img_path is None:
                raise RuntimeError(f"Segmento {i} sin imagen")
            if seg.motion == "fit":
                seg.fit_bg, seg.fit_fg = render.prep_fit(img_path)
            else:
                seg.base = render.prep_cover(img_path)
        else:
            src = img_path or (seg.visual.get("bg") == "prev" and last_img)
            if src:
                from PIL import Image, ImageEnhance, ImageFilter, ImageOps
                im = ImageOps.fit(Image.open(src).convert("RGB"), (render.W // 4, render.H // 4))
                im = im.filter(ImageFilter.GaussianBlur(6)).resize((render.W, render.H))
                seg.card_bg = ImageEnhance.Brightness(im).enhance(0.38)
            else:
                if star is None:
                    star = render.starfield(int(script["id"]),
                                            render.hex_rgb(cfg["brand"]["accent"]))
                seg.card_bg = star
    r = render.Renderer(script, cfg, segs, credits)
    audio = render.mix_audio(segs, total, script.get("mood", "misterio"), int(script["id"]),
                             music_level=float(script.get("music_level", 0.16)), style=script.get("style"))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "meta.json").unlink(missing_ok=True)  # meta solo existe si el vídeo está completo
    # Tarjetas animadas con Remotion (opcional; si falla, tarjetas Pillow). Los PNG son temporales.
    with tempfile.TemporaryDirectory(prefix="remotion-") as td:
        if script.get("remotion", True):  # "remotion": false = tarjetas Pillow (p. ej. grupo de control A)
            remotion_cards.attach(segs, cfg, Path(td))
        r.render(mp4, audio, total)
        # Miniatura (fotograma con gancho, sin subtítulos)
        r.frame_at(0.7, with_captions=False).save(out_dir / "thumb.jpg", quality=92)
    meta = {
        "id": script["id"], "slug": script["slug"], "title": script["title"][:100],
        "description": build_description(script, credits, cfg),
        "tags": script.get("tags", [])[:15], "categoryId": cfg["channel"]["categoryId"],
        "defaultLanguage": cfg["channel"]["language"], "containsSyntheticMedia": False,
        "selfDeclaredMadeForKids": False, "duration": round(total, 2),
    }
    meta["format"] = fmt
    for k in ("experiment", "variant", "style", "target_seconds"):  # para analizar experimentos después
        if script.get(k):
            meta[k] = script[k]
    # Subtítulos: tiempos de cada bloque (para el control de calidad) y .srt reutilizable
    caps = [{"start": round(c[0], 3), "end": round(c[1], 3), "text": " ".join(c[2])} for c in r.chunks]
    (out_dir / "captions.json").write_text(json.dumps(caps, ensure_ascii=False, indent=0), encoding="utf-8")

    def ts(x: float) -> str:
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    srt = "\n".join(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{c['text']}\n" for i, c in enumerate(caps, 1))
    (out_dir / "captions.srt").write_text(srt, encoding="utf-8")
    (out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "credits.json").write_text(json.dumps(credits, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ {_rel(mp4)}  {total:.1f}s  ({time.time() - t0:.0f}s de render)")
    return mp4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scripts", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--out", help="carpeta de salida para PRUEBAS (por defecto output/, la que lee la cola)")
    a = ap.parse_args()
    out_root = Path(a.out).resolve() if a.out else None
    paths = sorted(glob.glob(str(DATA / "content" / "scripts" / "*.json"))) if a.all else []
    for p in a.scripts:
        paths += glob.glob(p)
    fails = []
    for p in paths:
        try:
            build(Path(p), force=a.force, out_root=out_root)
        except Exception as e:  # sigue con los demás
            print(f"✗ {p}: {e}")
            fails.append(p)
    if fails:
        sys.exit(1)


if __name__ == "__main__":
    main()
