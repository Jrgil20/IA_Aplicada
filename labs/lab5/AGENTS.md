# Reglas del proyecto (lab 3)

- Los datos son ficticios. La empresa es Comercial Los Samanes, C.A. Para cualquier cálculo de fechas, hoy es 2026-11-05.
- Un pedido lleva atraso cuando está Pendiente y hoy supera su fecha_comprometida. Los días de atraso son días calendario desde la fecha_comprometida hasta hoy.
- Los documentos de compras están en documentos/. Son de solo lectura: no se editan, no se mueven y no se borran.
- El modelo local lo sirve llama-server en http://127.0.0.1:8080/v1, con el formato de la API de OpenAI y el modelo qwen3-coder.
- Los programas usan solo la biblioteca estándar de Python 3. No instales paquetes.
- Las páginas y aplicaciones web no cargan nada de internet: ni fuentes, ni librerías, ni imágenes externas.
- El asistente web escucha en 0.0.0.0, en el puerto del equipo: 8501 para el equipo 1 y 8502 para el equipo 2 de cada Spark.
- Los entregables van en la carpeta salidas/.
- No envíes correos ni publiques nada.
