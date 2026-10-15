#!/usr/bin/env python3
"""Apply two consistency fixes to seed_examples.jsonl:
1. Example 2 (index 1): Replace generic Error with typed ValidationError in EmailAddress.
2. Example 2 (index 1) + Example 4 (index 3): Unify error message style to lowercase, concise.
"""

import json
from pathlib import Path

target = Path(__file__).parent / "seed_examples.jsonl"

with open(target, "r", encoding="utf-8") as f:
    lines = [json.loads(line) for line in f if line.strip()]

# Fix Example 2 (index 1): EmailAddress Value Object
lines[1]["messages"][2]["content"] = """```typescript
export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

export class EmailAddress {
  private readonly value: string;
  private static readonly EMAIL_REGEX = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;

  private constructor(email: string) {
    this.value = email;
  }

  public static create(rawEmail: string): EmailAddress {
    if (!rawEmail || rawEmail.trim().length === 0) {
      throw new ValidationError('email address cannot be empty');
    }
    const trimmed = rawEmail.trim().toLowerCase();
    if (!this.EMAIL_REGEX.test(trimmed)) {
      throw new ValidationError(`invalid email address format: ${rawEmail}`);
    }
    return new EmailAddress(trimmed);
  }

  public getValue(): string {
    return this.value;
  }

  public equals(other: EmailAddress): boolean {
    return this.value === other.value;
  }
}
```

### Why this conforms to Clean Architecture:
1. **Typed Domain Error:** Throws `ValidationError` (a typed domain error) instead of a generic `Error`, making the contract explicit for consumers.
2. **Zero External Dependencies:** Relies strictly on standard TypeScript and ECMAScript features; no `validator.js` or `zod` polluting the core domain.
3. **Immutability:** The inner value cannot be altered after creation.
4. **Always Valid:** An instance of `EmailAddress` cannot exist in an invalid state."""

# Fix Example 4 (index 3): Password - already uses ValidationError, unify message casing
# The Password messages are already lowercase/concise — they are actually fine.
# But verify the ValidationError class definition is included consistently
current = lines[3]["messages"][2]["content"]
# The ValidationError class definition is already included at the top of Example 4
# Just ensure it matches the exact same shape as Example 2
lines[3]["messages"][2]["content"] = """```typescript
export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

export class Password {
  private readonly value: string;
  private static readonly MIN_LENGTH = 8;
  private static readonly HAS_LETTER = /[a-zA-Z]/;
  private static readonly HAS_NUMBER = /[0-9]/;

  private constructor(rawPassword: string) {
    this.value = rawPassword;
  }

  public static create(rawPassword: string): Password {
    if (!rawPassword || rawPassword.trim().length === 0) {
      throw new ValidationError('password cannot be empty');
    }
    if (rawPassword.length < this.MIN_LENGTH) {
      throw new ValidationError(`password must be at least ${this.MIN_LENGTH} characters long`);
    }
    if (!this.HAS_LETTER.test(rawPassword)) {
      throw new ValidationError('password must contain at least one letter');
    }
    if (!this.HAS_NUMBER.test(rawPassword)) {
      throw new ValidationError('password must contain at least one number');
    }
    return new Password(rawPassword);
  }

  public getValue(): string {
    return this.value;
  }

  public toString(): string {
    return '[PROTECTED_PASSWORD]';
  }
}
```

### Architectural Highlights:
1. **Typed Domain Error:** Throws `ValidationError` (same typed error as `EmailAddress`) — both Value Objects share the same error contract, enabling consistent error handling in the application layer.
2. **Zero External Dependencies:** Built with pure TypeScript ECMAScript semantics without third-party validation libraries.
3. **Private Constructor:** Guarantees that an invalid `Password` cannot be instantiated in memory.
4. **Safe String Representation:** `toString()` masks the internal value to avoid leaking secrets in loggers."""

with open(target, "w", encoding="utf-8") as f:
    for item in lines:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print("Successfully applied both fixes to examples 2 and 4.")
