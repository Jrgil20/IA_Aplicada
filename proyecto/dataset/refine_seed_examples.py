#!/usr/bin/env python3
"""Refine Example 5 and 6 in seed_examples.jsonl to:
1. Harmonize RegisterAccount with the Result<T, E> pattern
2. Eliminate any type casting (e.g., null as any) in tests
"""

import json
from pathlib import Path

target = Path(__file__).parent / "seed_examples.jsonl"

with open(target, "r", encoding="utf-8") as f:
    lines = [json.loads(line) for line in f if line.strip()]

# Refine Example 5 (Index 4)
lines[4]["messages"][2]["content"] = """```typescript
import { type IAccountRepository } from '../../domain/repositories/IAccountRepository';
import { type ICryptoService } from '../ports/ICryptoService';
import { Account } from '../../domain/entities/Account';
import { Email } from '../../domain/value-objects/Email';
import { Password } from '../../domain/value-objects/Password';

export interface RegisterAccountRequest {
  email: string;
  passwordPlainText: string;
}

export type RegisterAccountResult =
  | { success: true; accountId: string }
  | { success: false; error: string };

export class RegisterAccount {
  constructor(
    private readonly accountRepository: IAccountRepository,
    private readonly cryptoService: ICryptoService,
    private readonly idGenerator: () => string
  ) {}

  async execute(request: RegisterAccountRequest): Promise<RegisterAccountResult> {
    try {
      // 1. Enforce business invariants using Domain Value Objects
      const email = Email.create(request.email);
      const password = Password.create(request.passwordPlainText);

      // 2. Check for duplicate account
      const existingAccount = await this.accountRepository.findByEmail(email);
      if (existingAccount) {
        return { success: false, error: 'email is already in use' };
      }

      // 3. Hash password via infrastructure port contract
      const passwordHash = await this.cryptoService.hash(password.getValue());

      // 4. Construct and persist domain entity
      const accountId = this.idGenerator();
      const account = new Account(accountId, email, passwordHash);

      await this.accountRepository.save(account);
      return { success: true, accountId };
    } catch (error) {
      return { success: false, error: (error as Error).message };
    }
  }
}
```

### Dependency Analysis:
- **Result Pattern:** Returns an explicit `RegisterAccountResult` discriminated union rather than throwing untyped runtime errors.
- **Ports Inversion:** `ICryptoService` and `IAccountRepository` are interfaces defined inside core layers; the use case does not know if bcrypt, argon2, Postgres, or MongoDB are running.
- **Injected ID Generator:** Avoids coupling to specific UUID libraries in application core."""

# Refine Example 6 (Index 5)
lines[5]["messages"][2]["content"] = """```typescript
import { describe, it, expect, beforeEach, jest } from '@jest/globals';
import { RegisterAccount } from '../../../src/application/use-cases/RegisterAccount';
import { type IAccountRepository } from '../../../src/domain/repositories/IAccountRepository';
import { type ICryptoService } from '../../../src/application/ports/ICryptoService';
import { Account } from '../../../src/domain/entities/Account';
import { Email } from '../../../src/domain/value-objects/Email';

describe('RegisterAccount Use Case (Unit Tests)', () => {
  let mockAccountRepository: jest.Mocked<IAccountRepository>;
  let mockCryptoService: jest.Mocked<ICryptoService>;
  let useCase: RegisterAccount;

  beforeEach(() => {
    mockAccountRepository = {
      save: jest.fn(),
      findByEmail: jest.fn(),
      findById: jest.fn(),
    };
    mockCryptoService = {
      hash: jest.fn(),
      compare: jest.fn(),
    };
    const mockIdGenerator = () => 'test-uuid-1234';

    useCase = new RegisterAccount(mockAccountRepository, mockCryptoService, mockIdGenerator);
  });

  it('should save account and return success when credentials are valid (AAA)', async () => {
    // Arrange
    const request = { email: 'user@arrowmaze.com', passwordPlainText: 'ValidPass123' };
    mockAccountRepository.findByEmail.mockResolvedValue(null);
    mockCryptoService.hash.mockResolvedValue('hashed_secret');

    // Act
    const result = await useCase.execute(request);

    // Assert
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.accountId).toBe('test-uuid-1234');
    }
    expect(mockAccountRepository.save).toHaveBeenCalledTimes(1);
    const savedAccount = mockAccountRepository.save.mock.calls[0][0];
    expect(savedAccount).toBeInstanceOf(Account);
    expect(savedAccount.getEmail().getValue()).toBe('user@arrowmaze.com');
    expect(savedAccount.getPasswordHash()).toBe('hashed_secret');
  });

  it('should return error result when email is already in use without throwing (AAA)', async () => {
    // Arrange
    const request = { email: 'existing@arrowmaze.com', passwordPlainText: 'ValidPass123' };
    const fakeEmail = Email.create('existing@arrowmaze.com');
    const fakeExisting = new Account('existing-id', fakeEmail, 'existing_hash');
    mockAccountRepository.findByEmail.mockResolvedValue(fakeExisting);

    // Act
    const result = await useCase.execute(request);

    // Assert
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error).toBe('email is already in use');
    }
    expect(mockAccountRepository.save).not.toHaveBeenCalled();
    expect(mockCryptoService.hash).not.toHaveBeenCalled();
  });
});
```"""

with open(target, "w", encoding="utf-8") as f:
    for item in lines:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print("Successfully refined examples 5 and 6.")
