# Asistente de Compras · Comercial Los Samanes, C.A.

Asistente web del problema 9. Responde preguntas en español con información de
los documentos de compras y cita **documento y sección** en cada respuesta.

## Arrancar

```bash
bash ejecutar.sh          # escucha en 0.0.0.0:8501
bash ejecutar.sh 8502     # equipo 2
```

Luego abrir `http://<ip-del-spark>:8501` desde la laptop. Si la red no deja
pasar el puerto:

```bash
ssh -N -L 8501:127.0.0.1:8501 <usuario>@<ip-del-spark>
# y entrar a http://localhost:8501
```

Requiere que `llama-server` esté encendido en `http://127.0.0.1:8080/v1` con el
modelo `qwen3-coder`. El arranque indexa los 436 documentos en menos de un
segundo.

## Cómo funciona

1. **Búsqueda (`busqueda.py`).** Parte los documentos por secciones (`##`),
   indexa metadatos y texto con BM25 y aplica refuerzos por proveedor, tipo de
   documento y vigencia. Los correos se citan como «Mensaje».
2. **Redacción (`llm.py`).** Envía al modelo local solo los 8 fragmentos más
   pertinentes (no cabe todo el archivo en el contexto). El prompt obliga a
   citar `[DOC: id · sección]`, a preferir adendas y políticas vigentes, y a
   responder «No está en los documentos de compras.» cuando no hay evidencia.
3. **Validación.** El servidor comprueba que cada cita corresponda a un
   fragmento realmente recuperado y reescribe la cita con la sección exacta.
   Si la respuesta no trae ninguna fuente válida, reintenta una vez y, si
   persiste, no entrega una respuesta sin respaldo.
4. **Interfaz (`estaticos/`).** HTML, CSS y JavaScript propios, sin CDN, sin
   fuentes ni imágenes externas. Responsive para laptop y teléfono. Las fuentes
   se abren dentro de la misma página y el documento completo también.

## Evaluación para Legal

```bash
python3 evaluar.py
```

Genera `../salidas/9-evaluacion.html` y `../salidas/9-evaluacion.json` con las
12 preguntas de `preguntas_de_prueba.csv`, la respuesta del asistente, sus
fuentes, el criterio de corrección y el total de aciertos.

## Estructura

```
asistente/
├── servidor.py      # HTTP y API
├── motor.py         # recuperación + redacción
├── busqueda.py      # carga, chunking e índice BM25
├── llm.py           # cliente de llama-server y validación de citas
├── evaluar.py       # evaluación y HTML para Legal
├── ejecutar.sh
└── estaticos/
    ├── index.html
    ├── estilos.css
    └── app.js
```

Solo biblioteca estándar de Python 3. No se editan, mueven ni borran los
documentos de `documentos/`.
