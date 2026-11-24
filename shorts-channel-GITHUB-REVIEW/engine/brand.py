"""Genera la identidad visual: logo (foto de perfil), marca de agua y banner."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, font, hex_rgb, load_config  # noqa: E402

cfg = load_config()
ACC = hex_rgb(cfg["brand"]["accent"])
ACC2 = hex_rgb(cfg["brand"]["accent2"])
NAVY = hex_rgb(cfg["brand"]["navy"])
OUT = ROOT / "brand"


def radial_bg(w, h, cx, cy, inner=(28, 44, 96), outer=NAVY, radius=None):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = radius or max(w, h) * 0.6
    d = np.clip(np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r, 0, 1)[..., None]
    arr = np.array(inner, np.float32) * (1 - d) + np.array(outer, np.float32) * d
    return Image.fromarray(arr.astype(np.uint8))


def stars(img, n, seed, rmax=2.2):
    rng = np.random.default_rng(seed)
    d = ImageDraw.Draw(img)
    w, h = img.size
    for _ in range(n):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        r = rng.uniform(0.6, rmax)
        b = int(rng.uniform(120, 255))
        d.ellipse((x - r, y - r, x + r, y + r), fill=(b, b, min(255, b + 20)))


def emblem(size: int, bg: bool = True) -> Image.Image:
    """Lupa con un planeta anillado dentro: 'la prueba' + el cosmos."""
    S = size * 4
    if bg:
        im = radial_bg(S, S, S * 0.45, S * 0.4).convert("RGBA")
        stars(im, 70, 3, rmax=S * 0.004)
    else:
        im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cx, cy, R = S * 0.44, S * 0.42, S * 0.25
    lw = int(S * 0.055)
    d = ImageDraw.Draw(im)
    # mango
    a = np.deg2rad(45)
    hx0, hy0 = cx + (R + lw * 0.3) * np.cos(a), cy + (R + lw * 0.3) * np.sin(a)
    hx1, hy1 = S * 0.80, S * 0.80
    d.line((hx0, hy0, hx1, hy1), fill=ACC, width=int(S * 0.085))
    rr = S * 0.0425
    d.ellipse((hx1 - rr, hy1 - rr, hx1 + rr, hy1 + rr), fill=ACC)
    # interior de la lente
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(16, 26, 58, 255))
    # planeta + anillo
    pr = R * 0.42
    ring_back = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(ring_back).ellipse((cx - pr * 1.9, cy - pr * 0.55, cx + pr * 1.9, cy + pr * 0.55),
                                      outline=(235, 245, 255, 255), width=int(S * 0.016))
    ring_front = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(ring_front).arc((cx - pr * 1.9, cy - pr * 0.55, cx + pr * 1.9, cy + pr * 0.55),
                                   0, 180, fill=(235, 245, 255, 255), width=int(S * 0.016))
    ring_back = ring_back.rotate(18, center=(cx, cy), resample=Image.Resampling.BICUBIC)
    ring_front = ring_front.rotate(18, center=(cx, cy), resample=Image.Resampling.BICUBIC)
    im.alpha_composite(ring_back)
    planet = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    shade = np.clip(1 - (np.sqrt((xx - (cx - pr * 0.4)) ** 2 + (yy - (cy - pr * 0.4)) ** 2) / (pr * 2)), 0, 1)
    rgb = np.array(ACC2, np.float32) * (0.45 + 0.75 * shade[..., None])
    alpha = (dist <= pr).astype(np.float32) * 255
    planet = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), alpha]).astype(np.uint8), "RGBA")
    im.alpha_composite(planet)
    im.alpha_composite(ring_front)
    # aro de la lupa
    d = ImageDraw.Draw(im)
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=ACC, width=lw)
    # destello
    d.arc((cx - R * 0.72, cy - R * 0.72, cx + R * 0.72, cy + R * 0.72), 200, 245,
          fill=(255, 255, 255, 200), width=int(S * 0.018))
    return im.resize((size, size), Image.Resampling.LANCZOS)


def main():
    OUT.mkdir(exist_ok=True)
    # Foto de perfil (YouTube la recorta en círculo; 800x800 recomendado)
    logo = emblem(800)
    logo.convert("RGB").save(OUT / "profile_800.png")
    mask = Image.new("L", (800, 800), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 799, 799), fill=255)
    round_logo = logo.copy()
    round_logo.putalpha(mask)
    round_logo.save(OUT / "logo.png")
    # Marca de agua del vídeo (150x150, PNG transparente)
    emblem(150, bg=False).save(OUT / "watermark_150.png")
    # Banner 2560x1440 (zona segura central 1546x423)
    W, H = 2560, 1440
    ban = radial_bg(W, H, W * 0.5, H * 0.5, inner=(30, 48, 104), radius=W * 0.55).convert("RGBA")
    stars(ban, 900, 11, rmax=2.6)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((W * 0.5 - 900, H * 0.5 - 260, W * 0.5 + 900, H * 0.5 + 260),
                                 fill=ACC2 + (40,))
    ban.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120)))
    em = emblem(360)
    m = Image.new("L", (360, 360), 0)
    ImageDraw.Draw(m).ellipse((0, 0, 359, 359), fill=255)
    em.putalpha(m)
    sx0 = (W - 1546) // 2
    ban.alpha_composite(em, (sx0 + 10, H // 2 - 180))
    d = ImageDraw.Draw(ban)
    ft = font("anton", 132)
    tx = sx0 + 410
    d.text((tx, H // 2 - 190), "CIENCIA CON", font=ft, fill=(255, 255, 255))
    w1 = ft.getlength("CIENCIA CON ")
    d.text((tx + w1, H // 2 - 190), "PRUEBAS", font=ft, fill=ACC)
    fs = font("semibold", 44)
    d.text((tx + 4, H // 2 + 0), "Historias reales de ciencia, espacio e historia.", font=fs,
           fill=(220, 230, 250))
    d.text((tx + 4, H // 2 + 56), "Cada dato, con su fuente.", font=fs, fill=(220, 230, 250))
    fp = font("extrabold", 38)
    pill = "NUEVOS SHORTS CADA DÍA"
    pw = fp.getlength(pill)
    d.rounded_rectangle((tx, H // 2 + 140, tx + pw + 60, H // 2 + 205), radius=32, fill=ACC)
    d.text((tx + 30, H // 2 + 148), pill, font=fp, fill=NAVY)
    ban.convert("RGB").save(OUT / "banner_2560x1440.png")
    # Vista previa de las zonas seguras del banner (solo para revisión)
    prev = ban.convert("RGB").copy()
    pd_ = ImageDraw.Draw(prev)
    pd_.rectangle(((W - 1546) // 2, (H - 423) // 2, (W + 1546) // 2, (H + 423) // 2), outline=(255, 0, 0), width=4)
    prev.resize((1280, 720)).save(OUT / "banner_preview_safe_area.jpg", quality=88)
    print("Marca generada en", OUT)


if __name__ == "__main__":
    main()
