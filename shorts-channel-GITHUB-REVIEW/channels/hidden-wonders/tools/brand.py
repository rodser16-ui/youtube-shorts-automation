"""Identidad visual de Hidden Wonders (nombre y colores desde config.json del canal).

    python channels/hidden-wonders/tools/brand.py

Genera en channels/hidden-wonders/brand/: emblema, foto de perfil, logo redondo, marca de agua,
banner 2560x1440 (con vista de la zona segura), plantilla de miniatura 1280x720 para vídeos largos
y la hoja de estilo brand_sheet.png. Fuentes: Montserrat y Anton (licencia OFL, en assets/fonts).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

CH = Path(__file__).resolve().parent.parent
ROOT = CH.parent.parent
OUT = CH / "brand"
FONTS = ROOT / "assets" / "fonts"
cfg = json.loads((CH / "config.json").read_text(encoding="utf-8"))
NAME = cfg["channel"]["name"]


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


GOLD, TEAL, INK = hexrgb(cfg["brand"]["accent"]), hexrgb(cfg["brand"]["accent2"]), hexrgb(cfg["brand"]["navy"])
CREAM = (244, 236, 220)


def mont(size, weight="Bold"):
    f = ImageFont.truetype(str(FONTS / "Montserrat-VF.ttf"), size)
    f.set_variation_by_name(weight)
    return f


def anton(size):
    return ImageFont.truetype(str(FONTS / "Anton-Regular.ttf"), size)


def starfield(w, h, seed=7, density=0.00035):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w * 0.5, h * 0.42
    glow = np.exp(-(((xx - cx) / (w * 0.55)) ** 2 + ((yy - cy) / (h * 0.55)) ** 2))
    base = np.zeros((h, w, 3), np.float32)
    for c, k in zip(INK, (1.0, 1.0, 1.0)):
        pass
    base[..., 0] = INK[0] + 30 * glow
    base[..., 1] = INK[1] + 26 * glow
    base[..., 2] = INK[2] + 34 * glow
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    for _ in range(int(w * h * density)):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        r = rng.choice([0.6, 0.9, 1.3, 1.8], p=[0.5, 0.3, 0.15, 0.05])
        a = int(rng.uniform(90, 255))
        col = (255, 245, 220) if rng.random() < 0.8 else TEAL
        d.ellipse((x - r, y - r, x + r, y + r), fill=col + (a,) if img.mode == "RGBA" else col)
    return img


def keyhole_mask(size, scale=1.0):
    """Silueta de cerradura (círculo + trapecio) centrada, como máscara L."""
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    c = size / 2
    r = size * 0.16 * scale
    cy = size * 0.42
    d.ellipse((c - r, cy - r, c + r, cy + r), fill=255)
    top_w, bot_w, h = r * 0.62, r * 1.25, size * 0.30 * scale
    d.polygon([(c - top_w, cy + r * 0.4), (c + top_w, cy + r * 0.4), (c + bot_w, cy + r * 0.4 + h),
               (c - bot_w, cy + r * 0.4 + h)], fill=255)
    return m


def emblem(size=1024):
    """Medallón: anillo dorado, fondo oscuro y una cerradura por la que se ve un cielo estrellado con luz dorada."""
    S = size * 2  # supermuestreo para bordes suaves
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((0, 0, S - 1, S - 1), fill=INK + (255,))
    # anillo exterior doble
    for w, inset, col in ((int(S * 0.028), int(S * 0.035), GOLD), (int(S * 0.008), int(S * 0.085), GOLD)):
        d.ellipse((inset, inset, S - inset, S - inset), outline=col + (255,), width=w)
    # cielo dentro de la cerradura
    sky = starfield(S, S, seed=11, density=0.0009).convert("RGBA")
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    light = np.exp(-(((xx - S / 2) / (S * 0.18)) ** 2 + ((yy - S * 0.47) / (S * 0.26)) ** 2))
    lay = np.zeros((S, S, 4), np.float32)
    lay[..., 0], lay[..., 1], lay[..., 2] = GOLD
    lay[..., 3] = light * 210
    sky = Image.alpha_composite(sky, Image.fromarray(lay.astype(np.uint8), "RGBA"))
    mask = keyhole_mask(S, 1.0)
    im.paste(sky, (0, 0), mask)
    # contorno dorado de la cerradura
    edge = mask.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(9))
    gold = Image.new("RGBA", (S, S), GOLD + (255,))
    im.paste(gold, (0, 0), edge)
    # destello (estrella de 4 puntas) en el ojo de la cerradura
    c, cy = S / 2, S * 0.40
    for ang, L in ((0, S * 0.11), (90, S * 0.11), (45, S * 0.045), (135, S * 0.045)):
        a = math.radians(ang)
        dx, dy = math.cos(a) * L, math.sin(a) * L
        d.line((c - dx, cy - dy, c + dx, cy + dy), fill=(255, 250, 235, 235), width=int(S * 0.006))
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((c - S * 0.03, cy - S * 0.03, c + S * 0.03, cy + S * 0.03), fill=(255, 245, 220, 255))
    im = Image.alpha_composite(im, glow.filter(ImageFilter.GaussianBlur(S * 0.012)))
    return im.resize((size, size), Image.Resampling.LANCZOS)


def wordmark(height=220, color=CREAM, spacing=0.32):
    """Texto en dos niveles: HIDDEN fino y espaciado, WONDERS grueso en dorado."""
    w1, w2 = NAME.upper().split(" ", 1) if " " in NAME else (NAME.upper(), "")
    f1, f2 = mont(int(height * 0.30), "Light"), mont(int(height * 0.56), "Black")
    sp1 = f1.size * spacing

    def spaced_len(txt, f, sp):
        return sum(f.getlength(ch) for ch in txt) + sp * (len(txt) - 1)
    width = int(max(spaced_len(w1, f1, sp1), f2.getlength(w2)) + 20)
    im = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = (width - spaced_len(w1, f1, sp1)) / 2
    for ch in w1:
        d.text((x, 0), ch, font=f1, fill=color)
        x += f1.getlength(ch) + sp1
    d.text(((width - f2.getlength(w2)) / 2, height * 0.30), w2, font=f2, fill=GOLD)
    return im


def main():
    OUT.mkdir(exist_ok=True)
    em = emblem(1024)
    em.save(OUT / "emblem_1024.png")
    # Foto de perfil (800x800, cuadrada; YouTube la recorta en círculo)
    prof = Image.new("RGBA", (800, 800), INK + (255,))
    prof.alpha_composite(em.resize((760, 760), Image.Resampling.LANCZOS), (20, 20))
    prof.convert("RGB").save(OUT / "profile_800.png")
    prof.convert("RGB").resize((240, 240), Image.Resampling.LANCZOS).save(OUT / "profile_240.jpg", quality=92)
    em.resize((256, 256), Image.Resampling.LANCZOS).save(OUT / "logo.png")
    # Marca de agua (150x150, semitransparente)
    wm = em.resize((150, 150), Image.Resampling.LANCZOS)
    wm.putalpha(wm.getchannel("A").point(lambda a: int(a * 0.75)))
    wm.save(OUT / "watermark_150.png")
    # Banner 2560x1440; zona segura para todos los dispositivos: 1546x423 centrada
    bw, bh = 2560, 1440
    ban = starfield(bw, bh, seed=3).convert("RGBA")
    yy, xx = np.mgrid[0:bh, 0:bw].astype(np.float32)
    band = np.exp(-((yy - bh / 2) / 190) ** 2) * np.exp(-((xx - bw / 2) / 900) ** 2)
    lay = np.zeros((bh, bw, 4), np.float32)
    lay[..., :3] = GOLD
    lay[..., 3] = band * 60
    ban = Image.alpha_composite(ban, Image.fromarray(lay.astype(np.uint8), "RGBA"))
    e = em.resize((300, 300), Image.Resampling.LANCZOS)
    wmk = wordmark(260)
    total = e.width + 50 + wmk.width
    x0 = (bw - total) // 2
    ban.alpha_composite(e, (x0, bh // 2 - 150 - 20))
    ban.alpha_composite(wmk, (x0 + e.width + 50, bh // 2 - 130 - 20))
    tag = "MYSTERIES · ENGINEERING · DISCOVERIES — EVERY CLAIM SOURCED"
    ft = mont(30, "SemiBold")
    d = ImageDraw.Draw(ban)
    d.text(((bw - ft.getlength(tag)) / 2, bh // 2 + 130), tag, font=ft, fill=TEAL)
    ban.convert("RGB").save(OUT / "banner_2560x1440.png")
    prev = ban.copy()
    pd = ImageDraw.Draw(prev)
    pd.rectangle(((bw - 1546) // 2, (bh - 423) // 2, (bw + 1546) // 2, (bh + 423) // 2), outline=(255, 60, 60, 255), width=4)
    prev.convert("RGB").resize((1280, 720)).save(OUT / "banner_preview_safe_area.jpg", quality=88)
    # Plantilla de miniatura (vídeos largos) 1280x720: imagen a la izquierda, título a la derecha
    th = starfield(1280, 720, seed=5).convert("RGBA")
    tdraw = ImageDraw.Draw(th)
    tdraw.rectangle((0, 0, 700, 720), fill=(40, 46, 56, 255))
    tdraw.text((350 - mont(30, "SemiBold").getlength("[ archive image ]") / 2, 340), "[ archive image ]",
               font=mont(30, "SemiBold"), fill=(150, 160, 175))
    tdraw.polygon([(640, 0), (760, 0), (700, 720), (580, 720)], fill=INK + (255,))
    for i, (txt, col) in enumerate((("THE TITLE", CREAM), ("IN 2-4 WORDS", GOLD))):
        tdraw.text((735, 250 + i * 110), txt, font=anton(96), fill=col, stroke_width=4, stroke_fill=(0, 0, 0))
    th.alpha_composite(em.resize((110, 110), Image.Resampling.LANCZOS), (1150, 590))
    th.convert("RGB").save(OUT / "thumbnail_template_1280x720.png")
    # Hoja de estilo
    sh = Image.new("RGB", (1600, 1000), INK)
    s = ImageDraw.Draw(sh)
    sh.paste(em.resize((360, 360), Image.Resampling.LANCZOS).convert("RGB"), (60, 60), em.resize((360, 360)).getchannel("A"))
    wm2 = wordmark(200)
    sh.paste(wm2.convert("RGB"), (480, 130), wm2.getchannel("A"))
    s.text((60, 470), "COLORS", font=mont(34, "Bold"), fill=CREAM)
    for i, (nm, col) in enumerate((("Gold  " + cfg["brand"]["accent"], GOLD), ("Teal  " + cfg["brand"]["accent2"], TEAL),
                                    ("Ink  " + cfg["brand"]["navy"], INK), ("Cream  #F4ECDC", CREAM))):
        x = 60 + i * 380
        s.rounded_rectangle((x, 520, x + 340, 640), radius=16, fill=col, outline=(90, 96, 110), width=2)
        s.text((x, 655), nm, font=mont(26, "SemiBold"), fill=CREAM)
    s.text((60, 730), "TYPE", font=mont(34, "Bold"), fill=CREAM)
    s.text((60, 780), "Montserrat Light — narrative labels, spaced", font=mont(34, "Light"), fill=CREAM)
    s.text((60, 830), "MONTSERRAT BLACK — TITLES", font=mont(40, "Black"), fill=GOLD)
    s.text((60, 890), "ANTON — BIG NUMBERS 1,000 KM", font=anton(56), fill=CREAM)
    sh.save(OUT / "brand_sheet.png")
    print("OK ->", OUT)


if __name__ == "__main__":
    main()
