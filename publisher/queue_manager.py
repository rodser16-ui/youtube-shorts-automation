"""Cola de publicación de Ciencia con Pruebas (SQLite + YouTube Data API v3).

Comandos:
  python publisher/queue_manager.py auth              # autoriza tu cuenta de Google (una vez)
  python publisher/queue_manager.py sync              # añade a la cola los vídeos de output/
  python publisher/queue_manager.py status            # muestra la cola
  python publisher/queue_manager.py approve 001 002   # aprueba vídeos (o --all)
  python publisher/queue_manager.py reject 003        # descarta un vídeo
  python publisher/queue_manager.py schedule          # asigna horas de publicación libres
  python publisher/queue_manager.py upload [--max 4] [--dry-run]
                                                      # sube los aprobados como privados
                                                      # programados (publishAt)
  python publisher/queue_manager.py refresh           # comprueba en YouTube el estado real
  python publisher/queue_manager.py playlists         # crea las listas por serie y añade los vídeos
                                                      # (upload lo hace solo tras cada subida)

Garantías:
  * Solo se sube lo que está en estado 'approved' (aprobación humana) salvo que
    config.json -> publishing.require_approval sea false.
  * Anti-duplicados: huella SHA-256 del archivo + comprobación de títulos ya
    existentes en el canal antes de subir.
  * Reintentos con espera exponencial; tras 3 fallos el vídeo queda en 'failed'.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
# Multicanal (ver engine/common.py): sin SHORTS_CHANNEL todo es Ciencia con Pruebas, como siempre.
CHANNEL = os.environ.get("SHORTS_CHANNEL", "").strip()
DATA = ROOT / "channels" / CHANNEL if CHANNEL else ROOT
PUB = DATA / "publisher"
DB = PUB / "queue.db"
# El cliente OAuth (proyecto de Google Cloud) puede ser común; el TOKEN es siempre propio de cada canal.
CLIENT_SECRET = PUB / "client_secret.json" if (PUB / "client_secret.json").exists() \
    else ROOT / "publisher" / "client_secret.json"
TOKEN = PUB / "token.json"
LOG = PUB / "publish.log"
if CHANNEL and not (DATA / "config.json").exists():
    raise SystemExit(f"Canal desconocido: {CHANNEL}")
PUB.mkdir(parents=True, exist_ok=True)
SCOPES = [
    "https://www.googleapis.com/auth/youtube",  # gestionar el canal (banner, descripción, marca de agua)
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]
MAX_ATTEMPTS = 3


def cfg() -> dict:
    return json.loads((DATA / "config.json").read_text(encoding="utf-8"))


def lang() -> str:
    return cfg()["channel"].get("language", "es")


def check_channel(yt) -> str:
    """Salvaguarda multicanal: el token debe pertenecer al canal de este config.json.
    Si config.json -> channel.youtube_channel_id no coincide, se detiene antes de tocar nada."""
    mine = yt.channels().list(part="id", mine=True).execute().get("items", [])
    got = mine[0]["id"] if mine else None
    want = cfg()["channel"].get("youtube_channel_id")
    if want and got != want:
        sys.exit(f"ALTO: el token autoriza el canal {got}, pero este config.json es del canal {want}. "
                 f"Vuelve a autorizar eligiendo el canal correcto (queue_manager.py auth).")
    return got


def log(msg: str):
    line = f"{datetime.now().isoformat(timespec='seconds')}  {msg}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def db() -> sqlite3.Connection:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS videos(
        id TEXT PRIMARY KEY, slug TEXT, path TEXT, sha256 TEXT UNIQUE, title TEXT,
        status TEXT DEFAULT 'built', publish_at TEXT, youtube_id TEXT,
        attempts INTEGER DEFAULT 0, last_error TEXT,
        created_at TEXT, updated_at TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS stats(
        youtube_id TEXT, fetched_at TEXT, views INTEGER, likes INTEGER, comments INTEGER,
        avg_view_pct REAL, avg_view_sec REAL, subs_gained INTEGER,
        PRIMARY KEY(youtube_id, fetched_at))""")
    return con


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
def cmd_sync(_a):
    con = db()
    n = 0
    for meta_p in sorted((DATA / "output").glob("*/meta.json")):
        meta = json.loads(meta_p.read_text(encoding="utf-8"))
        mp4 = meta_p.parent / "video.mp4"
        if not mp4.exists():
            continue
        digest = sha256(mp4)
        row = con.execute("SELECT * FROM videos WHERE id=?", (meta["id"],)).fetchone()
        if row is None:
            dup = con.execute("SELECT id FROM videos WHERE sha256=?", (digest,)).fetchone()
            if dup:
                log(f"duplicado ignorado: {meta['id']} == {dup['id']}")
                continue
            con.execute("INSERT INTO videos(id,slug,path,sha256,title,created_at,updated_at) "
                        "VALUES(?,?,?,?,?,?,?)",
                        (meta["id"], meta["slug"], str(mp4.relative_to(DATA)), digest,
                         meta["title"], now_iso(), now_iso()))
            n += 1
        elif row["sha256"] != digest and row["status"] in ("built", "approved", "failed"):
            # vídeo re-renderizado antes de subirse: vuelve a requerir aprobación
            con.execute("UPDATE videos SET sha256=?, title=?, status='built', updated_at=? WHERE id=?",
                        (digest, meta["title"], now_iso(), meta["id"]))
            log(f"{meta['id']} re-renderizado -> vuelve a 'built' (requiere aprobación)")
    con.commit()
    print(f"{n} vídeos nuevos en la cola")


def cmd_status(_a):
    con = db()
    rows = con.execute("SELECT * FROM videos ORDER BY id").fetchall()
    tz = ZoneInfo(cfg()["publishing"]["timezone"])
    print(f"{'ID':5} {'ESTADO':10} {'PUBLICACIÓN (Madrid)':22} {'YOUTUBE':13} TÍTULO")
    for r in rows:
        pa = datetime.fromisoformat(r["publish_at"]).astimezone(tz).strftime("%a %d/%m %H:%M") if r["publish_at"] else "-"
        print(f"{r['id']:5} {r['status']:10} {pa:22} {r['youtube_id'] or '-':13} {r['title'][:60]}")


def cmd_approve(a):
    con = db()
    if a.all:
        con.execute("UPDATE videos SET status='approved', updated_at=? WHERE status='built'", (now_iso(),))
    for vid in a.ids:
        con.execute("UPDATE videos SET status='approved', attempts=0, updated_at=? "
                    "WHERE id=? AND status IN ('built','failed')", (now_iso(), vid))
    con.commit()
    cmd_status(a)


def cmd_reject(a):
    con = db()
    for vid in a.ids:
        con.execute("UPDATE videos SET status='rejected', updated_at=? WHERE id=? AND youtube_id IS NULL",
                    (now_iso(), vid))
    con.commit()
    cmd_status(a)


def next_slots(con, count: int) -> list[datetime]:
    p = cfg()["publishing"]
    tz = ZoneInfo(p["timezone"])
    taken = {r["publish_at"] for r in con.execute("SELECT publish_at FROM videos WHERE publish_at IS NOT NULL")}
    # YouTube exige publishAt en el futuro; dejamos margen de 3 h para la subida/procesado
    t = datetime.now(tz) + timedelta(hours=3)
    out = []
    day = t.date()
    while len(out) < count:
        for hhmm in sorted(p["slots"]):  # orden cronológico dentro del día
            h, m = map(int, hhmm.split(":"))
            slot = datetime(day.year, day.month, day.day, h, m, tzinfo=tz)
            naive = slot.replace(tzinfo=None)
            if slot.astimezone(timezone.utc).astimezone(tz).replace(tzinfo=None) != naive:
                continue  # hora inexistente por cambio de horario
            iso = slot.astimezone(timezone.utc).isoformat(timespec="seconds")
            if slot > t and iso not in taken:
                out.append(slot)
                taken.add(iso)
                if len(out) >= count:
                    break
        day += timedelta(days=1)
    return out


def cmd_schedule(_a):
    con = db()
    need_approval = cfg()["publishing"].get("require_approval", True)
    states = ("approved",) if need_approval else ("approved", "built")
    rows = con.execute(f"SELECT id FROM videos WHERE status IN ({','.join('?' * len(states))}) "
                       "AND publish_at IS NULL ORDER BY id", states).fetchall()
    for r, slot in zip(rows, next_slots(con, len(rows))):
        con.execute("UPDATE videos SET publish_at=?, updated_at=? WHERE id=?",
                    (slot.astimezone(timezone.utc).isoformat(timespec="seconds"), now_iso(), r["id"]))
    con.commit()
    cmd_status(_a)


# --------------------------------------------------------------------------- #
def credentials():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    creds = None
    if TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as e:
            log(f"no se pudo refrescar el token ({e}); hay que volver a autorizar")
            creds = None
    if not creds or not creds.valid:
        if not CLIENT_SECRET.exists():
            sys.exit("Falta publisher/client_secret.json (ver README, sección 'Conectar YouTube').")
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
        # Puerto fijo y sin abrir navegador: imprime la URL para abrirla en cualquier navegador
        creds = flow.run_local_server(port=8765, open_browser=False, prompt="consent",
                                      access_type="offline",
                                      authorization_prompt_message="Abre esta URL para autorizar: {url}",
                                      success_message="Autorización completada. Puedes cerrar esta pestaña.")
    TOKEN.write_text(creds.to_json(), encoding="utf-8")
    return creds


def youtube():
    from googleapiclient.discovery import build
    return build("youtube", "v3", credentials=credentials(), cache_discovery=False)


def cmd_auth(_a):
    yt = youtube()
    ch = yt.channels().list(part="snippet,statistics", mine=True).execute()
    if not ch.get("items"):
        sys.exit("La cuenta autorizada no tiene canal de YouTube. Créalo primero en youtube.com.")
    c = ch["items"][0]
    print(f"Conectado al canal: {c['snippet']['title']} ({c['id']}) — "
          f"{c['statistics'].get('subscriberCount', '?')} suscriptores")


def existing_titles(yt) -> set[str]:
    ch = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    titles, token = set(), None
    for _ in range(400):  # toda la lista de subidas (hasta 20.000 vídeos)
        r = yt.playlistItems().list(part="snippet", playlistId=uploads, maxResults=50,
                                    pageToken=token).execute()
        titles |= {i["snippet"]["title"].strip().lower() for i in r.get("items", [])}
        token = r.get("nextPageToken")
        if not token:
            break
    return titles


# Listas de reproducción por serie (ayudan a encadenar vídeos y al SEO).
PLAYLISTS = {
    "MISTERIO": ("Misterios reales, con pruebas",
                 "Misterios que ocurrieron de verdad, contados en menos de un minuto y con las fuentes "
                 "en la descripción: epidemias inexplicables, explosiones sin cráter, señales del espacio..."),
    "HISTORIA": ("Historia real en 1 minuto",
                 "Episodios de la historia que parecen inventados pero están documentados. "
                 "Cada dato, con su fuente."),
    "ESPACIO": ("Espacio y astronomía en 1 minuto",
                "Fotos reales de la NASA, misiones y descubrimientos del universo explicados en Shorts, "
                "con las fuentes en cada vídeo."),
    "CIENCIA": ("Ciencia sorprendente (y comprobada)",
                "Descubrimientos, experimentos y científicos que cambiaron lo que sabemos. "
                "Historias reales con fuentes verificadas."),
}


def series_of(video_id: str) -> str | None:
    script = next((DATA / "content" / "scripts").glob(f"{video_id}-*.json"), None)
    if not script:
        return None
    return json.loads(script.read_text(encoding="utf-8")).get("series")


def _all_pages(call, **kw):
    token = None
    while True:
        r = call(pageToken=token, maxResults=50, **kw).execute()
        yield from r.get("items", [])
        token = r.get("nextPageToken")
        if not token:
            return


def ensure_playlists(yt) -> dict[str, str]:
    """Devuelve {serie: playlist_id}; crea (pública) la lista que falte."""
    existing = {it["snippet"]["title"]: it["id"]
                for it in _all_pages(yt.playlists().list, part="snippet", mine=True)}
    out = {}
    lists = {k: tuple(v) for k, v in cfg().get("playlists", {}).items()} or PLAYLISTS
    for series, (title, desc) in lists.items():
        pid = existing.get(title)
        if not pid:
            pid = yt.playlists().insert(part="snippet,status", body={
                "snippet": {"title": title, "description": desc, "defaultLanguage": lang()},
                "status": {"privacyStatus": "public"}}).execute()["id"]
            log(f"lista creada: {title} ({pid})")
        out[series] = pid
    return out


def sync_playlists(yt) -> int:
    """Añade cada vídeo subido a la lista de su serie (sin duplicar). Devuelve cuántos añadió."""
    con = db()
    rows = con.execute("SELECT id, youtube_id FROM videos WHERE youtube_id IS NOT NULL "
                       "AND status IN ('scheduled', 'published') ORDER BY id").fetchall()
    if not rows:
        return 0
    check_channel(yt)
    pls = ensure_playlists(yt)
    have = {pid: {i["contentDetails"]["videoId"]
                  for i in _all_pages(yt.playlistItems().list, part="contentDetails", playlistId=pid)}
            for pid in set(pls.values())}
    added = 0
    for r in rows:
        series = series_of(r["id"]) or ""
        pid = pls.get(series)
        if not pid or r["youtube_id"] in have[pid]:
            continue
        try:
            yt.playlistItems().insert(part="snippet", body={"snippet": {
                "playlistId": pid, "resourceId": {"kind": "youtube#video", "videoId": r["youtube_id"]}}}).execute()
        except Exception as e:  # noqa: BLE001 — un vídeo con problemas no frena a los demás
            if any(k in str(e) for k in ("quotaExceeded", "invalid_grant", "unauthorized", "forbidden")):
                raise
            log(f"{r['id']}: no se pudo añadir a la lista {series} ({e})")
            continue
        have[pid].add(r["youtube_id"])
        added += 1
        log(f"{r['id']} añadido a la lista {series}")
    return added


def cmd_playlists(_a):
    print(f"{sync_playlists(youtube())} vídeos añadidos a listas")


def upload_one(yt, row, meta: dict) -> str:
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
    body = {
        "snippet": {"title": meta["title"], "description": meta["description"],
                    "tags": meta.get("tags", []), "categoryId": meta.get("categoryId", "28"),
                    "defaultLanguage": lang(), "defaultAudioLanguage": lang()},
        "status": {"privacyStatus": "private", "publishAt": row["publish_at"].replace("+00:00", "Z"),
                   "selfDeclaredMadeForKids": False,
                   "containsSyntheticMedia": bool(meta.get("containsSyntheticMedia", False)),
                   "embeddable": True, "license": "youtube"},
    }
    media = MediaFileUpload(str(DATA / row["path"]), mimetype="video/mp4", chunksize=8 << 20,
                            resumable=True)
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media,
                             notifySubscribers=True)
    resp, retry = None, 0
    while resp is None:
        try:
            _status, resp = req.next_chunk()
        except HttpError as e:
            if e.resp.status in (500, 502, 503, 504) and retry < 6:
                retry += 1
                time.sleep(min(64, 2 ** retry) + random.random())
                continue
            raise
        except (ConnectionError, TimeoutError, OSError):
            if retry < 6:
                retry += 1
                time.sleep(min(64, 2 ** retry) + random.random())
                continue
            raise
    return resp["id"]


def cmd_upload(a):
    con = db()
    need_approval = cfg()["publishing"].get("require_approval", True)
    states = ("approved",) if need_approval else ("approved", "built")
    # Subidas interrumpidas (proceso cerrado a mitad): vuelven a la cola. Si YouTube
    # llegó a aceptar el vídeo, la comprobación de títulos de abajo evita duplicarlo.
    con.execute("UPDATE videos SET status='approved', updated_at=? WHERE status='uploading' "
                "AND youtube_id IS NULL AND updated_at < ?",
                (now_iso(), (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(timespec="seconds")))
    con.commit()
    rows = con.execute(f"SELECT * FROM videos WHERE status IN ({','.join('?' * len(states))}) "
                       "AND publish_at IS NOT NULL AND youtube_id IS NULL AND attempts < ? "
                       "ORDER BY publish_at LIMIT ?", (*states, MAX_ATTEMPTS, a.max)).fetchall()
    if not rows:
        print("Nada que subir (¿aprobaste y programaste?).")
        return
    now = datetime.now(timezone.utc)
    if a.dry_run:
        for r in rows:
            print(f"[dry-run] subiría {r['id']} para {r['publish_at']}: {r['title']}")
        return
    if not cfg()["publishing"].get("active", True):
        sys.exit("Este canal no está activo (config.json -> publishing.active = false): no se sube nada.")
    yt = youtube()
    check_channel(yt)  # nunca subir al canal equivocado
    titles = existing_titles(yt)
    uploaded = 0
    for r in rows:
        meta = json.loads((DATA / Path(r["path"]).parent / "meta.json").read_text(encoding="utf-8"))
        if meta["title"].strip().lower() in titles:
            con.execute("UPDATE videos SET status='duplicate', last_error=?, updated_at=? WHERE id=?",
                        ("Ya existe un vídeo con este título en el canal", now_iso(), r["id"]))
            con.commit()
            log(f"{r['id']} omitido: título ya publicado")
            continue
        if sha256(DATA / r["path"]) != r["sha256"]:
            log(f"{r['id']} omitido: el archivo cambió tras la aprobación (vuelve a aprobarlo)")
            con.execute("UPDATE videos SET status='built', updated_at=? WHERE id=?", (now_iso(), r["id"]))
            con.commit()
            continue
        if datetime.fromisoformat(r["publish_at"]) < now + timedelta(minutes=30):
            nxt = next_slots(con, 1)[0].astimezone(timezone.utc).isoformat(timespec="seconds")
            con.execute("UPDATE videos SET publish_at=? WHERE id=?", (nxt, r["id"]))
            con.commit()
            r = con.execute("SELECT * FROM videos WHERE id=?", (r["id"],)).fetchone()
            log(f"{r['id']} reprogramado a {nxt} (la hora anterior ya había pasado)")
        # Reclamar la fila de forma atómica: si otro proceso ya la tomó, se salta.
        cur = con.execute("UPDATE videos SET status='uploading', attempts=attempts+1, updated_at=? "
                          "WHERE id=? AND status=? AND youtube_id IS NULL",
                          (now_iso(), r["id"], r["status"]))
        con.commit()
        if cur.rowcount != 1:
            log(f"{r['id']} lo está subiendo otro proceso; se omite")
            continue
        try:
            vid = upload_one(yt, r, meta)
            con.execute("UPDATE videos SET status='scheduled', youtube_id=?, last_error=NULL, updated_at=? "
                        "WHERE id=?", (vid, now_iso(), r["id"]))
            log(f"{r['id']} subido -> https://youtu.be/{vid} (publica {r['publish_at']})")
            titles.add(meta["title"].strip().lower())
            uploaded += 1
        except Exception as e:  # noqa: BLE001
            back = r["status"]  # estado al que vuelve para reintentar
            if "quotaExceeded" in str(e) or "uploadLimitExceeded" in str(e):
                # no es culpa del vídeo: no consume intento
                con.execute("UPDATE videos SET status=?, attempts=attempts-1, last_error=?, updated_at=? "
                            "WHERE id=?", (back, str(e)[:500], now_iso(), r["id"]))
                con.commit()
                log("Cuota/límite de YouTube alcanzado: se reintentará en la próxima ejecución")
                break
            st = "failed" if r["attempts"] + 1 >= MAX_ATTEMPTS else back
            con.execute("UPDATE videos SET status=?, last_error=?, updated_at=? WHERE id=?",
                        (st, str(e)[:500], now_iso(), r["id"]))
            log(f"ERROR subiendo {r['id']}: {e}")
        con.commit()
    if uploaded:
        try:
            sync_playlists(yt)
        except Exception as e:  # noqa: BLE001 — las listas nunca deben bloquear las subidas
            log(f"Aviso: no se pudieron actualizar las listas ({e})")


def cmd_refresh(_a):
    con = db()
    rows = con.execute("SELECT * FROM videos WHERE youtube_id IS NOT NULL").fetchall()
    if not rows:
        print("No hay vídeos subidos todavía.")
        return
    yt = youtube()
    ids = [r["youtube_id"] for r in rows]
    for i in range(0, len(ids), 50):
        res = yt.videos().list(part="status,statistics", id=",".join(ids[i:i + 50])).execute()
        found = {it["id"]: it for it in res.get("items", [])}
        for vid in ids[i:i + 50]:
            it = found.get(vid)
            if it is None:
                con.execute("UPDATE videos SET status='missing', updated_at=? WHERE youtube_id=?", (now_iso(), vid))
                continue
            st = it["status"]
            new = "published" if st["privacyStatus"] == "public" else "scheduled"
            if st.get("uploadStatus") in ("rejected", "failed"):
                new = "yt_" + st["uploadStatus"]
            con.execute("UPDATE videos SET status=?, updated_at=? WHERE youtube_id=?", (new, now_iso(), vid))
    con.commit()
    cmd_status(_a)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("auth", "sync", "status", "schedule", "refresh", "playlists"):
        sub.add_parser(name)
    p = sub.add_parser("approve")
    p.add_argument("ids", nargs="*")
    p.add_argument("--all", action="store_true")
    p = sub.add_parser("reject")
    p.add_argument("ids", nargs="+")
    p = sub.add_parser("upload")
    p.add_argument("--max", type=int, default=4)
    p.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    {"auth": cmd_auth, "sync": cmd_sync, "status": cmd_status, "approve": cmd_approve,
     "reject": cmd_reject, "schedule": cmd_schedule, "upload": cmd_upload,
     "refresh": cmd_refresh, "playlists": cmd_playlists}[a.cmd](a)


if __name__ == "__main__":
    main()
