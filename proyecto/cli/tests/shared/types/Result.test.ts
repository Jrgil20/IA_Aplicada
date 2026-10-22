import { describe, it, expect } from 'vitest';
import { Result } from '../../../src/shared/types/Result.js';
import { DomainError, ValidationError } from '../../../src/shared/errors/DomainError.js';

describe('Result<T, E> Functional Primitive', () => {
  describe('Result.ok', () => {
    it('should create a successful result containing the provided data', () => {
      // Arrange
      const payload = { id: 'file-123', lines: 42 };

      // Act
      const result = Result.ok(payload);

      // Assert
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual(payload);
        expect(result.data.id).toBe('file-123');
        expect(result.data.lines).toBe(42);
      }
    });

    it('should allow boolean and primitive values as payload', () => {
      // Arrange & Act
      const boolResult = Result.ok(true);
      const stringResult = Result.ok('clean architecture');

      // Assert
      expect(boolResult.success).toBe(true);
      if (boolResult.success) {
        expect(boolResult.data).toBe(true);
      }

      expect(stringResult.success).toBe(true);
      if (stringResult.success) {
        expect(stringResult.data).toBe('clean architecture');
      }
    });
  });

  describe('Result.fail', () => {
    it('should create a failure result containing a typed DomainError', () => {
      // Arrange
      const error = new DomainError('Business rule violation', 'RULE_VIOLATION');

      // Act
      const result = Result.fail(error);

      // Assert
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toBeInstanceOf(DomainError);
        expect(result.error.message).toBe('Business rule violation');
        expect(result.error.code).toBe('RULE_VIOLATION');
      }
    });

    it('should preserve specialized error subclasses like ValidationError', () => {
      // Arrange
      const validationError = new ValidationError('Invalid syntax');

      // Act
      const result = Result.fail(validationError);

      // Assert
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toBeInstanceOf(ValidationError);
        expect(result.error).toBeInstanceOf(DomainError);
        expect(result.error.code).toBe('VALIDATION_ERROR');
      }
    });
  });
});
