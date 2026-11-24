"""Música y efectos de sonido 100 % originales generados por código.

No se usa ninguna pista de terceros, así que no hay reclamaciones de Content ID
ni reparto de ingresos por licencia musical.
"""
from __future__ import annotations

import numpy as np

from common import SR

MOODS = {
    # raíz (Hz), bpm, progresión (semitonos de la raíz, menor/mayor)
    "misterio": (110.0, 80, [(0, "m"), (8, "M"), (3, "M"), (10, "M")]),
    "cosmos":   (98.0, 72, [(0, "m"), (5, "m"), (8, "M"), (7, "M")]),
    "epico":    (87.3, 88, [(0, "m"), (8, "M"), (10, "M"), (7, "M")]),
    "asombro":  (130.8, 84, [(0, "M"), (9, "m"), (5, "M"), (7, "M")]),
}


def _st(f: float, s: float) -> float:
    return f * 2 ** (s / 12)


def _tone(freq: float, n: int, harmonics: int = 6, detune: float = 0.0, rng=None) -> np.ndarray:
    t = np.arange(n) / SR
    out = np.zeros(n, dtype=np.float64)
    for d in (-detune, detune) if detune else (0.0,):
        f = freq * (1 + d)
        ph = rng.uniform(0, 2 * np.pi) if rng is not None else 0.0
        for k in range(1, harmonics + 1):
            if f * k > 6000:
                break
            out += np.sin(2 * np.pi * f * k * t + ph * k) / (k ** 1.6)
    return out


def _reverb(x: np.ndarray, seconds: float = 1.6, mix: float = 0.35, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = rng.standard_normal(n) * np.exp(-np.linspace(0, 7, n))
    ir /= np.sqrt(np.sum(ir ** 2))
    size = 1 << int(np.ceil(np.log2(len(x) + n)))
    wet = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[:len(x)]
    return (1 - mix) * x + mix * wet


def make_music(duration: float, mood: str = "misterio", seed: int = 1) -> np.ndarray:
    rng = np.random.default_rng(seed)
    root, bpm, prog = MOODS.get(mood, MOODS["misterio"])
    beat = 60.0 / bpm
    bar = beat * 4
    n = int(duration * SR) + SR
    out = np.zeros(n)
    chord_len = bar * 2
    # Pad de acordes
    t0, ci = 0.0, int(rng.integers(0, len(prog)))
    while t0 < duration + 1:
        semi, kind = prog[ci % len(prog)]
        r = _st(root, semi)
        notes = [r, _st(r, 3 if kind == "m" else 4), _st(r, 7), _st(r, 12)]
        a, b = int(t0 * SR), min(n, int((t0 + chord_len + 1.5) * SR))
        seg = np.zeros(b - a)
        for f in notes:
            seg += _tone(f, b - a, harmonics=5, detune=0.004, rng=rng) * 0.22
        if b - a < SR // 4:
            break
        env = np.ones(b - a)
        att = min(int(0.9 * SR), (b - a) // 2)
        rel = min(int(1.5 * SR), (b - a) // 2)
        env[:att] = np.linspace(0, 1, att) ** 2
        env[-rel:] *= np.linspace(1, 0, rel)
        out[a:b] += seg * env
        # Arpegio suave (pluck) en corcheas, una octava arriba
        arp = [notes[0] * 2, notes[1] * 2, notes[2] * 2, notes[1] * 2]
        steps = int(chord_len / (beat / 2))
        for s in range(steps):
            ts = t0 + s * beat / 2
            if ts < bar * 1.0 or ts > duration:  # entra tras el primer compás
                continue
            pa = int(ts * SR)
            pn = int(0.45 * SR)
            if pa + pn > n:
                continue
            tt = np.arange(pn) / SR
            f = arp[s % len(arp)]
            pl = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 9) * 0.10
            out[pa:pa + pn] += pl
        t0 += chord_len
        ci += 1
    # Pulso grave tipo latido
    t = 0.0
    while t < duration:
        a = int(t * SR)
        pn = int(0.5 * SR)
        if a + pn < n:
            tt = np.arange(pn) / SR
            f = root / 2 * (1 + 0.6 * np.exp(-tt * 30))
            out[a:a + pn] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 7) * 0.55
        t += beat * 2
    out = _reverb(out, seed=seed)
    out = out[: int(duration * SR)]
    fade = int(0.8 * SR)
    out[-fade:] *= np.linspace(1, 0, fade)
    out[: int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))
    return (out / (np.max(np.abs(out)) + 1e-9)).astype(np.float32)


def _lowpass(x: np.ndarray, cutoff: float) -> np.ndarray:
    """Filtro paso bajo de un polo (suave), en el dominio de la frecuencia."""
    size = 1 << int(np.ceil(np.log2(len(x) + 1)))
    X = np.fft.rfft(x, size)
    f = np.fft.rfftfreq(size, 1 / SR)
    return np.fft.irfft(X / np.sqrt(1 + (f / cutoff) ** 2), size)[:len(x)]


def _piano(freq: float, n: int, vel: float, rng) -> np.ndarray:
    """Nota de piano aproximada: parciales algo inarmónicos con caída exponencial y ataque percutido."""
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k, a in ((1, 1.0), (2, 0.45), (3, 0.22), (4, 0.12), (5, 0.06)):
        fk = freq * k * np.sqrt(1 + 0.0004 * k * k)
        out += a * np.sin(2 * np.pi * fk * t + rng.uniform(0, 6.28)) * np.exp(-t * (2.2 + 1.3 * k))
    att = min(n, int(0.004 * SR))
    out[:att] *= np.linspace(0, 1, att)
    return out * vel


def make_documental(duration: float, seed: int = 1, accents: list[float] | None = None) -> np.ndarray:
    """Banda sonora de documental (original): dron grave, cuerdas sintéticas, piano escaso,
    subidas de tensión y golpes graves en los momentos clave (accents, en segundos)."""
    rng = np.random.default_rng(seed)
    n = int(duration * SR) + SR
    out = np.zeros(n)
    t_all = np.arange(n) / SR
    root = 73.42  # re menor
    # Dron: re1 + la1 con respiración lenta
    swell = 0.75 + 0.25 * np.sin(2 * np.pi * t_all / 9.0)
    out += (np.sin(2 * np.pi * root / 2 * t_all) * 0.5 + np.sin(2 * np.pi * root * 0.75 * t_all) * 0.18) * swell
    # Cuerdas: acordes largos con muchas voces desafinadas y ataque lento
    prog = [(0, "m"), (8, "M"), (3, "M"), (10, "M")]
    chord = 4.0
    t0, ci = 0.0, 0
    while t0 < duration + 1:
        semi, kind = prog[ci % len(prog)]
        r = _st(root * 2, semi)
        notes = [r, _st(r, 3 if kind == "m" else 4), _st(r, 7), _st(r, 12)]
        a, b = int(t0 * SR), min(n, int((t0 + chord + 2.0) * SR))
        if b - a < SR // 4:
            break
        seg = np.zeros(b - a)
        for f in notes:
            seg += _tone(f, b - a, harmonics=7, detune=0.006, rng=rng) * 0.16
        env = np.ones(b - a)
        att, rel = min(int(1.6 * SR), (b - a) // 2), min(int(2.0 * SR), (b - a) // 2)
        env[:att] = np.linspace(0, 1, att) ** 1.5
        env[-rel:] *= np.linspace(1, 0, rel)
        out[a:b] += seg * env
        # Piano: 2-3 notas escasas por acorde, octava media
        for _ in range(int(rng.integers(2, 4))):
            ts = t0 + rng.uniform(0.3, chord - 0.4)
            if ts > duration - 1.0:
                continue
            pa, pn = int(ts * SR), int(2.5 * SR)
            if pa + pn < n:
                f = notes[int(rng.integers(0, 4))] * 2
                out[pa:pa + pn] += _piano(f, pn, rng.uniform(0.25, 0.4), rng)
        t0 += chord
        ci += 1
    # Tensión antes de cada momento clave + golpe grave en el momento
    for ac in accents or []:
        ra, rb = int(max(0, ac - 1.8) * SR), int(ac * SR)
        if rb - ra > SR // 4 and rb < n:
            noise = rng.standard_normal(rb - ra)
            noise = np.diff(np.concatenate([[0], noise]))  # paso alto suave
            out[ra:rb] += noise * np.linspace(0, 1, rb - ra) ** 2.5 * 0.10
        hn = int(1.6 * SR)
        if rb + hn < n:
            tt = np.arange(hn) / SR
            f = 55 * (1 + 0.8 * np.exp(-tt * 18))
            out[rb:rb + hn] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 2.6) * 0.9
    out = _lowpass(out, 3800)
    out = _reverb(out, seconds=2.8, mix=0.42, seed=seed)
    out = out[: int(duration * SR)]
    fade = int(1.2 * SR)
    out[-fade:] *= np.linspace(1, 0, fade)
    out[: int(0.3 * SR)] *= np.linspace(0, 1, int(0.3 * SR))
    return (out / (np.max(np.abs(out)) + 1e-9)).astype(np.float32)


def whoosh(seed: int = 0, length: float = 0.55) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(length * SR)
    noise = rng.standard_normal(n)
    # Filtro paso bajo variable (barrido) — bucle en bloques para velocidad
    cut = np.concatenate([np.linspace(0.02, 0.35, int(n * 0.65)),
                          np.linspace(0.35, 0.05, n - int(n * 0.65))])
    y = np.zeros(n)
    acc = 0.0
    for i in range(n):
        acc += cut[i] * (noise[i] - acc)
        y[i] = acc
    env = np.concatenate([np.linspace(0, 1, int(n * 0.65)) ** 2,
                          np.linspace(1, 0, n - int(n * 0.65)) ** 1.5])
    y *= env
    return (y / (np.max(np.abs(y)) + 1e-9)).astype(np.float32)


def impact(seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(1.1 * SR)
    t = np.arange(n) / SR
    f = 38 + 110 * np.exp(-t * 12)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
    click = rng.standard_normal(n) * np.exp(-t * 60) * 0.35
    y = _reverb(body + click, seconds=1.0, mix=0.25, seed=seed)
    return (y / (np.max(np.abs(y)) + 1e-9)).astype(np.float32)


def ducking_envelope(voice: np.ndarray, depth: float = 0.55) -> np.ndarray:
    """Ganancia para la música: baja cuando hay voz, sube en las pausas."""
    win = int(0.05 * SR)
    pad = (-len(voice)) % win
    v = np.pad(np.abs(voice), (0, pad)).reshape(-1, win).mean(axis=1)
    v = v / (v.max() + 1e-9)
    act = np.clip(v * 4, 0, 1)
    # suavizado ataque/liberación
    sm = np.zeros_like(act)
    for i in range(len(act)):
        prev = sm[i - 1] if i else 0
        k = 0.5 if act[i] > prev else 0.08
        sm[i] = prev + k * (act[i] - prev)
    g = 1 - depth * sm
    return np.repeat(g, win)[: len(voice)].astype(np.float32)
