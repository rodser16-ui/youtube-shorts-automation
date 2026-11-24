"""Configura la identidad del canal por la API oficial (una vez):
descripción, palabras clave, país, idioma, banner y marca de agua.

    python publisher/channel_setup.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import queue_manager as qm  # noqa: E402

ROOT = qm.ROOT
DESCRIPTION = """Historias reales de ciencia, espacio e historia… y la prueba de que pasaron.

Epidemias de baile, explosiones sin cráter, señales del espacio, médicos a los que nadie creyó: en cada Short te contamos una historia sorprendente y te enseñamos la fuente — el documento, la foto o el estudio científico. Cada dato, con su fuente (la tienes siempre en la descripción).

🔎 Series: MISTERIO · HISTORIA · ESPACIO · CIENCIA
📅 Nuevos Shorts cada día.

Narración con voz sintética; guiones investigados y verificados con fuentes. Imágenes de archivo de dominio público o con licencia libre; gráficos y música originales."""
KEYWORDS = ('ciencia historia espacio astronomía "curiosidades científicas" "misterios de la historia" '
            '"datos curiosos" "divulgación científica" NASA "historia de la medicina" arqueología '
            '"shorts de ciencia" "Ciencia con Pruebas"')


def main():
    from googleapiclient.http import MediaFileUpload
    yt = qm.youtube()
    ch = yt.channels().list(part="snippet,brandingSettings", mine=True).execute()["items"][0]
    cid = ch["id"]
    print(f"Canal: {ch['snippet']['title']} ({cid})")
    # Banner
    media = MediaFileUpload(str(ROOT / "brand" / "banner_2560x1440.png"), mimetype="image/png")
    banner_url = yt.channelBanners().insert(media_body=media).execute()["url"]
    branding = ch.get("brandingSettings", {})
    branding.setdefault("channel", {})
    branding["channel"].update({"description": DESCRIPTION, "keywords": KEYWORDS,
                                "country": "ES", "defaultLanguage": "es"})
    branding["image"] = {"bannerExternalUrl": banner_url}
    yt.channels().update(part="brandingSettings", body={"id": cid, "brandingSettings": branding}).execute()
    print("Descripción, palabras clave, país, idioma y banner actualizados")
    # Marca de agua (aparece en los vídeos; en Shorts YouTube puede no mostrarla)
    try:
        yt.watermarks().set(channelId=cid, body={"timing": {"type": "offsetFromEnd", "offsetMs": 15000,
                                                           "durationMs": 15000},
                                                "position": {"type": "corner", "cornerPosition": "topRight"}},
                            media_body=MediaFileUpload(str(ROOT / "brand" / "watermark_150.png"),
                                                       mimetype="image/png")).execute()
        print("Marca de agua configurada")
    except Exception as e:  # noqa: BLE001
        print(f"Aviso marca de agua: {e}")


if __name__ == "__main__":
    main()
