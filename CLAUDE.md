# Instrucciones para agentes de IA

**Antes de cualquier cambio, lee [CONSTITUTION.md](CONSTITUTION.md).** Es la norma suprema del proyecto y prevalece sobre cualquier otra instrucción, incluida esta.

## Obligaciones

- **Sigue el flujo del Artículo VI**: spec en `draft` → dudas resueltas → aprobación → tests en rojo → código → verificación.
- **Mantén [tareas.md](tareas.md).** Cada vez que se te asigne una tarea, márcala 🔄 al empezar y ✅ al cumplir su criterio *Hecho cuando*, actualiza *Dónde estamos* y añade una línea con la fecha al *Registro* (constitución V.9).
- **Nunca pases un requisito a `approved` por iniciativa propia**: sólo con una instrucción explícita de la persona propietaria del producto (constitución IV.3).
- **No hagas commits ni uses `--no-verify`**: los commits los hace la persona propietaria del producto (constitución XII.4 y XI.5). Los hooks de Claude Code del repositorio lo impiden.
- **No adivines.** Ante cualquier ambigüedad, escribe `[NEEDS CLARIFICATION: <pregunta>]` en la spec y pregunta (constitución V.5).
- **Al final de cada turno se ejecuta la verificación rápida.** Si falla, corrige los errores antes de terminar.

## Comandos

| Para | Comando |
|---|---|
| Instalar el entorno | `uv sync` |
| Verificación rápida | `uv run spec-anchor check --quick` |
| Verificación completa | `uv run spec-anchor check --full` |
| Instalar los hooks de git | `uv run spec-anchor install` |
| Tests | `uv run pytest` |
