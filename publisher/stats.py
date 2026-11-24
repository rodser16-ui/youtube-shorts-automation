"""Estadísticas de rendimiento (YouTube Data API + YouTube Analytics API).

    python publisher/stats.py            # descarga métricas y escribe reports/informe-AAAA-MM-DD.md

Métricas por vídeo: visualizaciones, % medio visto, segundos medios vistos,
suscriptores ganados, me gusta y comentarios. El dato "Siguieron viendo vs.
deslizaron" de YouTube Studio NO está disponible en la API pública: hay que
consultarlo en Studio > Contenido > Shorts (ver README).
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import queue_manager as qm  # noqa: E402

ROOT = qm.DATA  # datos del canal activo (ver SHORTS_CHANNEL)
REPORTS = ROOT / "reports"


def main():
    con = qm.db()
    rows = con.execute("SELECT * FROM videos WHERE youtube_id IS NOT NULL").fetchall()
    if not rows:
        print("Aún no hay vídeos subidos.")
        return
    from googleapiclient.discovery import build
    creds = qm.credentials()
    yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
    ya = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
    by_id = {r["youtube_id"]: r for r in rows}
    ids = list(by_id)
    basic = {}
    for i in range(0, len(ids), 50):
        res = yt.videos().list(part="statistics,snippet,status", id=",".join(ids[i:i + 50])).execute()
        for it in res.get("items", []):
            s = it["statistics"]
            basic[it["id"]] = {"views": int(s.get("viewCount", 0)), "likes": int(s.get("likeCount", 0)),
                               "comments": int(s.get("commentCount", 0)),
                               "public": it["status"]["privacyStatus"] == "public",
                               "published": it["snippet"]["publishedAt"]}
    public = [v for v in ids if basic.get(v, {}).get("public")]
    an = {}
    try:
        start = (date.today() - timedelta(days=365)).isoformat()
        rep = ya.reports().query(ids="channel==MINE", startDate=start, endDate=date.today().isoformat(),
                                 dimensions="video",
                                 metrics="views,averageViewDuration,averageViewPercentage,subscribersGained,engagedViews",
                                 filters="video==" + ",".join(public[:200]), maxResults=200,
                                 sort="-views").execute()
        for row in rep.get("rows", []):
            an[row[0]] = {"an_views": row[1], "avg_view_sec": row[2], "avg_view_pct": row[3],
                          "subs_gained": row[4], "engaged": row[5]}
    except Exception as e:  # la API de Analytics tarda 24-48 h en tener datos
        print(f"Aviso Analytics: {e}")
    now = qm.now_iso()
    for vid in ids:
        b, x = basic.get(vid, {}), an.get(vid, {})
        con.execute("INSERT OR REPLACE INTO stats VALUES(?,?,?,?,?,?,?,?)",
                    (vid, now, b.get("views"), b.get("likes"), b.get("comments"),
                     x.get("avg_view_pct"), x.get("avg_view_sec"), x.get("subs_gained")))
    con.commit()
    # Informe
    series = defaultdict(list)
    variants = defaultdict(list)  # experimentos: (exp, variante) -> [(vistas, s vistos, % visto, engaged/vistas)]
    lines = [f"# Informe de rendimiento — {date.today().isoformat()}", "",
             "Vistas = Data API (al día). s/% vistos, «engaged» y subs = Analytics (24-72 h de retraso).", "",
             "| ID | Grupo | Título | Vistas | s vistos | % visto | Engaged/vistas | Subs | Likes |",
             "|---|---|---|---|---|---|---|---|---|"]
    for vid in sorted(public, key=lambda v: by_id[v]["id"]):  # las medias, solo con vídeos ya públicos
        r, b, x = by_id[vid], basic.get(vid, {}), an.get(vid, {})
        script = next((ROOT / "content" / "scripts").glob(f"{r['id']}-*.json"), None)
        sj = json.loads(script.read_text(encoding="utf-8")) if script else {}
        ser = sj.get("series", "?")
        grp = f"{sj['experiment']}-{sj['variant']}" if sj.get("experiment") and sj.get("variant") else "-"
        series[ser].append(b.get("views", 0))
        eng = (x["engaged"] / x["an_views"]) if x.get("an_views") else None
        if grp != "-":
            variants[grp].append((b.get("views", 0), x.get("avg_view_sec"), x.get("avg_view_pct"), eng))
        n_an = x.get("an_views") or 0
        if n_an < 50:  # con tan pocas visualizaciones procesadas, la retención no significa nada
            x = {**x, "avg_view_sec": None, "avg_view_pct": None}
            eng = None
            if grp != "-":
                variants[grp][-1] = (b.get("views", 0), None, None, None)
        lines.append(f"| {r['id']} | {grp} | {r['title'][:45]} | {b.get('views', '-')} | "
                     f"{x.get('avg_view_sec') or f'pendiente (n={n_an})'} | {x.get('avg_view_pct') or '-'} | "
                     f"{f'{eng:.0%}' if eng is not None else '-'} | "
                     f"{x.get('subs_gained', '-')} | {b.get('likes', '-')} |")
    lines += ["", "## Vistas medias por serie", ""]
    for ser, v in sorted(series.items(), key=lambda kv: -sum(kv[1]) / len(kv[1])):
        lines.append(f"- **{ser}**: {sum(v) / len(v):.0f} vistas de media ({len(v)} vídeos)")
    if variants:
        from statistics import median
        lines += ["", "## Experimentos (medianas por grupo)", "",
                  "| Grupo | Vídeos | Vistas | s vistos | % visto | Engaged/vistas |", "|---|---|---|---|---|---|"]
        for g, rows_ in sorted(variants.items()):
            def med(i, fmt):
                vals = [t[i] for t in rows_ if t[i] is not None]
                return fmt(median(vals)) if vals else "-"
            lines.append(f"| {g} | {len(rows_)} | {med(0, lambda v: f'{v:.0f}')} | {med(1, lambda v: f'{v:.1f}')} | "
                         f"{med(2, lambda v: f'{v:.1f}')} | {med(3, lambda v: f'{v:.0%}')} |")
        lines += ["", "> Con 5 vídeos por grupo las diferencias son orientativas, no concluyentes."]
    # Rendimiento por franja horaria (hora de publicación en Madrid)
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(qm.cfg()["publishing"]["timezone"])
    slots = defaultdict(list)
    for vid in public:
        r = by_id[vid]
        if r["publish_at"]:
            hh = datetime.fromisoformat(r["publish_at"]).astimezone(tz).strftime("%H:%M")
            slots[hh].append(basic.get(vid, {}).get("views", 0))
    lines += ["", "## Vistas medias por franja (Madrid)", ""]
    for hh, v in sorted(slots.items(), key=lambda kv: -sum(kv[1]) / len(kv[1])):
        lines.append(f"- **{hh}**: {sum(v) / len(v):.0f} vistas de media ({len(v)} vídeos)")
    lines += ["", f"Vídeos públicos: {len(public)} · programados aún sin publicar: {len(ids) - len(public)}",
              "", "> Recuerda revisar en YouTube Studio el % de \"Siguieron viendo\" (no disponible en la API)."]
    REPORTS.mkdir(exist_ok=True)
    out = REPORTS / f"informe-{date.today().isoformat()}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Informe: {out}")


if __name__ == "__main__":
    main()
