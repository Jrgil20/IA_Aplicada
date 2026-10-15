import { SourceFile } from '../../domain/entities/SourceFile.js';
import { IInferenceEngine } from '../ports/IInferenceEngine.js';
import { RefactorInputDTO, RefactorOutputDTO } from '../dtos/RefactorDTO.js';
import { Result } from '../../shared/types/Result.js';
import { DomainError, InfrastructureError } from '../../shared/errors/DomainError.js';

export class RefactorCodeUseCase {
  private static readonly SYSTEM_PROMPT =
    'You are Edge Clean Copilot, an expert software architect specialized in Clean Architecture, ' +
    'Domain-Driven Design (DDD), and SOLID principles. You strictly enforce the Dependency Rule: ' +
    'domain and application layers must never depend on external libraries, frameworks, databases, or infrastructure.';

  constructor(private readonly inferenceEngine: IInferenceEngine) {}

  public async execute(
    dto: RefactorInputDTO
  ): Promise<Result<RefactorOutputDTO, DomainError | InfrastructureError>> {
    try {
      const sourceFile = SourceFile.create({
        filePath: dto.filePath,
        content: dto.fileContent
      });

      const userPrompt =
        `Refactor the following ${sourceFile.language} code to adhere strictly to Clean Architecture ` +
        `and Ports & Adapters:\n\n` +
        `\`\`\`${sourceFile.language}\n` +
        `${sourceFile.content}\n` +
        `\`\`\``;

      const inferenceResult = await this.inferenceEngine.complete({
        systemPrompt: RefactorCodeUseCase.SYSTEM_PROMPT,
        userPrompt,
        temperature: 0.1,
        maxTokens: 2048
      });

      if (!inferenceResult.success) {
        return Result.fail(inferenceResult.error);
      }

      const output: RefactorOutputDTO = {
        filePath: sourceFile.filePath,
        originalLineCount: sourceFile.lineCount,
        refactoredCode: inferenceResult.data.text,
        modelUsed: inferenceResult.data.modelName,
        durationMs: inferenceResult.data.durationMs
      };

      return Result.ok(output);
    } catch (error) {
      if (error instanceof DomainError) {
        return Result.fail(error);
      }
      return Result.fail(
        new InfrastructureError('Unexpected error during refactoring use case', 'UNEXPECTED_ERROR', error)
      );
    }
  }
}
