import { IInferenceEngine, InferencePrompt, InferenceOutput } from '../../application/ports/IInferenceEngine.js';
import { Result } from '../../shared/types/Result.js';
import { InfrastructureError } from '../../shared/errors/DomainError.js';

export class MockInferenceAdapter implements IInferenceEngine {
  constructor(private readonly mockLatencyMs: number = 25) {}

  public async complete(
    _prompt: InferencePrompt
  ): Promise<Result<InferenceOutput, InfrastructureError>> {
    const startTime = Date.now();

    if (this.mockLatencyMs > 0) {
      await new Promise((resolve) => setTimeout(resolve, this.mockLatencyMs));
    }

    const mockResponse =
      `// [Edge Clean Copilot - Mock Engine Output]\n` +
      `// Clean Architecture Refactoring applied successfully.\n\n` +
      `// 1. Domain Layer: Pure entity with zero external dependencies\n` +
      `export class RefactoredEntity {\n` +
      `  constructor(public readonly id: string, public readonly status: string) {}\n` +
      `}\n\n` +
      `// 2. Application Layer: Port contract\n` +
      `export interface IEntityRepository {\n` +
      `  save(entity: RefactoredEntity): Promise<void>;\n` +
      `}\n\n` +
      `// 3. Application Layer: Use Case\n` +
      `export class ProcessEntityUseCase {\n` +
      `  constructor(private readonly repository: IEntityRepository) {}\n` +
      `  async execute(id: string): Promise<RefactoredEntity> {\n` +
      `    const entity = new RefactoredEntity(id, 'PROCESSED');\n` +
      `    await this.repository.save(entity);\n` +
      `    return entity;\n` +
      `  }\n` +
      `}`;

    return Result.ok({
      text: mockResponse,
      modelName: 'mock-clean-slm-v1',
      durationMs: Date.now() - startTime
    });
  }
}
