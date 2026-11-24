# Automatización multicanal de vídeo para YouTube

Proyecto en Python para convertir guiones JSON en vídeos, revisarlos y gestionar una cola de publicación en YouTube. La carpeta incluye un motor común y datos de ejemplo para más de un canal.

Esta es una copia de revisión preparada para GitHub. No contiene credenciales, tokens, bases de datos, vídeos renderizados, cachés, historiales locales ni rutas personales.

## Estructura

- `engine/`: voz, imágenes, música, montaje, subtítulos, control de calidad y página de revisión.
- `publisher/`: autenticación OAuth, cola, programación, subida y estadísticas.
- `content/`: guiones y comprobaciones de fuentes de ejemplo.
- `channels/`: configuración y contenido de canales adicionales.
- `brand/` y `channels/*/brand/`: recursos visuales pequeños.
- `assets/fonts/`: fuentes y sus avisos de licencia.
- `site/`: página web estática opcional.

## Preparación local

Requisitos: Python 3.11 o posterior, FFmpeg y los paquetes de `requirements.txt`.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item config.example.json config.json
```

Edita `config.json` y sustituye únicamente los valores públicos del canal. La configuración de ejemplo exige aprobación manual antes de publicar.

Para un canal adicional:

```powershell
Copy-Item channels\hidden-wonders\config.example.json channels\hidden-wonders\config.json
$env:SHORTS_CHANNEL = "hidden-wonders"
```

## Render y revisión

```powershell
python engine/build.py content/scripts/001-plaga-del-baile.json --force
python engine/review_page.py
python publisher/queue_manager.py sync
python publisher/queue_manager.py status
```

Los resultados se generan en `output/` y `review/`; ambas rutas están ignoradas por Git.

Remotion es opcional. Para utilizarlo, configura `remotion.dir` con una ruta local. Si no está disponible, pon `remotion.enabled` en `false` para usar las tarjetas generadas por Pillow.

## Conectar YouTube

1. Crea un cliente OAuth de escritorio en Google Cloud para YouTube Data API v3.
2. Guarda el archivo descargado como `publisher/client_secret.json`.
3. Ejecuta `python publisher/queue_manager.py auth`.
4. Comprueba primero con `python publisher/queue_manager.py upload --dry-run`.

`client_secret.json` y el `token.json` generado están excluidos por `.gitignore`. No los subas ni los compartas.

## Seguridad antes de publicar

- Mantén `publishing.require_approval` en `true` durante las pruebas.
- Mantén `publishing.active` en `false` para canales que todavía no deban publicar.
- Revisa `PUBLICATION_REVIEW.md` antes de crear un repositorio público.
- Ejecuta una comprobación de secretos sobre los cambios preparados antes de cada publicación.


## Licencia

El código fuente de este proyecto se distribuye bajo la licencia MIT.

Las marcas, identidades visuales, guiones, investigaciones, imágenes y demás contenidos editoriales no están incluidos en la licencia MIT. Consulta `ASSETS_AND_CONTENT.md` para conocer los detalles. Las fuentes conservan sus respectivas licencias SIL Open Font License.
