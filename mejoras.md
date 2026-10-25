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

## MEJ-002 · Esqueleto de la aplicación y ejecutable

- **Qué:** la aplicación arranca, muestra una ventana principal vacía y se distribuye como `pxls.exe`.
- **Por qué:** el ejecutable debe existir desde la primera versión; conviene resolver el empaquetado antes de que haya funcionalidad.
- **Dudas:** un único fichero `.exe` o carpeta con el `.exe` y sus dependencias; icono; título de la ventana.

## MEJ-003 · Modelo de color y formatos

- **Qué:** representar un color con canal alfa y convertirlo entre HEX `#RRGGBBAA`, RGB, HSL y HSV.
- **Por qué:** es el núcleo sobre el que se apoyan el cuentagotas, el selector, el portapapeles, el historial y las paletas.
- **Dudas:** ¿se aceptan también como entrada `#RRGGBB` y `#RGB`?; cómo se muestra el alfa en RGB, HSL y HSV (`rgba()`, `hsla()`, porcentaje, 0–255); redondeo de los valores mostrados.

## MEJ-004 · Cuentagotas de pantalla

- **Qué:** capturar el color de cualquier píxel de la pantalla, con una lupa para apuntar con precisión.
- **Por qué:** es la función principal de un color picker de escritorio.
- **Dudas:** cómo se activa (botón, atajo global); varios monitores y escalado de pantalla (DPI); cómo se cancela.

## MEJ-005 · Selector visual

- **Qué:** elegir un color con un cuadrado de saturación y brillo, una barra de tono y controles para el alfa y para cada componente.
- **Por qué:** permite crear colores, no sólo capturarlos.
- **Dudas:** modelo del selector (HSV es lo habitual); si los valores se pueden escribir a mano en cada formato.

## MEJ-006 · Copiar al portapapeles

- **Qué:** copiar el color actual en el formato elegido.
- **Por qué:** es como el color llega a otras herramientas.
- **Dudas:** formato por defecto; si se puede copiar en todos los formatos; atajo de teclado.

## MEJ-007 · Historial

- **Qué:** recordar los últimos colores elegidos, también entre sesiones.
- **Por qué:** recuperar un color sin tener que volver a capturarlo.
- **Dudas:** cuántos colores; si se guardan duplicados; si se puede borrar.

## MEJ-008 · Paletas de color

- **Qué:** crear, nombrar, editar y guardar paletas de colores.
- **Por qué:** organizar los colores de un proyecto.
- **Dudas:** número de paletas y de colores por paleta; reordenar colores; exportar e importar (y en qué formatos).

## MEJ-009 · `spec-anchor`: proteger también los ficheros auxiliares de los tests

- **Qué:** que las reglas de clase traten `conftest.py` y los módulos auxiliares bajo `tests/` como ficheros de test.
- **Por qué:** hoy (ANCH-025 y glosario de `specs/spec-anchor/spec.md`) sólo cuentan como ficheros de test los `test_*.py`; un `chore` podría cambiar un `conftest.py` y alterar el comportamiento de los tests sin tocar ninguna spec.
- **Dudas:** si los helpers de `tests/` deben llevar también `Spec:` como los módulos anclados.
