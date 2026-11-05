# Lab 3 · Preguntarle a los documentos

La misma empresa de compras, una semana después del lab 2. Compras tiene cientos de documentos con proveedores (contratos, adendas, políticas, actas y correos), y las respuestas que necesita están repartidas entre ellos.

Igual que en los labs anteriores: no hay pasos guiados, cada problema dice qué hay que entregar y qué condición tiene que cumplir, y el equipo decide cómo llegar ahí. Discutan entre los tres antes de escribirle al agente.

## Antes de empezar

1. Entra al Spark de tu equipo por SSH.
2. Copia esta carpeta en tu usuario y entra en ella.
3. Ejecuta `bash preparar.sh`.
4. Abre OpenCode con `opencode`.

## Cómo se entrega

Igual que en los labs anteriores: cada problema termina en una página HTML en `salidas/` que un jefe pueda abrir y usar en una reunión sin que nadie se la explique, y que se abra sin internet.

## Cómo abrir el asistente web

El asistente del problema 9 corre en el Spark y se abre desde el navegador de la laptop. Cada equipo usa su puerto: 8501 el equipo 1 y 8502 el equipo 2 de cada Spark.

- Directo: `http://<ip-del-spark>:8501`.
- Si la red no deja pasar ese puerto, abre un túnel desde la laptop y deja esa terminal abierta: `ssh -N -L 8501:127.0.0.1:8501 <tu-usuario>@<ip-del-spark>`. Luego entra a `http://localhost:8501`.

## Los problemas

| # | Problema |
| --- | --- |
| 8 | [Lo que dice el contrato](problemas/8-lo-que-dice-el-contrato.md) |
| 9 | [Pregúntale a compras](problemas/9-preguntale-a-compras.md) |
| 10 | [El buscador para el agente](problemas/10-el-buscador-para-el-agente.md), para quien termine el 9 |

## Qué hay en la carpeta

- `documentos/`: 436 documentos de compras, de solo lectura. Contratos y adendas, políticas, procedimientos, actas de reuniones con proveedores, evaluaciones trimestrales, fichas técnicas, listas de precios y el archivo de correos.
- `datos/pedidos_pendientes.csv`: los pedidos pendientes, exportados hoy del ERP.
- `preguntas_de_prueba.csv`: las preguntas que Legal usará para aprobar el asistente del problema 9.
- `asistente/`: carpeta vacía para el asistente web del problema 9.
- `AGENTS.md` y `CLAUDE.md`: las reglas del proyecto.
- `opencode.json`: la configuración de OpenCode del proyecto, vacía.

El modelo local lo sirve llama-server en el Spark, en `http://127.0.0.1:8080/v1`, con el formato de la API de OpenAI.

Todos los datos son ficticios.
