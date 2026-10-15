#!/usr/bin/env python3
"""Dataset Validator for Edge Clean Copilot

Validates JSONL dataset format, ChatML message structure, and token approximations
prior to LoRA fine-tuning on DGX Spark.
"""

import json
import sys
from pathlib import Path

REQUIRED_ROLES = ["system", "user", "assistant"]

def validate_dataset(file_path: Path) -> bool:
    print(f"--> Validating dataset: {file_path}")
    if not file_path.exists():
        print(f"Error: File '{file_path}' does not exist.", file=sys.stderr)
        return False

    valid_count = 0
    total_tokens_approx = 0

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError as err:
                print(f"Line {line_num}: Invalid JSON - {err}", file=sys.stderr)
                return False

            if "messages" not in data or not isinstance(data["messages"], list):
                print(f"Line {line_num}: Missing or invalid 'messages' array.", file=sys.stderr)
                return False

            messages = data["messages"]
            roles_found = [m.get("role") for m in messages if isinstance(m, dict)]

            for role in REQUIRED_ROLES:
                if role not in roles_found:
                    print(f"Line {line_num}: Missing required role '{role}'.", file=sys.stderr)
                    return False

            for msg_idx, msg in enumerate(messages):
                content = msg.get("content", "")
                if not isinstance(content, str) or not content.strip():
                    print(f"Line {line_num}, message {msg_idx}: Empty content for role '{msg.get('role')}'.", file=sys.stderr)
                    return False
                # Rough token estimation (~4 chars/token)
                total_tokens_approx += len(content) // 4

            valid_count += 1

    print(f"[OK] Successfully validated {valid_count} sample(s).")
    print(f"     Approximate total tokens: ~{total_tokens_approx:,}")
    return True

if __name__ == "__main__":
    target = Path(__file__).parent / "seed_examples.jsonl"
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
    
    success = validate_dataset(target)
    sys.exit(0 if success else 1)
