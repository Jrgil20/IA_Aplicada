# Prompts para OpenCode — Lab 1: Mesa de Soporte

Instrucciones para interactuar con **OpenCode** conectado a `Qwen3-Coder-30B-A3B-Instruct` en la DGX Spark.

---

## 1. Prompt Principal para OpenCode (Generación de `classify_tickets.py`)

Copia y pega este prompt directamente en OpenCode:

```markdown
Write a complete, robust Python script named `classify_tickets.py` to classify support tickets from `tickets_tramontana.csv` using a local LLM server running on `http://localhost:8080/v1`.

### Data Details
- Input file: `tickets_tramontana.csv`
- Columns: `Cliente`, `Asunto`, `Nº Ticket`, `Fecha de creación`, `Canal`, `Descripción del problema`, `Estado`, `Agente`.
- Edge cases in data:
  1. Missing descriptions: some rows have empty "Descripción del problema"; use the "Asunto" column instead.
  2. Language: some tickets are in English.
  3. Dirty formats: ticket IDs formatted in different ways (e.g., `#0002`, `tk14`, `TK-0032`), dates in varied formats.
  4. Duplicates: duplicate requests exist across different clients or agents.

### Functional Requirements
1. Standard libraries only (`csv`, `json`, `urllib.request` or `http.client`) so it runs without extra pip dependencies.
2. Read all 85 tickets from `tickets_tramontana.csv`.
3. Detect duplicate descriptions (normalize text by trimming and lowercasing) and flag `es_duplicado: true/false`.
4. For each ticket, send a prompt to `http://localhost:8080/v1/chat/completions` using the local model.
5. The LLM must return ONLY a raw JSON object with:
   - "categoria": one of ["facturacion", "tecnico", "ventas", "otro"]
   - "urgencia": one of ["baja", "media", "alta"]
   - "resumen": a single concise sentence summarizing the issue.
6. Error handling: If parsing fails or the LLM call times out, do NOT crash. Fall back gracefully to `categoria: "sin_clasificar"` and `urgencia: "sin_clasificar"`.
7. Output: Save the full enriched list ordered with highest urgency first ("alta" > "media" > "baja" > "sin_clasificar") into `tickets_clasificados.json`.
8. Print a clean summary table to stdout with counts per category and urgency, plus duplicates detected.
```

---

## 2. System Prompt & User Prompt Templates (Embedded in the Script)

Si necesitas afinar cómo el script llama a `llama-server`, estas son las instrucciones recomendadas para el modelo:

### System Message
```text
You are a specialized support ticket classifier for an enterprise logistics platform.
You must analyze the incoming support ticket and return ONLY valid JSON matching this schema:
{
  "categoria": "facturacion" | "tecnico" | "ventas" | "otro",
  "urgencia": "baja" | "media" | "alta",
  "resumen": "One-sentence summary"
}
Do not include markdown fences, thoughts, or explanatory text. Return strictly the JSON object.
```

### User Message Format
```text
Ticket ID: {ticket_id}
Client: {cliente}
Subject: {asunto}
Channel: {canal}
Description: {descripcion or asunto}

Classify category and urgency. Provide a one-sentence summary.
```
