# TP 5 – Simulación de eventos discretos: Degustación H (Grupo 18 – 4K4)

## Cómo correrlo

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

Se abre solo en el navegador (http://localhost:8501).

## Archivos

| Archivo | Qué hace |
|---|---|
| `simulacion.py` | Toda la lógica: generador congruencial mixto compartido, distribuciones, integración por Euler, objetos, eventos, colas y estadísticas. No tiene interfaz. |
| `app.py` | Frontend en Streamlit: panel de parámetros, botón de simular y pestañas de resultados. |

## Cómo funciona (resumen)

1. **Un solo generador** para todas las variables: `X(i) = (1714·X(i-1) + 1221) mod 3922`, semilla 1234, `RND = X(i)/3922`.
2. Se arma el evento más próximo (el menor de todos los "próximos eventos"), se avanza el reloj y se ejecuta su lógica.
3. Cuando un invitado entra a la sala se sortea su expectativa E0 (1000 / 1500 / 2000) y el tiempo que se queda sale de integrar por Euler `dE/dt = -68 - E²/E0` desde E0 hasta E ≤ 0.
4. Se simula hasta el tiempo **X** o hasta **N = 100.000** iteraciones, lo que ocurra primero.
5. Solo se guarda el vector actual. De toda la simulación se guardan nada más las **i filas desde la hora j** y la **última fila**.

## Pestañas

- **Resultados**: las 4 respuestas que pide el enunciado con sus fórmulas, datos complementarios y parámetros usados.
- **Vector de Estado**: las i filas pedidas desde la hora j, con encabezado fijo, columnas Fila/Evento/Reloj ancladas y selección de fila. Al seleccionar una fila se ve abajo el detalle de todos los objetos en ese instante. Botón para bajar todo a Excel.
- **Última Fila**: el estado al instante X (o a la iteración N).
- **Integración Euler**: una tabla por cada valor de E0, con el T obtenido y la comparación con la solución exacta.
- **Modelo**: diagrama del sistema, variables aleatorias, tabla de rangos, eventos y colas.

## Supuestos

- El tiempo entre llegadas peatonales es **constante** (2,5 min) porque el enunciado no indica distribución; se puede cambiar desde la interfaz a exponencial negativa o uniforme.
- Las tres expectativas son **equiprobables** (1/3 cada una); las probabilidades son parámetros.
- Estacionamiento y sala sin límite de capacidad. Colas FIFO, sin abandono.
- A igual hora, primero se procesan salidas y fines de atención y después las llegadas.
