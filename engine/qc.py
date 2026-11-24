"""Control de calidad automático antes de publicar.

    python engine/qc.py "output/NNN-*"                  # una o varias carpetas de vídeo
    python engine/qc.py "staging/experimento-01/*" --report staging/experimento-01/QC.md

Comprueba en cada vídeo: resolución, fps y duración; fotogramas negros; silencios largos;
sonoridad (LUFS) y pico real; subtítulos (orden, huecos, que no pasen del final);
licencias de las imágenes; metadatos; y parecido con los demás vídeos del canal
(miniatura y título). Devuelve código 1 si algún vídeo no pasa.
"""
from __future__ import annotations

import argparse
import difflib
import glob
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA as ROOT, FFMPEG, load_config  # noqa: E402

OK, WARN, FAIL = "✅", "⚠️", "❌"
BAD_LICENSE = re.compile(r"\bSA\b|share.?alike|GFDL|GNU Free|non.?commercial|\bNC\b|\bND\b|fair use|all rights", re.I)


def ff(args: list[str]) -> str:
    r = subprocess.run([FFMPEG, "-hide_banner", "-nostats", *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.stderr


def probe(video: Path) -> dict:
    err = ff(["-i", str(video)])
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    dur = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 0.0
    v = re.search(r"Video: (\w+).*?, (\d{3,5})x(\d{3,5}).*?, ([\d.]+) fps", err)
    a = re.search(r"Audio: (\w+)[^,\n]*, (\d+) Hz", err)
    return {"dur": dur, "vcodec": v[1] if v else "?", "w": int(v[2]) if v else 0, "h": int(v[3]) if v else 0,
            "fps": float(v[4]) if v else 0.0, "acodec": a[1] if a else "?", "sr": int(a[2]) if a else 0}


def dhash(p: Path) -> int:
    px = np.asarray(Image.open(p).convert("L").resize((9, 16)), dtype=np.int16)
    bits = (px[:, :-1] > px[:, 1:]).flatten()
    return sum(1 << i for i, b in enumerate(bits) if b)


def check(folder: Path, others: list[Path]) -> list[tuple[str, str, str]]:
    res = []
    add = lambda st, name, det: res.append((st, name, det))  # noqa: E731
    video = folder / "video.mp4"
    meta = json.loads((folder / "meta.json").read_text(encoding="utf-8")) if (folder / "meta.json").exists() else {}
    if not video.exists() or not meta:
        add(FAIL, "Archivos", "falta video.mp4 o meta.json")
        return res
    # Formato
    p = probe(video)
    want = (1920, 1080) if meta.get("format") == "long" else (1080, 1920)
    fmt_ok = (p["w"], p["h"]) == want and abs(p["fps"] - 30) < 0.01 and p["vcodec"] == "h264" and p["acodec"] == "aac"
    add(OK if fmt_ok else FAIL, "Formato", f"{p['w']}×{p['h']} {p['fps']:g} fps {p['vcodec']}/{p['acodec']} {p['sr']} Hz")
    lo, hi = meta.get("target_seconds") or ((480, 720) if meta.get("format") == "long" else (30, 60))
    add(OK if lo - 1 <= p["dur"] <= hi + 1 else WARN, "Duración", f"{p['dur']:.1f} s (objetivo {lo}-{hi} s)")
    # Negros
    blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", ff(["-i", str(video), "-vf", "blackdetect=d=0.3:pix_th=0.10", "-an", "-f", "null", "-"]))
    add(OK if not blacks else FAIL, "Fotogramas negros", "ninguno" if not blacks else ", ".join(f"{a}-{b}s" for a, b in blacks))
    # Silencios (se tolera el final)
    sil = re.findall(r"silence_start: ([\d.]+)", ff(["-i", str(video), "-af", "silencedetect=n=-45dB:d=0.8", "-vn", "-f", "null", "-"]))
    sil = [float(s) for s in sil if float(s) < p["dur"] - 1.2]
    add(OK if not sil else WARN, "Silencios > 0,8 s", "ninguno" if not sil else ", ".join(f"{s:.1f}s" for s in sil))
    # Sonoridad
    eb = ff(["-i", str(video), "-af", "ebur128=peak=true", "-f", "null", "-"])
    i_m = re.findall(r"I:\s+(-?[\d.]+) LUFS", eb)
    tp_m = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", eb)
    lufs = float(i_m[-1]) if i_m else 0.0
    tp = float(tp_m[-1]) if tp_m else 0.0
    add(OK if -15.5 <= lufs <= -12.5 and tp <= -1.0 else WARN, "Sonoridad", f"{lufs:.1f} LUFS, pico real {tp:.1f} dBTP (objetivo −14 / ≤ −1)")
    # Subtítulos
    cap_p = folder / "captions.json"
    if cap_p.exists():
        caps = json.loads(cap_p.read_text(encoding="utf-8"))
        probs = []
        for a, b in zip(caps, caps[1:]):
            if b["start"] < a["start"]:
                probs.append(f"desorden en {b['start']}s")
            if b["start"] - a["end"] > 1.5:
                probs.append(f"hueco {a['end']:.1f}-{b['start']:.1f}s")
        if caps and caps[-1]["end"] > p["dur"] + 0.1:
            probs.append("el último subtítulo pasa del final")
        if caps and caps[0]["start"] > 1.0:
            probs.append(f"primer subtítulo tarde ({caps[0]['start']}s)")
        add(OK if caps and not probs else FAIL, "Subtítulos", f"{len(caps)} bloques" + (": " + "; ".join(probs[:4]) if probs else ", en orden y sin huecos"))
    else:
        add(WARN, "Subtítulos", "sin captions.json (vídeo hecho con una versión anterior del motor)")
    # Licencias
    cred_p = folder / "credits.json"
    creds = json.loads(cred_p.read_text(encoding="utf-8")) if cred_p.exists() else []
    bad = [c for c in creds if BAD_LICENSE.search(c.get("license", ""))]
    missing_attr = [c for c in creds if c.get("attribution_required") and c.get("page", "") not in meta.get("description", "")]
    add(OK if creds and not bad and not missing_attr else FAIL, "Licencias",
        f"{len(creds)} imágenes" + (f"; no válidas: {[c['title'] for c in bad]}" if bad else "")
        + (f"; sin atribución: {[c['title'] for c in missing_attr]}" if missing_attr else "; todas con licencia válida y atribuidas"))
    # Metadatos
    desc = meta.get("description", "")
    mprob = []
    if not 10 <= len(meta.get("title", "")) <= 100:
        mprob.append("título fuera de 10-100 caracteres")
    if load_config()["strings"]["sources_heading"].strip(":") .split()[-1] not in desc:
        mprob.append("descripción sin fuentes")
    if load_config()["strings"]["synthetic_marker"] not in desc:
        mprob.append("sin aviso de voz sintética")
    add(OK if not mprob else FAIL, "Metadatos", "; ".join(mprob) or "título, fuentes y aviso correctos")
    # Parecido con otros vídeos
    sims = []
    thumb = folder / "thumb.jpg"
    if thumb.exists():
        h = dhash(thumb)
        for o in others:
            if o.resolve() == folder.resolve() or not (o / "thumb.jpg").exists():
                continue
            d = bin(h ^ dhash(o / "thumb.jpg")).count("1")
            if d <= 12:
                sims.append(f"miniatura casi igual a {o.name} ({d}/128)")
        for o in others:
            if o.resolve() == folder.resolve() or not (o / "meta.json").exists():
                continue
            t2 = json.loads((o / "meta.json").read_text(encoding="utf-8")).get("title", "")
            r = difflib.SequenceMatcher(None, meta.get("title", "").lower(), t2.lower()).ratio()
            if r >= 0.6:
                sims.append(f"título parecido a {o.name} ({r:.0%})")
    add(OK if not sims else WARN, "Parecido con otros vídeos", "; ".join(sims) or "ninguno")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folders", nargs="+")
    ap.add_argument("--report", help="escribe un informe Markdown")
    a = ap.parse_args()
    folders = sorted({Path(p) for pat in a.folders for p in (glob.glob(pat) or [pat]) if Path(p).is_dir()})
    others = sorted({Path(p) for p in glob.glob(str(ROOT / "output" / "*"))} | set(folders))
    lines, failed = ["# Control de calidad", ""], 0
    for f in folders:
        res = check(f, others)
        bad = any(s == FAIL for s, _, _ in res)
        failed += bad
        head = f"## {f.name} — {'NO APTO' if bad else 'APTO'}"
        print(head)
        lines += [head, "", "| | Prueba | Resultado |", "|---|---|---|"]
        for s, n, d in res:
            print(f"  {s} {n}: {d}")
            lines.append(f"| {s} | {n} | {d} |")
        lines.append("")
    if a.report:
        Path(a.report).write_text("\n".join(lines), encoding="utf-8")
        print(f"Informe: {a.report}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
