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
   fragmento realmente recuperado y reescribe la cita con la sección exacta
   (acepta `[DOC: …]` y `[FRAGMENTO n]`). Además verifica que toda cifra de la
   respuesta aparezca en las fuentes citadas; si no, pide corregir y, si
   insiste, elimina la frase sin respaldo. Si no hay ninguna fuente válida, no
   entrega una respuesta sin respaldo.
4. **Interfaz (`estaticos/`).** HTML, CSS y JavaScript propios, sin CDN, sin
   fuentes ni imágenes externas. Responsive para laptop y teléfono. Las fuentes
   se abren dentro de la misma página y el documento completo también, con el
   Markdown renderizado como vista previa (títulos, listas, tablas y citas).

## Seguridad y límites

- **Sin fuente no hay respuesta.** Si el modelo no cita un fragmento válido, el
  servidor devuelve una negativa fija; nunca devuelve texto del modelo sin
  respaldo. Las cifras y correos de la respuesta deben aparecer en la fuente
  citada; las cifras de la pregunta solo se aceptan en oraciones negativas.
- **Inyección.** Se eliminan etiquetas de delimitación y se rechazan las
  instrucciones de rol más comunes (`ignora las instrucciones`, `a partir de
  ahora...`, `responde solo`, cierres de `</user_query>`, etc.). Es una capa,
  no una defensa completa: el modelo local sigue siendo el último filtro.
- **Límites.** 30 solicitudes por minuto por IP y 4 consultas concurrentes como
  máximo. El cuerpo se limita a 20.000 bytes y la pregunta a 1.000 caracteres.
  Solo se acepta `Content-Type: application/json`.
- **Autenticación opcional.** Para entornos compartidos, definir
  `ASISTENTE_USUARIO` y `ASISTENTE_CLAVE`; el navegador pedirá autenticación
  básica. Sin esas variables, el asistente queda abierto como en el laboratorio.
  En producción, además, conviene un proxy/ACL de red, porque la autenticación
  básica viaja sobre HTTP.
- **Bind.** `ASISTENTE_HOST` (o `--host`) permite escuchar solo en una interfaz
  interna; por defecto se mantiene `0.0.0.0` para el acceso desde las laptops.
- **Evaluación preliminar.** `evaluar.py` exige fuente para las respuestas
  positivas y detecta negaciones, pero sigue siendo una comprobación automática:
  Legal debe revisar las fuentes y el texto.
- **Pruebas de seguridad.** `python3 asistente/probar_seguridad.py` ejecuta las
  pruebas de inyección, cifras/correos y evaluador sin llamar al modelo.

## Evaluación para Legal

```bash
python3 evaluar.py
```

Genera `../salidas/9-evaluacion.html` y `../salidas/9-evaluacion.json` con las
12 preguntas de `preguntas_de_prueba.csv`, la respuesta del asistente, sus
fuentes, el criterio de corrección y el total de aciertos.

## Buscador MCP (problema 10)

`servidor_mcp.py` expone el mismo índice BM25 como servidor MCP por stdio. El
agente conectado a `buscador` solo ve los documentos a través de dos
herramientas y no abre archivos de `documentos/` por su cuenta.

```bash
# Prueba del protocolo
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \
  | python3 asistente/servidor_mcp.py

# Comparación Modo A (archivos directos) vs Modo B (MCP)
python3 scripts/comparar_busqueda.py
```

Herramientas: `buscar_documentos(consulta, limite=5)` y
`leer_fragmento(documento_id, seccion)`. La configuración está en
`opencode.json`: el agente `agente-mcp` tiene una lista blanca con solo esas dos
herramientas y todo lo demás denegado (`read`, `glob`, `grep`, `shell`,
`subagent`, `webfetch`, `websearch`). Las pruebas de la condición de TI se
ejecutan con:

```bash
python3 scripts/probar_condicion_ti.py   # deja salidas/10-condicion-ti.json
```

El informe para TI queda en `salidas/10-comparacion.html`.

## Estructura

```
asistente/
├── servidor.py      # HTTP y API
├── servidor_mcp.py  # buscador documental como servidor MCP (stdio)
├── motor.py         # recuperación + redacción
├── busqueda.py      # carga, chunking e índice BM25
├── llm.py           # cliente de llama-server y validación de citas
├── evaluar.py       # evaluación y HTML para Legal
├── ejecutar.sh
└── estaticos/
    ├── index.html
    ├── estilos.css
    ├── markdown.js
    └── app.js
```

Solo biblioteca estándar de Python 3. No se editan, mueven ni borran los
documentos de `documentos/`.
