# Experimento 01 — Estilo actual (A) vs. estilo mejorado (B)

Objetivo: ver qué cambios mejoran la retención (duración media vista, % visto, «engaged views»/vistas).
Sin publicar hasta que el titular autorice el lote. Guiones en `content/experimento-01/scripts/`,
vídeos en `staging/experimento-01/` (la cola de publicación solo lee `output/`).

## Diseño
- 5 parejas de temas comparables (misma serie y tipo de historia); dentro de cada pareja, uno A y uno B.
- Orden de publicación alternado para repartir franjas (19:00 / 02:00 Madrid) y días.
- B prueba dos duraciones: 3 vídeos de 30-35 s y 2 de 40-45 s. A: 40-45 s.
- La voz es la misma en A y B (es-ES-AlvaroNeural, +12 %), para no mezclar efectos.
- Con 5 vídeos por grupo el resultado es **orientativo**, no estadísticamente concluyente.

| id | grupo | serie | tema | duración objetivo | franja prevista |
|---|---|---|---|---|---|
| 017 | A | MISTERIO | Las piedras que se mueven solas (Racetrack Playa, Valle de la Muerte) y cómo se resolvió en 2014 | 40-45 s | sáb 28/11 19:00 |
| 018 | B | MISTERIO | El «Bloop» (1997): el sonido submarino misterioso que registró la NOAA y su explicación | 30-35 s | dom 29/11 02:00 |
| 019 | B | ESPACIO | La Luna se aleja de la Tierra unos 3,8 cm al año (retrorreflectores del Apolo) | 40-45 s | dom 29/11 19:00 |
| 020 | A | ESPACIO | Olympus Mons, el volcán más grande conocido del sistema solar | 40-45 s | lun 30/11 02:00 |
| 021 | A | CIENCIA | Fleming y la penicilina (1928): la placa contaminada | 40-45 s | lun 30/11 19:00 |
| 022 | B | CIENCIA | Galvani, las ancas de rana y la pila de Volta | 30-35 s | mar 1/12 02:00 |
| 023 | B | HISTORIA | Newton y la peste de 1665-1666: su «año milagroso» en casa | 40-45 s | mar 1/12 19:00 |
| 024 | A | HISTORIA | Arquímedes y el «¡Eureka!»: lo que cuenta Vitruvio (y lo que es leyenda) | 40-45 s | mié 2/12 02:00 |
| 025 | A | ESPACIO | Halley predijo el regreso de su cometa para 1758 y no vivió para verlo | 40-45 s | mié 2/12 19:00 |
| 026 | B | ESPACIO | El evento Carrington (1859): la tormenta solar que hizo arder telégrafos | 30-35 s | jue 3/12 02:00 |

Cambios tras la verificación: 026 — el gancho pasa de «telégrafos ardiendo» a «telégrafos que funcionaron sin
baterías» (2 de septiembre de 1859, fuente primaria: Prescott 1860); lo de las chispas y el papel ardiendo corresponde
a otra noche o no tiene fecha fiable.

Si un tema no tiene imágenes con licencia válida o no se puede verificar bien, se cambia por otro de la misma serie y
se anota aquí.

## Grupo A — estilo actual (control)
Exactamente como los guiones publicados (p. ej. `content/scripts/005-tunguska.json`): 6-8 frases, 115-130 palabras
(40-45 s), gancho en la primera frase, 1 segmento `evidence`, 1-2 tarjetas (stat/timeline/title), final que enlaza.
Campos extra: `"experiment": "EXP01"`, `"variant": "A"`, `"remotion": false` (tarjetas Pillow de siempre).

## Grupo B — estilo mejorado
Campos extra: `"experiment": "EXP01"`, `"variant": "B"`, `"style": "cinematic"`, `"gap": 0.12`, `"music_level": 0.11`.

**Narrativa** (ver skill `shorts-director`):
- Primeros 2 s: conflicto, pregunta o hecho extraordinario dicho en ≤ 10 palabras. Sin introducción («Hoy…», «¿Sabías que…?»).
- Frases cortas (≤ 14 palabras), una idea por frase, ritmo de pregunta → pista → giro → respuesta.
- Desenlace que responde al gancho (no un final forzado). Llamada a seguir el canal SOLO si encaja de forma natural
  (máx. 1 de los 5 B, p. ej. «Aquí cada dato lleva su fuente»). Nada de «dale like».
- 30-35 s ≈ 85-100 palabras; 40-45 s ≈ 115-125 palabras.

**Visual** (cada cambio de plano aporta información):
- Al menos 1 diagrama animado nuevo: `compare` o `steps` (formatos abajo), además de stat/timeline/title si encajan.
- Mapas o diagramas de dominio público con `marker` cuando la historia tenga un lugar.
- Fotografías históricas con movimiento (`zoom`, `center`, `pan_*`) y `label` claro.
- Primer plano del vídeo con movimiento evidente y relacionado con el gancho.

### Formatos nuevos
```json
{"kind": "compare", "title": "LO QUE SE ALEJA", "items": [
  {"label": "Uña humana", "value": 4.2, "display": "≈4 cm/año"},
  {"label": "La Luna", "value": 3.8, "display": "3,8 cm/año"}], "highlight": 1, "bg": "prev"}
```
2-4 barras horizontales proporcionales a `value`; `display` es el texto que se ve; `highlight` = índice destacado.

```json
{"kind": "steps", "title": "DE LA RANA A LA PILA", "items": ["Ancas que se mueven", "Galvani: «electricidad animal»", "Volta: dos metales", "Pila de 1800"], "bg": "prev"}
```
2-4 pasos que aparecen en orden con flechas.
