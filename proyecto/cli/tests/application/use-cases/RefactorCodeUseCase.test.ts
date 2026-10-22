import { describe, it, expect } from 'vitest';
import { RefactorCodeUseCase } from '../../../src/application/use-cases/RefactorCodeUseCase.js';
import { MockInferenceAdapter } from '../../../src/infrastructure/ai/MockInferenceAdapter.js';
import { IInferenceEngine, InferencePrompt, InferenceOutput } from '../../../src/application/ports/IInferenceEngine.js';
import { Result } from '../../../src/shared/types/Result.js';
import { ValidationError, InfrastructureError, DomainError } from '../../../src/shared/errors/DomainError.js';

describe('RefactorCodeUseCase Application Service', () => {
  describe('Happy Path (Deterministic Offline Inference)', () => {
    it('should successfully orchestrate refactoring using MockInferenceAdapter', async () => {
      // Arrange
      const mockEngine = new MockInferenceAdapter(0); // 0ms latency for ultra-fast tests
      const useCase = new RefactorCodeUseCase(mockEngine);
      const input = {
        filePath: 'src/domain/legacy/OrderManager.ts',
        fileContent: 'class OrderManager {\n  process() {\n    // coupled code\n  }\n}'
      };

      // Act
      const result = await useCase.execute(input);

      // Assert
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.filePath).toBe('src/domain/legacy/OrderManager.ts');
        expect(result.data.originalLineCount).toBe(5);
        expect(result.data.modelUsed).toBe('mock-clean-slm-v1');
        expect(result.data.refactoredCode).toContain('Clean Architecture Refactoring applied successfully');
        expect(result.data.refactoredCode).toContain('export class RefactoredEntity');
        expect(result.data.refactoredCode).toContain('export interface IEntityRepository');
        expect(result.data.durationMs).toBeGreaterThanOrEqual(0);
      }
    });

    it('should correctly measure line counts across multiline source files', async () => {
      // Arrange
      const mockEngine = new MockInferenceAdapter(0);
      const useCase = new RefactorCodeUseCase(mockEngine);
      const input = {
        filePath: 'src/app.ts',
        fileContent: 'line 1\nline 2\nline 3\nline 4\nline 5\nline 6\nline 7'
      };

      // Act
      const result = await useCase.execute(input);

      // Assert
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.originalLineCount).toBe(7);
      }
    });
  });

  describe('Domain Invariant Failure Handling', () => {
    it('should return Result.fail with ValidationError when file content is empty', async () => {
      // Arrange
      const mockEngine = new MockInferenceAdapter(0);
      const useCase = new RefactorCodeUseCase(mockEngine);
      const input = {
        filePath: 'src/empty.ts',
        fileContent: ''
      };

      // Act
      const result = await useCase.execute(input);

      // Assert
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toBeInstanceOf(ValidationError);
        expect(result.error).toBeInstanceOf(DomainError);
        expect(result.error.message).toContain('is empty');
      }
    });

    it('should return Result.fail with ValidationError when file extension is unsupported', async () => {
      // Arrange
      const mockEngine = new MockInferenceAdapter(0);
      const useCase = new RefactorCodeUseCase(mockEngine);
      const input = {
        filePath: 'scripts/deploy.py',
        fileContent: 'def run(): pass'
      };

      // Act
      const result = await useCase.execute(input);

      // Assert
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toBeInstanceOf(ValidationError);
        expect(result.error.message).toContain('Unsupported file extension');
      }
    });
  });

  describe('Infrastructure Error Propagation', () => {
    it('should return Result.fail with InfrastructureError when the inference engine port fails', async () => {
      // Arrange: Create a failing test double adapter
      const failingEngine: IInferenceEngine = {
        async complete(_prompt: InferencePrompt): Promise<Result<InferenceOutput, InfrastructureError>> {
          return Result.fail(new InfrastructureError('LLM server connection timeout', 'CONNECTION_TIMEOUT'));
        }
      };

      const useCase = new RefactorCodeUseCase(failingEngine);
      const input = {
        filePath: 'src/domain/User.ts',
        fileContent: 'export class User {}'
      };

      // Act
      const result = await useCase.execute(input);

      // Assert
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toBeInstanceOf(InfrastructureError);
        expect(result.error.message).toBe('LLM server connection timeout');
        expect(result.error.code).toBe('CONNECTION_TIMEOUT');
      }
    });
  });
});
