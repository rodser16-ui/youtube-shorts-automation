"""Genera review/index.html: galería local para revisar y aprobar los Shorts."""
from __future__ import annotations

import html
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA as ROOT  # noqa: E402  (datos del canal activo)


def main():
    status = {}
    db = ROOT / "publisher" / "queue.db"
    if db.exists():
        con = sqlite3.connect(db)
        status = dict(con.execute("SELECT id, status FROM videos").fetchall())
    cards = []
    for meta_p in sorted((ROOT / "output").glob("*/meta.json")):
        m = json.loads(meta_p.read_text(encoding="utf-8"))
        d = meta_p.parent.name
        st = status.get(m["id"], "sin sincronizar")
        desc = html.escape(m["description"]).replace("\n", "<br>")
        cards.append(f"""
<article class="card">
  <video src="../output/{d}/video.mp4" poster="../output/{d}/thumb.jpg" controls preload="none" playsinline></video>
  <div class="body">
    <div class="row"><span class="id">#{m['id']}</span><span class="st st-{st}">{html.escape(st)}</span><span class="dur">{m['duration']:.0f} s</span></div>
    <h2>{html.escape(m['title'])}</h2>
    <details><summary>Descripción, fuentes y créditos</summary><p>{desc}</p>
    <p class="tags">{html.escape(', '.join(m['tags']))}</p></details>
  </div>
</article>""")
    page = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Revisión de Shorts</title>
<style>
:root{{--bg:#0b1020;--card:#151c33;--ink:#e8edf8;--mut:#9aa6c4;--acc:#ffd23f}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,Segoe UI,sans-serif}}
header{{padding:24px 16px;max-width:1300px;margin:auto}} h1{{margin:0 0 6px;font-size:26px}} h1 b{{color:var(--acc)}}
header p{{color:var(--mut);margin:4px 0}} code{{background:#22294a;padding:2px 6px;border-radius:5px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:18px;padding:0 16px 40px;max-width:1300px;margin:auto}}
.card{{background:var(--card);border-radius:14px;overflow:hidden}} video{{width:100%;aspect-ratio:9/16;background:#000;display:block}}
.body{{padding:12px 14px}} .row{{display:flex;gap:8px;align-items:center;font-size:13px}} .id{{font-weight:800;color:var(--acc)}}
.st{{padding:1px 8px;border-radius:99px;background:#2a3355}} .st-approved,.st-scheduled,.st-published{{background:#1f6b45}} .st-rejected,.st-failed{{background:#7a2433}}
.dur{{margin-left:auto;color:var(--mut)}} h2{{font-size:15px;margin:8px 0}} details{{color:var(--mut);font-size:13px}} summary{{cursor:pointer}}
.tags{{font-style:italic}}
</style></head><body>
<header><h1>Ciencia con <b>Pruebas</b> — revisión de Shorts</h1>
<p>Reproduce cada vídeo. Para aprobar: <code>python publisher/queue_manager.py approve 001 002 …</code> (o <code>approve --all</code>). Para descartar: <code>reject 003</code>.</p>
<p>Nada se sube a YouTube sin tu aprobación.</p></header>
<section class="grid">{''.join(cards)}</section></body></html>"""
    out = ROOT / "review" / "index.html"
    out.write_text(page, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
