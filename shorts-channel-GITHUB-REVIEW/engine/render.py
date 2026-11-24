"""Compositor de Shorts 1080x1920: imagen con movimiento, tarjetas animadas
originales (cifras, líneas de tiempo), subtítulos dinámicos, sello de
"PRUEBA", música original y efectos. Exporta MP4 H.264 + AAC.
"""
from __future__ import annotations

import math
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

import music
from common import DATA, DEFAULT_STRINGS, FFMPEG, FPS, H, ROOT, SR, W, decode_audio, font, hex_rgb

BILINEAR = Image.Resampling.BILINEAR
LANCZOS = Image.Resampling.LANCZOS


def ease_out(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def clamp(x, a=0.0, b=1.0):
    return min(max(x, a), b)


# --------------------------------------------------------------------------- #
#  Preparación de imágenes
# --------------------------------------------------------------------------- #
def grade(im: Image.Image) -> Image.Image:
    im = ImageEnhance.Contrast(im).enhance(1.08)
    im = ImageEnhance.Color(im).enhance(0.92)
    return im.filter(ImageFilter.UnsharpMask(radius=2, percent=55, threshold=2))


def prep_cover(path: Path, headroom: float = 1.3) -> Image.Image:
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    iw, ih = im.size
    ch = ih if iw / ih > W / H else iw * H / W
    scale = (H * headroom) / ch
    nw, nh = round(iw * scale), round(ih * scale)
    if nw * nh > 26e6:  # límite de memoria
        k = math.sqrt(26e6 / (nw * nh))
        nw, nh = round(nw * k), round(nh * k)
    return grade(im.resize((nw, nh), LANCZOS))


def prep_fit(path: Path) -> tuple[Image.Image, Image.Image]:
    """Para imágenes anchas (mapas, cuadros, diagramas): fondo desenfocado
    + imagen completa en primer plano."""
    im = grade(ImageOps.exif_transpose(Image.open(path)).convert("RGB"))
    bg = ImageOps.fit(im, (W // 4, H // 4), LANCZOS).filter(ImageFilter.GaussianBlur(10))
    bg = ImageEnhance.Brightness(bg.resize((W, H), BILINEAR)).enhance(0.45)
    fw = 1000 if H > W else 1500
    fh = round(im.height * fw / im.width)
    maxh = 1100 if H > W else 820
    if fh > maxh:
        fh = maxh
        fw = round(im.width * fh / im.height)
    fg = im.resize((round(fw * 1.1), round(fh * 1.1)), LANCZOS)
    return bg, fg


def starfield(seed: int, accent: tuple) -> Image.Image:
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W * 0.5) / W) ** 2 + ((yy - H * 0.38) / H) ** 2)
    base = np.array([11, 16, 32], np.float32)
    glow = np.array([24, 40, 86], np.float32)
    arr = base + glow * np.clip(1 - d * 1.9, 0, 1)[..., None]
    n = 900
    xs, ys = rng.integers(0, W, n), rng.integers(0, H, n)
    br = rng.uniform(60, 230, n)
    for x, y, b in zip(xs, ys, br):
        arr[y, x] = np.maximum(arr[y, x], b)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return im.filter(ImageFilter.GaussianBlur(0.6))


# --------------------------------------------------------------------------- #
#  Elementos gráficos
# --------------------------------------------------------------------------- #
def text_block(lines: list[tuple[str, tuple]], fnt, stroke: int, max_w: int = 1000,
               line_gap: float = 1.05, shadow: bool = True) -> Image.Image:
    """Renderiza líneas centradas [(texto, color)] en un RGBA recortado."""
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * line_gap)
    widths = [fnt.getlength(t) for t, _ in lines]
    iw = int(min(max(widths), 2000) + stroke * 2 + 30)
    ih = lh * len(lines) + stroke * 2 + 30
    im = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, ((t, col), w) in enumerate(zip(lines, widths)):
        x = (iw - w) / 2
        y = stroke + 10 + i * lh
        if shadow:
            d.text((x + 7, y + 9), t, font=fnt, fill=(0, 0, 0, 150),
                   stroke_width=stroke, stroke_fill=(0, 0, 0, 150))
        d.text((x, y), t, font=fnt, fill=col, stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
    if im.width > max_w:
        k = max_w / im.width
        im = im.resize((max_w, round(im.height * k)), LANCZOS)
    return im


def wrap(text: str, fnt, max_w: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if cur and fnt.getlength(test) > max_w:
            lines.append(cur)
            cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


def paste_center(frame: Image.Image, im: Image.Image, cx: float, cy: float,
                 scale: float = 1.0, alpha: float = 1.0):
    if scale != 1.0:
        im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), BILINEAR)
    if alpha < 1.0:
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im = im.copy()
        im.putalpha(a)
    frame.paste(im, (round(cx - im.width / 2), round(cy - im.height / 2)), im)


# --------------------------------------------------------------------------- #
#  Segmentos
# --------------------------------------------------------------------------- #
MOTIONS = {
    #            z0    z1    px0   px1   py0   py1
    "zoom_in":  (1.00, 1.16, None, None, None, None),
    "zoom_out": (1.16, 1.00, None, None, None, None),
    "pan_lr":   (1.04, 1.08, 0.10, 0.90, None, None),
    "pan_rl":   (1.04, 1.08, 0.90, 0.10, None, None),
    "pan_ud":   (1.05, 1.10, None, None, 0.10, 0.90),
    "pan_du":   (1.05, 1.10, None, None, 0.90, 0.10),
}


STOPWORDS_BY_LANG = {
    "es": set("el la los las un una unos unas y o e ni de del al a en con por para "
              "sin sobre que se su sus lo le les mi tu muy más no como entre hasta "
              "desde tras cada este esta ese esa".split()),
    "en": set("a an the and or nor of to in on at by for with from into onto as than that "
              "this these those its his her their our your my is was were be been are "
              "not no so but if then over under about after before".split()),
}
STOPWORDS = STOPWORDS_BY_LANG["es"]  # se sustituye por el del idioma del canal en Renderer



def layout(long: bool) -> dict:
    """Posiciones de cada capa según el formato. Vertical = valores de siempre de los Shorts."""
    if not long:
        return dict(tag=(46, 120), hook_y=560, hook_w=1000, hook_font=150,
                    stamp_img=(W - 300, 470), stamp_card=(W / 2, 1420), stamp_scale=1.0,
                    info_x=52, info_y=228, info_w=930, cap_y=1190, cap_font=92, cap_words=3, cap_chars=14,
                    cap_w=860, stat_y=560, lab_w=900, tl=(200, 880, 700), title_y=640, list_y=460, bar_x=110,
                    fit_cy=760, ov_top=430, ov_bot=(1180, 740))
    # Horizontal 16:9 (1920x1080): subtítulos de documental (frases de hasta 7 palabras abajo)
    return dict(tag=(40, 34), hook_y=470, hook_w=1600, hook_font=130,
                stamp_img=(W - 250, 270), stamp_card=(W - 250, 270), stamp_scale=0.72,
                info_x=40, info_y=132, info_w=1500, cap_y=960, cap_font=60, cap_words=7, cap_chars=42,
                cap_w=1500, stat_y=400, lab_w=1400, tl=(360, 1560, 500), title_y=470, list_y=250, bar_x=360,
                fit_cy=520, ov_top=240, ov_bot=(720, 360))

CARD_KINDS = ("stat", "timeline", "title", "compare", "steps", "skull")


@dataclass
class Seg:
    text: str
    visual: dict
    audio: np.ndarray = None
    words: list = field(default_factory=list)
    a_start: float = 0.0
    v_start: float = 0.0
    v_end: float = 0.0
    kind: str = "image"
    base: Image.Image = None
    fit_bg: Image.Image = None
    fit_fg: Image.Image = None
    card_bg: Image.Image = None
    motion: str = "zoom_in"
    focus: tuple = (0.5, 0.5)
    remo_frames: list = None  # fotogramas PNG de Remotion (tarjetas); None = tarjeta Pillow


class Renderer:
    def __init__(self, script: dict, cfg: dict, segs: list[Seg], credits: list[dict]):
        self.s, self.cfg, self.segs, self.credits = script, cfg, segs, credits
        self.accent = hex_rgb(cfg["brand"]["accent"])
        self.accent2 = hex_rgb(cfg["brand"]["accent2"])
        self.white = (255, 255, 255)
        self._cap_cache: dict = {}
        self.txt = {**DEFAULT_STRINGS, **cfg.get("strings", {})}
        self.stopwords = STOPWORDS_BY_LANG.get(cfg.get("channel", {}).get("language", "es"), STOPWORDS)
        self.doc = script.get("style") == "documental"
        self.cinematic = script.get("style") in ("cinematic", "documental")
        self.xfade = 0.32 if self.doc else 0.12  # duración del fundido entre planos
        self.long = W > H  # formato horizontal 16:9 (documentales)
        self.L = layout(self.long)
        if self.cinematic:
            self._build_cinematic()
        self._build_overlay()
        self._build_static()
        self._build_captions()

    # ---------------- preparación ----------------
    def _build_overlay(self):
        y = np.arange(H, dtype=np.float32)
        top = np.clip(1 - y / self.L["ov_top"], 0, 1) ** 1.6 * 0.70
        b0, b1 = self.L["ov_bot"]
        bot = np.clip((y - b0) / b1, 0, 1) ** 1.3 * 0.78
        col = np.maximum(top, bot)
        x = np.arange(W, dtype=np.float32)
        vx = ((x - W / 2) / (W / 2)) ** 2
        vy = ((y - H / 2) / (H / 2)) ** 2
        vig = np.clip((vx[None, :] + vy[:, None]) * 0.28 - 0.08, 0, 0.5)
        m = np.clip(np.maximum(col[:, None], vig) + 0.10, 0, 1)
        self.overlay = Image.fromarray((m * 255).astype(np.uint8), "L")
        self.black = Image.new("RGB", (W, H), (0, 0, 0))

    def _build_cinematic(self):
        """Estilo «cinematic» (grupo B): grano de película sutil y barrido de luz al entrar cada foto."""
        rng = np.random.default_rng(int(self.s.get("id", 0) or 0))
        self.grain = [Image.fromarray(np.clip(rng.normal(128, 38, (H // 2, W // 2)), 0, 255).astype(np.uint8), "L")
                      .resize((W, H), BILINEAR).convert("RGB") for _ in range(4)]
        # banda diagonal de luz cálida (máscara L) más ancha que el lienzo para desplazarla
        x = np.arange(W * 2, dtype=np.float32)[None, :]
        y = np.arange(H, dtype=np.float32)[:, None]
        dist = np.abs((x - W) + (y - H / 2) * 0.45)
        band = np.clip(1 - dist / 170, 0, 1) ** 2 * 70
        self.sweep_mask = Image.fromarray(band.astype(np.uint8), "L")
        self.warm = Image.new("RGB", (W, H), (255, 236, 200))

    def _cinematic(self, fr: Image.Image, t: float, si: int) -> Image.Image:
        seg = self.segs[si]
        lt = t - seg.v_start
        if seg.kind == "image" and 0 <= lt < 1.6:
            off = int((-0.6 + 1.2 * (lt / 1.6)) * W)  # la banda cruza de izquierda a derecha
            mask = self.sweep_mask.crop((W - off - W // 2, 0, W - off - W // 2 + W, H))
            fr = Image.composite(self.warm, fr, mask)
        return Image.blend(fr, self.grain[int(t * FPS) % 4], 0.045)

    def _build_static(self):
        b = self.cfg["brand"]
        num = self.s["id"]
        # Etiqueta superior (serie + número) con logo
        f = font("extrabold", 38)
        label = f"{self.s.get('series', 'CIENCIA')}  ·  {self.txt['number']} {num}"
        tw = int(f.getlength(label))
        tag = Image.new("RGBA", (tw + 150, 84), (0, 0, 0, 0))
        d = ImageDraw.Draw(tag)
        d.rounded_rectangle((44, 10, tw + 140, 74), radius=32, fill=(10, 14, 28, 215),
                            outline=self.accent + (255,), width=3)
        d.text((92, 19), label, font=f, fill=self.white)
        logo_p = DATA / "brand" / "logo.png"
        if logo_p.exists():
            lg = Image.open(logo_p).convert("RGBA").resize((84, 84), LANCZOS)
            tag.paste(lg, (0, 0), lg)
        self.tag = tag
        # Gancho visual (primeros segundos)
        hook = self.s.get("hook_text", "").upper().split("\n")
        cols = [self.white] * (len(hook) - 1) + [self.accent]
        self.hook_img = text_block(list(zip(hook, cols)), font("anton", self.L["hook_font"]), stroke=11,
                                   max_w=self.L["hook_w"], line_gap=1.0)
        # Sello "PRUEBA"
        st = Image.new("RGBA", (520, 230), (0, 0, 0, 0))
        d = ImageDraw.Draw(st)
        d.rounded_rectangle((10, 10, 510, 220), radius=26, outline=self.accent + (255,), width=10,
                            fill=(10, 14, 28, 170))
        fa = font("anton", 112)
        tx = self.txt["stamp"]
        d.text(((520 - fa.getlength(tx)) / 2, 18), tx, font=fa, fill=self.accent)
        fb = font("extrabold", 40)
        sub = f"{self.txt['number']} {num}"
        d.text(((520 - fb.getlength(sub)) / 2, 160), sub, font=fb, fill=self.white)
        self.stamp = st.rotate(-7, resample=Image.Resampling.BICUBIC, expand=True)

    def _build_captions(self):
        """Agrupa las palabras en bloques de 1-3 palabras."""
        self.chunks = []  # (start, end, [palabras], [inicios])
        for seg in self.segs:
            toks = seg.text.split()
            punct_after = set()
            ti = 0
            for wi, w in enumerate(seg.words):
                # alinear con el texto original para detectar puntuación
                while ti < len(toks):
                    clean = toks[ti].strip(".,;:!?¡¿«»\"'()…—-").lower()
                    ti += 1
                    if clean == w["text"].strip(".,;:!?¡¿«»\"'()…—-").lower():
                        if toks[ti - 1][-1:] in ".,;:!?…—":
                            punct_after.add(wi)
                        break
            cur, curs = [], []
            nw = len(seg.words)
            for wi, w in enumerate(seg.words):
                txt = w["text"].upper().strip("«»\"")
                cur.append(txt)
                curs.append(seg.a_start + w["start"])
                too_long = sum(len(c) for c in cur) >= self.L["cap_chars"]
                # no cortar un bloque en un artículo/preposición ("Y MONTARON UN")
                dangling = txt.lower() in self.stopwords and wi + 1 < nw and wi not in punct_after
                cw = self.L["cap_words"]
                if wi in punct_after or ((len(cur) >= cw or too_long) and not dangling) or len(cur) >= cw + 1:
                    self.chunks.append([curs[0], None, cur, curs])
                    cur, curs = [], []
            if cur:
                self.chunks.append([curs[0], None, cur, curs])
            last = seg.words[-1] if seg.words else None
            if last is not None:
                self.chunks[-1].append(seg.a_start + last["start"] + last["dur"] + 0.35)
        for i, c in enumerate(self.chunks):
            nxt = self.chunks[i + 1][0] if i + 1 < len(self.chunks) else 1e9
            hard_end = c[4] if len(c) > 4 else 1e9
            c[1] = min(nxt, hard_end)

    def caption_img(self, ci: int, hi: int) -> Image.Image:
        key = (ci, hi)
        if key in self._cap_cache:
            return self._cap_cache[key]
        words = self.chunks[ci][2]
        f = font("black", self.L["cap_font"])
        stroke = 9 if not self.long else 6
        capw = self.L["cap_w"]
        imw = capw + 140
        space = f.getlength(" ")
        widths = [f.getlength(w) for w in words]
        lines, cur, cw = [], [], 0.0
        for i, (w, ww) in enumerate(zip(words, widths)):
            if cur and cw + space + ww > capw:
                lines.append(cur)
                cur, cw = [], 0.0
            cw += (space if cur else 0) + ww
            cur.append(i)
        lines.append(cur)
        asc, desc = f.getmetrics()
        lh = int((asc + desc) * 1.02)
        im = Image.new("RGBA", (imw, lh * len(lines) + 40), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for li, line in enumerate(lines):
            tot = sum(widths[i] for i in line) + space * (len(line) - 1)
            x = (imw - tot) / 2
            y = 18 + li * lh
            for i in line:
                d.text((x + 6, y + 8), words[i], font=f, fill=(0, 0, 0, 140),
                       stroke_width=stroke, stroke_fill=(0, 0, 0, 140))
                x += widths[i] + space
            x = (imw - tot) / 2
            for i in line:
                col = self.accent if i == hi else self.white
                d.text((x, y), words[i], font=f, fill=col, stroke_width=stroke,
                       stroke_fill=(0, 0, 0, 255))
                x += widths[i] + space
        self._cap_cache[key] = im
        return im

    # ---------------- fondos ----------------
    def seg_frame(self, si: int, t: float) -> Image.Image:
        seg = self.segs[si]
        dur = max(seg.v_end - seg.v_start, 0.1)
        p = clamp((t - seg.v_start) / dur)
        punch = 0.0
        if si > 0 and not self.doc:  # el documental no usa «zoom punch»: entra con foco progresivo
            pt = t - seg.v_start
            if pt >= 0:
                punch = 0.07 * math.exp(-pt * 9)
        if seg.kind in CARD_KINDS:
            return self.card_frame(seg, t, p)
        if self.doc:
            p = p * p * (3 - 2 * p)  # movimiento de cámara con aceleración y frenada suaves
            fr = self._image_frame(seg, t, p, punch)
            lt = t - seg.v_start
            if si > 0 and 0 <= lt < 0.45:  # «rack focus»: la imagen entra desenfocada y se enfoca
                fr = fr.filter(ImageFilter.GaussianBlur(9 * (1 - ease_out(lt / 0.45))))
            return fr
        return self._image_frame(seg, t, p, punch)

    def _image_frame(self, seg: Seg, t: float, p: float, punch: float) -> Image.Image:
        if seg.motion == "fit":
            fr = seg.fit_bg.copy()
            z = (1.0 + 0.07 * p + punch) / 1.1
            fg = seg.fit_fg.resize((round(seg.fit_fg.width * z), round(seg.fit_fg.height * z)),
                                   BILINEAR)
            cy = self.L["fit_cy"]
            sh = Image.new("RGBA", (fg.width + 40, fg.height + 40), (0, 0, 0, 0))
            ImageDraw.Draw(sh).rounded_rectangle((20, 26, fg.width + 20, fg.height + 26),
                                                 radius=18, fill=(0, 0, 0, 120))
            fr.paste(sh, (round(W / 2 - sh.width / 2), round(cy - sh.height / 2)), sh)
            fr.paste(fg, (round(W / 2 - fg.width / 2), round(cy - fg.height / 2)))
            return fr
        z0, z1, px0, px1, py0, py1 = MOTIONS.get(seg.motion, MOTIONS["zoom_in"])
        if seg.visual.get("zoom"):  # zoom personalizado [inicio, fin]
            z0, z1 = seg.visual["zoom"]
        z = z0 + (z1 - z0) * p + punch
        fx, fy = seg.focus
        px = fx if px0 is None else px0 + (px1 - px0) * p
        py = fy if py0 is None else py0 + (py1 - py0) * p
        B = seg.base
        bw, bh = B.size
        if bw / bh > W / H:
            ch = bh / 1.0
            cw = ch * W / H
        else:
            cw = bw
            ch = cw * H / W
        rw, rh = cw / z, ch / z
        center = seg.visual.get("center")  # centrar en un punto de la imagen (0-1)
        if center:
            x0 = clamp(center[0] * bw - rw / 2, 0, bw - rw)
            y0 = clamp(center[1] * bh - rh / 2, 0, bh - rh)
        else:
            x0 = (bw - rw) * px
            y0 = (bh - rh) * py
        fr = B.transform((W, H), Image.Transform.EXTENT, (x0, y0, x0 + rw, y0 + rh), BILINEAR)
        mk = seg.visual.get("marker")  # círculo animado sobre un detalle de la imagen
        if mk:
            sx = (mk[0] * bw - x0) / rw * W
            sy = (mk[1] * bh - y0) / rh * H
            lt = t - seg.v_start
            a = clamp((lt - 0.3) / 0.3)
            if a > 0:
                d = ImageDraw.Draw(fr)
                r = 54 + 10 * math.sin(lt * 5)
                d.ellipse((sx - r, sy - r, sx + r, sy + r), outline=self.accent, width=7)
                if seg.visual.get("marker_label"):
                    lab = text_block([(seg.visual["marker_label"].upper(), self.accent)],
                                     font("extrabold", 46), stroke=6)
                    paste_center(fr, lab, sx, sy - r - 40, alpha=a)
        return fr

    def card_frame(self, seg: Seg, t: float, p: float) -> Image.Image:
        lt = t - seg.v_start
        if seg.remo_frames:  # tarjeta animada de Remotion sobre el fondo del motor
            idx = max(0, min(int(math.floor(max(0.0, lt) * FPS)), len(seg.remo_frames) - 1))
            try:
                with Image.open(seg.remo_frames[idx]) as png:
                    fg = png.convert("RGBA")
                if fg.size != (W, H):
                    raise ValueError(f"PNG de {fg.size}")
                fr = seg.card_bg.copy()
                fr.paste(fg, (0, 0), fg)
                return fr
            except (OSError, ValueError) as e:  # PNG dañado: esta tarjeta sigue con Pillow
                print(f"  Aviso: fotograma Remotion no válido ({e}); tarjeta Pillow")
                seg.remo_frames = None
        fr = seg.card_bg.copy()
        v = seg.visual
        if seg.kind == "stat":
            val = str(v["value"])
            digits = "".join(ch for ch in val if ch.isdigit())
            shown = val
            if digits and v.get("count", True):
                k = ease_out(lt / 0.9)
                target = int(digits)
                cur = int(round(target * k))
                shown = val.replace(digits, f"{cur:,}".replace(",", ".") if v.get("thousands") else str(cur), 1)
            big = text_block([(v.get("prefix", "") + shown + v.get("suffix", ""), self.accent)],
                             font("anton", 250), stroke=12, max_w=1000)
            sc = 0.75 + 0.25 * ease_out(lt / 0.25)
            paste_center(fr, big, W / 2, self.L["stat_y"], scale=sc)
            lab = wrap(v.get("label", "").upper(), font("extrabold", 56), self.L["lab_w"])
            if lab:
                lim = text_block([(l, self.white) for l in lab], font("extrabold", 56), stroke=6)
                paste_center(fr, lim, W / 2, self.L["stat_y"] + big.height * 0.5 + lim.height * 0.5 + 10,
                             alpha=ease_out((lt - 0.2) / 0.3))
        elif seg.kind == "timeline":
            pts = v["points"]
            act = v.get("active", len(pts) - 1)
            d = ImageDraw.Draw(fr)
            x0, x1, y = self.L["tl"]
            prog = ease_out(lt / 0.9)
            d.line((x0, y, x0 + (x1 - x0) * prog, y), fill=(200, 210, 230), width=8)
            n = len(pts)
            for i, ptd in enumerate(pts):
                x = x0 + (x1 - x0) * (i / max(n - 1, 1))
                appear = clamp((lt - 0.15 - i * 0.25) / 0.25)
                if appear <= 0:
                    continue
                col = self.accent if i == act else (235, 240, 250)
                r = 18 if i == act else 13
                if i == act:
                    pulse = 30 + 12 * math.sin(lt * 6)
                    d.ellipse((x - pulse, y - pulse, x + pulse, y + pulse), outline=col, width=4)
                d.ellipse((x - r, y - r, x + r, y + r), fill=col)
                yr = text_block([(str(ptd["year"]), col)], font("anton", 96 if i == act else 76), stroke=7)
                paste_center(fr, yr, x, y - 105, alpha=appear)
                lf = font("extrabold", 44)
                lb = wrap(ptd.get("label", "").upper(), lf, 300)
                if lb:
                    li = text_block([(l, col) for l in lb], lf, stroke=6, max_w=330)
                    paste_center(fr, li, x, y + 45 + li.height / 2, alpha=appear)
        elif seg.kind == "title":
            lines = v["text"].upper().split("\n")
            cols = [self.white] * (len(lines) - 1) + [self.accent]
            im = text_block(list(zip(lines, cols)), font("anton", 140), stroke=10)
            paste_center(fr, im, W / 2, self.L["title_y"], scale=0.85 + 0.15 * ease_out(lt / 0.3))
        elif seg.kind == "skull":  # respaldo: el esquema animado solo existe en Remotion; aquí, sus rótulos
            lines = [v.get("entry", "Entrada: bajo el pómulo izquierdo"), v.get("exit", "Salida: lo alto del cráneo")]
            tb = text_block([(l.upper(), self.white) for l in lines], font("extrabold", 50), stroke=6, max_w=900)
            paste_center(fr, tb, W / 2, self.L["title_y"], alpha=ease_out(lt / 0.3))
        elif seg.kind in ("compare", "steps"):  # respaldo simple si Remotion no está disponible
            items = v.get("items", [])
            hi = v.get("highlight", len(items) - 1)
            y = self.L["list_y"]
            if v.get("title"):
                ti = text_block([(v["title"].upper(), self.white)], font("anton", 92), stroke=8, max_w=960)
                paste_center(fr, ti, W / 2, y, alpha=ease_out(lt / 0.3))
                y += ti.height / 2 + 90
            vals = [float(it.get("value", 0) or 0) for it in items] if seg.kind == "compare" else []
            vmax = max(vals + [1e-9])
            d = ImageDraw.Draw(fr)
            for i, it in enumerate(items):
                a = clamp((lt - 0.25 - i * 0.3) / 0.25)
                if a <= 0:
                    continue
                col = self.accent if i == (hi if seg.kind == "compare" else len(items) - 1) else self.white
                if seg.kind == "compare":
                    lab = f"{it.get('label', '')}: {it.get('display', it.get('value', ''))}".upper()
                    bx = self.L["bar_x"]
                    bw = max(14, (W - 2 * bx) * vals[i] / vmax) * ease_out(a)
                    d.rounded_rectangle((bx, y + 30, bx + bw, y + 80), radius=12,
                                        fill=self.accent if col == self.accent else self.accent2)
                    tb = text_block([(lab, col)], font("extrabold", 44), stroke=5, max_w=900)
                    paste_center(fr, tb, W / 2, y - 10, alpha=a)
                    y += 150
                else:
                    tb = text_block([(f"{i + 1}. {str(it).upper()}", col)], font("extrabold", 46), stroke=5, max_w=900)
                    paste_center(fr, tb, W / 2, y, alpha=a)
                    y += 120
        return fr

    # ---------------- capas superiores ----------------
    def overlays(self, fr: Image.Image, t: float, with_captions: bool = True) -> Image.Image:
        fr = Image.composite(self.black, fr, self.overlay)
        fr.paste(self.tag, self.L["tag"], self.tag)
        # Gancho
        hook_end = self.s.get("hook_seconds", 2.4)
        if t < hook_end + 0.25 and self.s.get("hook_text"):
            a = 1.0 if t < hook_end else 1 - (t - hook_end) / 0.25
            sc = 1.0 + 0.30 * (1 - ease_out(t / 0.22))
            paste_center(fr, self.hook_img, W / 2, self.L["hook_y"], scale=sc, alpha=clamp(a))
        # Sello de prueba + fuente en pantalla
        for seg in self.segs:
            ev = seg.visual.get("evidence")
            if ev and seg.v_start <= t < seg.v_end:
                lt = t - seg.v_start
                sc = 1.0 + 0.9 * (1 - ease_out(lt / 0.18))
                # En tarjetas (cifra, línea temporal, título) el sello va bajo los subtítulos
                # para no tapar el dato ni su rótulo
                sx, sy = self.L["stamp_img"] if seg.kind == "image" else self.L["stamp_card"]
                paste_center(fr, self.stamp, sx, sy, scale=sc * self.L["stamp_scale"],
                             alpha=clamp(lt / 0.12))
                src = ev if isinstance(ev, str) else seg.visual.get("source_label", "")
                if src:
                    self._info_box(fr, f"{self.txt['source']}: " + src.upper())
            elif (seg.kind == "image" and seg.visual.get("label") and seg.v_start <= t < seg.v_end
                  and t > self.s.get("hook_seconds", 2.4)):
                self._info_box(fr, seg.visual["label"].upper())
        # Subtítulos
        if with_captions:
            for ci, (st, en, words, starts, *_) in enumerate(self.chunks):
                if st <= t < en:
                    hi = max(i for i, s0 in enumerate(starts) if s0 <= t)
                    im = self.caption_img(ci, hi)
                    pop = 0.86 + 0.14 * ease_out((t - st) / 0.09)
                    lift = 16 * (1 - ease_out((t - st) / 0.14)) if self.doc else 0  # sube un poco al entrar
                    paste_center(fr, im, W / 2 - 10, self.L["cap_y"] + lift, scale=pop)
                    break
        return fr

    def _info_box(self, fr: Image.Image, txt: str):
        """Recuadro pequeño bajo la etiqueta: fuente o pie de imagen."""
        key = ("info", txt)
        box = self._cap_cache.get(key)
        if box is None:
            size = 34
            while size > 20 and font("semibold", size).getlength(txt) > self.L["info_w"]:
                size -= 2
            f = font("semibold", size)
            tw = int(f.getlength(txt))
            box = Image.new("RGBA", (tw + 44, 62), (0, 0, 0, 0))
            d = ImageDraw.Draw(box)
            d.rounded_rectangle((0, 0, tw + 43, 61), radius=14, fill=(0, 0, 0, 170))
            d.text((22, 31), txt, font=f, fill=(225, 232, 245), anchor="lm")
            self._cap_cache[key] = box
        fr.paste(box, (self.L["info_x"], self.L["info_y"]), box)

    # ---------------- bucle principal ----------------
    def frame_at(self, t: float, with_captions: bool = True) -> Image.Image:
        si = 0
        for i, seg in enumerate(self.segs):
            if seg.v_start <= t:
                si = i
        fr = self.seg_frame(si, t)
        # fundido corto con el segmento anterior
        if si > 0:
            dt = t - self.segs[si].v_start
            if dt < self.xfade:
                prev = self.seg_frame(si - 1, t)
                k = dt / self.xfade
                fr = Image.blend(prev, fr, k * k * (3 - 2 * k) if self.doc else ease_out(k))
        if self.cinematic:
            fr = self._cinematic(fr, t, si)
        return self.overlays(fr, t, with_captions)

    def render(self, out_mp4: Path, audio: np.ndarray, total: float):
        out_mp4.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as td:
            raw = Path(td) / "mix.f32"
            audio.astype(np.float32).tofile(raw)
            cmd = [FFMPEG, "-y", "-v", "error",
                   "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                   "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", str(raw),
                   "-map", "0:v", "-map", "1:a",
                   "-c:v", "libx264", "-preset", "medium", "-crf", "21",
                   "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p",
                   "-profile:v", "high", "-r", str(FPS),
                   "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000",
                   "-c:a", "aac", "-b:a", "192k", "-ac", "2",
                   "-shortest", "-movflags", "+faststart", str(out_mp4)]
            tmp_mp4 = out_mp4.with_suffix(".tmp.mp4")
            cmd[-1] = str(tmp_mp4)
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            nframes = int(total * FPS)
            try:
                for fi in range(nframes):
                    fr = self.frame_at(fi / FPS)
                    proc.stdin.write(fr.tobytes())
            finally:
                try:
                    proc.stdin.close()
                finally:
                    proc.wait()
            if proc.returncode != 0 or not tmp_mp4.exists() or tmp_mp4.stat().st_size < 10000:
                tmp_mp4.unlink(missing_ok=True)
                raise RuntimeError("ffmpeg falló al codificar")
            tmp_mp4.replace(out_mp4)  # solo un vídeo completo ocupa el nombre final


def mix_audio(segs: list[Seg], total: float, mood: str, seed: int, music_level: float = 0.16,
              style: str | None = None) -> np.ndarray:
    n = int(total * SR) + SR
    voice = np.zeros(n, np.float32)
    for s in segs:
        a = int(s.a_start * SR)
        voice[a:a + len(s.audio)] += s.audio[: n - a]
    voice /= (np.max(np.abs(voice)) + 1e-9)
    doc = style == "documental"
    accents = [s.v_start for s in segs if s.visual.get("accent")]
    if doc:
        mus = music.make_documental(n / SR, seed=seed, accents=accents)
    else:
        mus = music.make_music(n / SR, mood=mood, seed=seed)
    mus = np.pad(mus, (0, max(0, n - len(mus))))[:n]
    duck = music.ducking_envelope(voice, depth=0.6 if doc else 0.55)
    sfx = np.zeros(n, np.float32)
    imp = music.impact(seed)
    sfx[: len(imp)] += imp[: n] * 0.75
    wh = music.whoosh(seed)
    for s in segs[1:]:
        a = int(max(0, s.v_start - 0.32) * SR)
        sfx[a:a + len(wh)] += wh[: n - a] * (0.16 if doc else 0.32)  # en documental, transiciones discretas
    mix = voice * 1.0 + mus * music_level * duck + sfx * 0.5
    mix = mix[: int(total * SR)]
    return (mix / (np.max(np.abs(mix)) + 1e-9) * 0.95).astype(np.float32)
