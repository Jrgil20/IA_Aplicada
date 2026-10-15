#!/usr/bin/env python3
"""Synthetic Clean Architecture Dataset Generator using Qwen3-Coder-30B Teacher Model.

Queries llama-server on DGX Spark via local/forwarded endpoint (http://127.0.0.1:8080/v1)
and generates validated ChatML pairs bounded by a configurable time limit (e.g. 5 minutes).
"""

import argparse
import json
import sys
import time
from pathlib import Path
import urllib.request
import urllib.error

DOMAIN_PROMPTS = [
    {
        "category": "ARCH_REFACTOR",
        "prompt": "Refactor this coupled FastAPI route with direct SQLAlchemy queries into Clean Architecture with Domain Entity, Repository Port, and Use Case:\n\n```python\n@app.post('/billing/invoices')\ndef create_invoice(data: dict, db: Session = Depends(get_db)):\n    if data['amount'] <= 0:\n        raise HTTPException(400, 'Invalid amount')\n    inv = Invoice(customer_id=data['customer_id'], amount=data['amount'], status='UNPAID')\n    db.add(inv)\n    db.commit()\n    stripe.Charge.create(amount=int(data['amount']*100), currency='usd', customer=data['stripe_id'])\n    return {'invoice_id': inv.id, 'status': 'UNPAID'}\n```"
    },
    {
        "category": "USE_CASE_GEN",
        "prompt": "Write a pure Domain Entity `Subscription` and a Use Case `CancelSubscriptionUseCase` in TypeScript that validates invariant rules (cannot cancel already expired subscription) and returns a Result<T, E> type."
    },
    {
        "category": "AAA_TEST_GEN",
        "prompt": "Write an isolated AAA (Arrange-Act-Assert) unit test in TypeScript for `CancelSubscriptionUseCase` using an in-memory mock repository and verifying domain event publication."
    },
    {
        "category": "USE_CASE_GEN",
        "prompt": "Implement a pure Value Object `Money` in TypeScript that handles amount and currency, enforces positive values, and provides an `add(other: Money): Money` method with currency check."
    },
    {
        "category": "PORT_ADAPTER",
        "prompt": "Design an application Port `IPaymentGateway` and an infrastructure Adapter `StripePaymentAdapter` in TypeScript conforming to Clean Architecture principles."
    },
    {
        "category": "ARCH_REFACTOR",
        "prompt": "Refactor this Express route that mixes database queries and third-party email sending into Clean Architecture with `RegisterUserUseCase`, `IUserRepository`, and `IEmailService` port:\n\n```typescript\napp.post('/users', async (req, res) => {\n  const { email, password } = req.body;\n  if (!email.includes('@')) return res.status(400).send('Invalid email');\n  const exists = await db.query('SELECT id FROM users WHERE email = $1', [email]);\n  if (exists.rows.length > 0) return res.status(409).send('User exists');\n  const hash = await bcrypt.hash(password, 10);\n  const user = await db.query('INSERT INTO users(email, password) VALUES($1, $2) RETURNING id', [email, hash]);\n  await sendgrid.send({ to: email, subject: 'Welcome' });\n  res.status(201).json({ id: user.rows[0].id });\n});\n```"
    },
    {
        "category": "USE_CASE_GEN",
        "prompt": "Implement a pure Value Object `Email` in TypeScript with invariant validation (valid format, non-empty, lowercase normalization) returning a `Result<Email, ValidationError>`."
    },
    {
        "category": "AAA_TEST_GEN",
        "prompt": "Write an isolated AAA (Arrange-Act-Assert) unit test in TypeScript for `RegisterUserUseCase` using an in-memory mock repository, testing the failure case when the user email already exists."
    },
    {
        "category": "SOLID_CRITIQUE",
        "prompt": "Critique this TypeScript class from the perspective of SOLID principles (especially SRP and DIP) and provide the refactored Clean Architecture structure:\n\n```typescript\nclass OrderManager {\n  async processOrder(orderData: any) {\n    // 1. Validate data\n    if (!orderData.items || orderData.items.length === 0) throw new Error('Empty');\n    // 2. Calculate tax\n    const tax = orderData.total * 0.16;\n    // 3. Save to MongoDB directly\n    await mongoose.connection.collection('orders').insertOne({ ...orderData, tax });\n    // 4. Send Slack notification\n    await axios.post('https://hooks.slack.com/...', { text: `New order: ${orderData.id}` });\n  }\n}\n```"
    },
    {
        "category": "PORT_ADAPTER",
        "prompt": "Define a Domain Port `IEventPublisher` with an `IDomainEvent` interface, and implement an in-memory test double adapter `InMemoryEventPublisher` in TypeScript."
    },
    {
        "category": "USE_CASE_GEN",
        "prompt": "Write a Use Case `ChangePasswordUseCase` in TypeScript with `IUserRepository` and `IPasswordHasher` ports, enforcing business rules (new password cannot equal old password) and returning a `Result<void, DomainError>`."
    },
    {
        "category": "ARCH_REFACTOR",
        "prompt": "Explain and refactor an Active Record model where domain business rules are tightly coupled inside an ORM model lifecycle hook (`before_save`), separating the pure domain invariants from persistence."
    }
]

SYSTEM_PROMPT = (
    "You are Edge Clean Copilot, an expert software architect specialized in Clean Architecture, "
    "Domain-Driven Design (DDD), and SOLID principles. You strictly enforce the Dependency Rule: "
    "domain and application layers must never depend on external libraries, frameworks, databases, or infrastructure. "
    "Always use the Result<T, E> pattern for use cases and typed domain errors. "
    "NEVER use the TypeScript `any` type under any circumstances. Always use strict interfaces, dedicated types, "
    "or `unknown` with type guards."
)

def parse_args():
    parser = argparse.ArgumentParser(description="Generate Clean Architecture dataset using teacher model.")
    parser.add_argument("--url", type=str, default="http://127.0.0.1:8080/v1/chat/completions", help="Endpoint URL.")
    parser.add_argument("--output", type=str, default=str(Path(__file__).parent / "generated_examples.jsonl"), help="Output JSONL path.")
    parser.add_argument("--max-time-minutes", type=float, default=5.0, help="Maximum generation time in minutes (default: 5.0).")
    return parser.parse_args()

def query_teacher(url: str, user_prompt: str) -> str:
    payload = {
        "model": "qwen3-coder",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 1024,
        "temperature": 0.2
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res["choices"][0]["message"]["content"]

def main():
    args = parse_args()
    print("=" * 60)
    print("Edge Clean Copilot — Teacher Dataset Generator")
    print(f"Teacher Endpoint: {args.url}")
    print(f"Output File:      {args.output}")
    print(f"Time Limit Flag:  {args.max_time_minutes} minute(s)")
    print("=" * 60)

    start_time = time.time()
    max_duration_seconds = args.max_time_minutes * 60
    output_path = Path(args.output)

    idx = 0
    generated_count = 0

    while (time.time() - start_time) < max_duration_seconds:
        prompt_item = DOMAIN_PROMPTS[idx % len(DOMAIN_PROMPTS)]
        idx += 1
        elapsed = (time.time() - start_time) / 60
        print(f"\n[{elapsed:.1f}m / {args.max_time_minutes}m] Generating sample #{generated_count + 1} ({prompt_item['category']})...")

        try:
            assistant_response = query_teacher(args.url, prompt_item["prompt"])
            sample = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_item["prompt"]},
                    {"role": "assistant", "content": assistant_response}
                ]
            }

            with open(output_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")

            generated_count += 1
            print(f"  --> Saved sample #{generated_count} (~{len(assistant_response)} chars).")
        except Exception as e:
            print(f"  [ERROR] Request failed: {e}", file=sys.stderr)
            time.sleep(2)

    total_time = (time.time() - start_time) / 60
    print(f"\n[TIME LIMIT REACHED] Finished after {total_time:.2f} minute(s).")
    print(f"Total new samples generated: {generated_count}")

if __name__ == "__main__":
    main()
