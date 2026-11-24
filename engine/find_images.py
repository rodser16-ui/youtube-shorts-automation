"""Busca candidatas con licencia válida (para escribir guiones).

    python engine/find_images.py "commons:dancing plague 1518" "nasa:pale blue dot"
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import images  # noqa: E402

for q in sys.argv[1:]:
    src, _, query = q.partition(":")
    print(f"\n### {q}")
    try:
        if src == "commons":
            for p in images._commons_search(query, 14):
                if "imageinfo" not in p:
                    continue
                ii = p["imageinfo"][0]
                lic = ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "")
                ok, att = images._license_ok(lic)
                if ok:
                    print(f"  {ii['width']}x{ii['height']}  [{lic}]  {p['title']}")
        elif src == "nasa":
            items = images._get("https://images-api.nasa.gov/search",
                                params={"q": query, "media_type": "image"}).json()["collection"]["items"]
            for it in items[:10]:
                d = it["data"][0]
                print(f"  {d['nasa_id']}  | {d.get('title', '')[:70]} | {d.get('secondary_creator', '')}")
    except Exception as e:
        print("  ERROR", e)
