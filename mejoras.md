# Mejoras pendientes

Backlog de funcionalidades y mejoras **todavía no implementadas**. Este fichero no es normativo: nada de lo que aparece aquí existe en el sistema, y ni el código ni los tests pueden referenciarlo (Constitución, Artículo IV).

## Cómo se usa

- Cualquiera, persona o agente de IA, puede añadir una mejora. Un cambio que sólo toca este fichero es de clase `chore`.
- Cada mejora tiene un ID `MEJ-NNN` que nunca se reutiliza.
- El orden del fichero es el orden de prioridad.
- Para implementar una mejora, en la copia de trabajo de `dev`: requisitos en `draft` → clarificar → aprobación de la persona propietaria del producto → tests → código → y, **en el mismo commit en `dev`**, se elimina la mejora de este fichero.

### Plantilla

```markdown
## MEJ-NNN · Título

- **Qué:** lo que debería poder hacer quien use la aplicación.
- **Por qué:** el valor que aporta.
- **Dudas:** lo que habrá que clarificar al especificarla.
```

---

## MEJ-009 · `spec-anchor`: proteger también los ficheros auxiliares de los tests

- **Qué:** que las reglas de clase traten `conftest.py` y los módulos auxiliares bajo `tests/` como ficheros de test.
- **Por qué:** hoy (ANCH-025 y glosario de `specs/spec-anchor/spec.md`) sólo cuentan como ficheros de test los `test_*.py`; un `chore` podría cambiar un `conftest.py` y alterar el comportamiento de los tests sin tocar ninguna spec.
- **Dudas:** si los helpers de `tests/` deben llevar también `Spec:` como los módulos anclados.

## MEJ-010 · `spec-anchor`: mostrar el progreso de la verificación completa

- **Qué:** que la verificación completa vaya mostrando qué puerta está ejecutando (formato, tipos, tests…) y cuánto ha tardado cada una.
- **Por qué:** durante un commit el hook tarda alrededor de un minuto sin mostrar nada y parece colgado; el primer commit de la fase 2 se interrumpió con Ctrl+C por eso.
- **Dudas:** si se muestra siempre o sólo en los hooks; formato de las líneas de progreso.
