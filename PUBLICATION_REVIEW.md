# Revisión previa a publicación

Fecha de preparación: 24 de noviembre de 2026.

## Incluido

- Código Python actual de `engine/` y `publisher/`.
- Guiones, comprobaciones de fuentes y recursos de contenido pequeños.
- Recursos de marca y fuentes que ya formaban parte del proyecto.
- Web estática y configuración pública de Firebase.
- Configuraciones de ejemplo desactivadas, documentación limpia y reglas de exclusión.
- Cambios locales actuales del código y contenido seguro aún no guardado en el historial original.

## Excluido

- Historial `.git` original y metadatos de Claude/Firebase.
- `publisher/client_secret.json`, `publisher/token.json` y cualquier equivalente por canal.
- Bases de datos de cola, registros de publicación y datos operativos.
- Configuraciones reales del canal con identificadores, nombres, horarios y rutas locales.
- Vídeos y audios renderizados, miniaturas de trabajo, salidas, staging, revisión, informes y cachés.
- `node_modules`, entornos virtuales, `__pycache__` y otros archivos regenerables.
- Rutas personales del equipo y documentación interna de operación.

## Comprobaciones realizadas

- Búsqueda por nombres de archivos sensibles y formatos habituales de claves, tokens y claves privadas.
- Revisión del árbol actual y de los cuatro cambios guardados del historial original.
- No se detectaron claves con formato real incrustadas en el código ni en el historial.
- Se detectaron credenciales OAuth reales en los dos archivos de autenticación esperados; ambos fueron excluidos.
- La copia se creó sin modificar la carpeta original.

## Pendiente antes de hacer público

- Confirmar los derechos de reutilización de textos, imágenes, marcas y demás recursos.
- Elegir una licencia solo después de esa revisión; por eso esta copia no incluye `LICENSE`.
- Revisar manualmente la lista de archivos y ejecutar otra comprobación de secretos justo antes de publicar.
