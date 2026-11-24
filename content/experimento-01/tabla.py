"""Tabla de características del experimento 01 (lee guiones y metadatos de staging)."""
import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SLOTS = ["sáb 28/11 19:00", "dom 29/11 02:00", "dom 29/11 19:00", "lun 30/11 02:00", "lun 30/11 19:00",
         "mar 1/12 02:00", "mar 1/12 19:00", "mié 2/12 02:00", "mié 2/12 19:00", "jue 3/12 02:00"]
rows = ["| ID | Grupo | Serie | Título | Duración | Palabras | Tarjetas | Remotion | Estilo | Pruebas | Publicación propuesta (Madrid) |",
        "|---|---|---|---|---|---|---|---|---|---|---|"]
for i, p in enumerate(sorted(glob.glob(str(ROOT / "content/experimento-01/scripts/*.json")))):
    s = json.load(open(p, encoding="utf-8"))
    m = json.load(open(glob.glob(str(ROOT / f"staging/experimento-01/{s['id']}-*/meta.json"))[0], encoding="utf-8"))
    w = sum(len(x["text"].split()) for x in s["segments"])
    kinds = [x["visual"].get("kind") for x in s["segments"] if x["visual"].get("kind")]
    ev = sum(1 for x in s["segments"] if x["visual"].get("evidence"))
    rows.append(f"| {s['id']} | {s['variant']} | {s['series']} | {s['title'][:58]} | {m['duration']:.1f} s | {w} | "
                f"{', '.join(kinds)} | {'no' if s.get('remotion') is False else 'sí'} | {s.get('style', 'actual')} | {ev} | {SLOTS[i]} |")
print("\n".join(rows))
