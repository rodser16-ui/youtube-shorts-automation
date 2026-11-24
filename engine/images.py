"""Descarga de imágenes con licencia verificada (dominio público / CC0).

Fuentes soportadas (todas sin clave de API):
  - commons: Wikimedia Commons (solo licencias en ALLOWED_LICENSES)
  - nasa:    NASA Image and Video Library (material de la NASA, por lo general
             sin copyright; se descartan imágenes con autor externo indicado)
  - artic:   Art Institute of Chicago (solo is_public_domain = true, CC0)
Cada descarga guarda un JSON con autor, licencia y URL para los créditos.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

import requests

UA = {"User-Agent": "CienciaConPruebasStudio/0.1 (personal video tool; python-requests)"}
ALLOWED_LICENSES = ("public domain", "pd", "cc0", "cc-zero", "no restrictions")
# CC BY (sin SA) se admite con atribución obligatoria en la descripción.
ATTRIBUTION_LICENSES = ("cc by 4.0", "cc by 3.0", "cc by 2.0", "cc by 2.5")


def _strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s or "").strip()


_last_call = [0.0]


def _get(url: str, **kw) -> requests.Response:
    for i in range(5):
        wait = 1.2 - (time.time() - _last_call[0])  # respetar a los servidores
        if wait > 0:
            time.sleep(wait)
        _last_call[0] = time.time()
        r = requests.get(url, headers=UA, timeout=60, **kw)
        if r.status_code == 429 or r.status_code >= 500:
            ra = r.headers.get("Retry-After", "")
            # nunca esperar más de 2 minutos por intento (un Retry-After enorme dejaba el render parado)
            time.sleep(min(120, int(ra)) if ra.isdigit() else 15 + 20 * i)
            continue
        r.raise_for_status()
        return r
    r.raise_for_status()
    return r


def _license_ok(lic: str) -> tuple[bool, bool]:
    """(permitida, requiere_atribución)"""
    l = (lic or "").lower().strip()
    if any(l.startswith(a) or a == l for a in ALLOWED_LICENSES) or l.startswith("pd-"):
        return True, False
    if "sa" not in l.split() and any(l.startswith(a) for a in ATTRIBUTION_LICENSES):
        return True, True
    return False, False


def _commons_info(titles: str) -> list[dict]:
    r = _get("https://commons.wikimedia.org/w/api.php", params={
        "action": "query", "format": "json", "titles": titles, "prop": "imageinfo",
        "iiprop": "url|extmetadata|size|mime", "iiurlwidth": 2400}).json()
    return list(r.get("query", {}).get("pages", {}).values())


def _commons_search(query: str, n: int = 12) -> list[dict]:
    r = _get("https://commons.wikimedia.org/w/api.php", params={
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": f"{query} filetype:bitmap", "gsrnamespace": 6, "gsrlimit": n,
        "prop": "imageinfo", "iiprop": "url|extmetadata|size|mime",
        "iiurlwidth": 2400}).json()
    pages = list(r.get("query", {}).get("pages", {}).values())
    pages.sort(key=lambda p: p.get("index", 0))
    return pages


def _commons_pick(pages: list[dict], min_px: int) -> dict | None:
    for p in pages:
        if "imageinfo" not in p:
            continue
        ii = p["imageinfo"][0]
        if ii.get("mime") not in ("image/jpeg", "image/png", "image/tiff", "image/webp"):
            continue
        if max(ii["width"], ii["height"]) < min_px:
            continue
        m = ii.get("extmetadata", {})
        lic = m.get("LicenseShortName", {}).get("value", "")
        ok, attrib = _license_ok(lic)
        if not ok:
            continue
        # Special:FilePath con ancho -> servidor de miniaturas (upload.wikimedia.org
        # limita mucho las descargas automatizadas de originales).
        name = p["title"].split(":", 1)[1].replace(" ", "_")
        # Tamaño ESTÁNDAR de miniatura (https://w.wiki/GHai) menor que el original: con tamaños no estándar
        # Wikimedia redirige al archivo original («thumbnail_unscaled»), que limita mucho las descargas.
        std = [s for s in (1920, 1280, 960, 500, 330, 250) if s < ii["width"]]
        width = std[0] if std else ii["width"] - 1
        url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{requests.utils.quote(name)}?width={width}"
        return {"url": url, "page": ii["descriptionurl"],
                "title": p["title"], "license": lic, "attribution_required": attrib,
                "author": _strip_html(m.get("Artist", {}).get("value", ""))[:200] or "Desconocido",
                "source": "Wikimedia Commons"}
    return None


def _nasa(spec: dict) -> dict | None:
    if "nasa_id" in spec:
        items = _get("https://images-api.nasa.gov/search",
                     params={"nasa_id": spec["nasa_id"]}).json()["collection"]["items"]
    else:
        items = _get("https://images-api.nasa.gov/search",
                     params={"q": spec["query"], "media_type": "image"}).json()["collection"]["items"]
    for it in items[:15]:
        d = it["data"][0]
        sec = (d.get("secondary_creator") or "") + (d.get("photographer") or "")
        if sec and "nasa" not in sec.lower() and "jpl" not in sec.lower():
            continue  # posible autor externo con derechos: descartar
        nid = d["nasa_id"]
        assets = _get(f"https://images-api.nasa.gov/asset/{nid}").json()["collection"]["items"]
        hrefs = [a["href"] for a in assets if a["href"].lower().endswith((".jpg", ".png"))]
        pick = next((h for h in hrefs if "~large" in h), None) or \
            next((h for h in hrefs if "~orig" in h), None) or (hrefs[0] if hrefs else None)
        if not pick:
            continue
        return {"url": pick.replace("http://", "https://"),
                "page": f"https://images.nasa.gov/details/{nid}", "title": d.get("title", nid),
                "license": "NASA (sin copyright, uso según NASA Media Guidelines)",
                "attribution_required": True, "author": d.get("center", "NASA"),
                "source": "NASA Image and Video Library"}
    return None


def _artic(spec: dict) -> dict | None:
    if "id" in spec:
        data = [_get(f"https://api.artic.edu/api/v1/artworks/{spec['id']}",
                     params={"fields": "id,title,image_id,is_public_domain,artist_display"}).json()["data"]]
    else:
        data = _get("https://api.artic.edu/api/v1/artworks/search", params={
            "q": spec["query"], "limit": 15,
            "fields": "id,title,image_id,is_public_domain,artist_display"}).json()["data"]
    for d in data:
        if d.get("is_public_domain") and d.get("image_id"):
            return {"url": f"https://www.artic.edu/iiif/2/{d['image_id']}/full/1686,/0/default.jpg",
                    "page": f"https://www.artic.edu/artworks/{d['id']}", "title": d["title"],
                    "license": "CC0 (Art Institute of Chicago)", "attribution_required": False,
                    "author": (d.get("artist_display") or "").split("\n")[0],
                    "source": "Art Institute of Chicago"}
    return None


def fetch(spec: dict, cache_dir: Path, min_px: int = 1000) -> tuple[Path, dict]:
    """Devuelve (ruta_imagen, créditos). Lanza error si no hay imagen válida."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:16]
    meta_p = cache_dir / f"{key}.json"
    if meta_p.exists():
        meta = json.loads(meta_p.read_text(encoding="utf-8"))
        img_p = cache_dir / meta["file"]
        if img_p.exists():
            return img_p, meta
    src = spec.get("source", "commons")
    info = None
    if src == "commons":
        if "file" in spec:
            title = spec["file"] if spec["file"].startswith("File:") else "File:" + spec["file"]
            info = _commons_pick(_commons_info(title), min_px=min(min_px, 500))
        if info is None and "query" in spec:
            info = _commons_pick(_commons_search(spec["query"]), min_px)
    elif src == "nasa":
        info = _nasa(spec)
    elif src == "artic":
        info = _artic(spec)
    if info is None:
        raise RuntimeError(f"Sin imagen con licencia válida para {spec}")
    ext = ".png" if info["url"].lower().split("?")[0].endswith(".png") else ".jpg"
    img_p = cache_dir / f"{key}{ext}"
    img_p.write_bytes(_get(info["url"]).content)
    info["file"] = img_p.name
    meta_p.write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    return img_p, info
