#!/usr/bin/env python3
"""
classify_tickets.py
Classify support tickets from tickets_tramontana.csv using local llama-server.
Compatible with standard library (no pip dependencies required).
"""

import csv
import json
import re
import urllib.request
import urllib.error
from collections import Counter

API_URL = "http://localhost:8080/v1/chat/completions"
CSV_FILE = "tickets_tramontana.csv"
OUTPUT_FILE = "tickets_clasificados.json"

SYSTEM_PROMPT = (
    "You are a specialized support ticket classifier for an enterprise logistics platform.\n"
    "You must analyze the incoming support ticket and return ONLY valid JSON matching this schema:\n"
    "{\n"
    '  "categoria": "facturacion" | "tecnico" | "ventas" | "otro",\n'
    '  "urgencia": "baja" | "media" | "alta",\n'
    '  "resumen": "A concise one-sentence summary in Spanish"\n'
    "}\n"
    "Do NOT include markdown formatting, backticks, thoughts, or any surrounding text. Return ONLY raw JSON."
)

VALID_CATEGORIAS = {"facturacion", "tecnico", "ventas", "otro"}
VALID_URGENCIAS = {"baja", "media", "alta"}
URGENCY_ORDER = {"alta": 0, "media": 1, "baja": 2, "sin_clasificar": 3}


def normalize_text(text: str) -> str:
    """Normalize text for duplicate detection."""
    if not text:
        return ""
    # remove punctuation and extra spaces, lowercase
    cleaned = re.sub(r"[^\w\s]", "", text).lower().strip()
    return re.sub(r"\s+", " ", cleaned)


def call_llm(ticket_id: str, cliente: str, asunto: str, canal: str, desc: str) -> dict:
    """Send ticket to local llama-server via OpenAI-compatible endpoint."""
    user_prompt = (
        f"Nº Ticket: {ticket_id}\n"
        f"Cliente: {cliente}\n"
        f"Asunto: {asunto}\n"
        f"Canal: {canal}\n"
        f"Descripción: {desc}\n\n"
        "Return classification JSON."
    )

    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 200,
        "stream": False
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer no-key-required"
    }

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"].strip()

            # Strip markdown code blocks if the model wrapped them
            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\s*", "", content)
                content = re.sub(r"\s*```$", "", content)

            parsed = json.loads(content)
            cat = str(parsed.get("categoria", "")).lower().strip()
            urg = str(parsed.get("urgencia", "")).lower().strip()
            res = str(parsed.get("resumen", "")).strip()

            return {
                "categoria": cat if cat in VALID_CATEGORIAS else "sin_clasificar",
                "urgencia": urg if urg in VALID_URGENCIAS else "sin_clasificar",
                "resumen": res if res else asunto
            }

    except Exception as e:
        # Graceful fallback without crashing
        return {
            "categoria": "sin_clasificar",
            "urgencia": "sin_clasificar",
            "resumen": f"Error: {str(e)[:60]}"
        }


def main():
    print(f"[*] Reading tickets from {CSV_FILE}...")
    tickets = []
    with open(CSV_FILE, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            tickets.append(row)

    total_tickets = len(tickets)
    print(f"[*] Total tickets loaded: {total_tickets}")

    # Duplicate detection rule:
    # Only non-empty descriptions can form duplicate groups.
    # Empty descriptions are NOT duplicates of each other.
    seen_texts = {}
    duplicate_flags = []

    for item in tickets:
        raw_desc = (item.get("Descripción del problema") or "").strip()
        norm_desc = normalize_text(raw_desc)

        if not norm_desc or len(norm_desc) < 10:
            # If description is empty or too short, do not consider duplicate
            duplicate_flags.append(False)
        else:
            if norm_desc in seen_texts:
                duplicate_flags.append(True)
            else:
                seen_texts[norm_desc] = True
                duplicate_flags.append(False)

    total_dups = sum(1 for d in duplicate_flags if d)
    print(f"[*] Duplicate tickets identified: {total_dups}")

    # Process and classify
    classified_records = []
    print("[*] Classifying tickets via local LLM...")

    for idx, (row, is_dup) in enumerate(zip(tickets, duplicate_flags), start=1):
        ticket_id = (row.get("Nº Ticket") or "").strip()
        cliente = (row.get("Cliente") or "").strip()
        asunto = (row.get("Asunto") or "").strip()
        canal = (row.get("Canal") or "").strip()
        raw_desc = (row.get("Descripción del problema") or "").strip()

        effective_desc = raw_desc if raw_desc else f"(Sin descripción - Asunto: {asunto})"

        print(f"  [{idx:02d}/{total_tickets}] Processing {ticket_id} ({cliente[:20]})...", end="\r")
        result = call_llm(ticket_id, cliente, asunto, canal, effective_desc)

        record = {
            "ticket_id": ticket_id,
            "cliente": cliente,
            "asunto": asunto,
            "canal": canal,
            "fecha": (row.get("Fecha de creación") or "").strip(),
            "estado": (row.get("Estado") or "").strip(),
            "agente": (row.get("Agente") or "").strip(),
            "es_duplicado": is_dup,
            "categoria": result["categoria"],
            "urgencia": result["urgencia"],
            "resumen": result["resumen"]
        }
        classified_records.append(record)

    print("\n[*] Sorting queue by urgency (alta > media > baja > sin_clasificar)...")
    classified_records.sort(key=lambda x: URGENCY_ORDER.get(x["urgencia"], 99))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(classified_records, f, ensure_ascii=False, indent=2)

    print(f"[✔] Successfully saved output to {OUTPUT_FILE}")

    # Summary report
    urgencias = Counter(item["urgencia"] for item in classified_records)
    categorias = Counter(item["categoria"] for item in classified_records)

    print("\n" + "=" * 45)
    print("RESUMEN DE CLASIFICACIÓN")
    print("=" * 45)
    print("Por Urgencia:")
    for k, v in urgencias.items():
        print(f"  - {k:<15}: {v}")
    print("\nPor Categoría:")
    for k, v in categorias.items():
        print(f"  - {k:<15}: {v}")
    print(f"\nDuplicados detectados: {total_dups}")
    print("=" * 45)


if __name__ == "__main__":
    main()
