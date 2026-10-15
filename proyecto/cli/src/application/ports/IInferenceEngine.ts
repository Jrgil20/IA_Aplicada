import { Result } from '../../shared/types/Result.js';
import { InfrastructureError } from '../../shared/errors/DomainError.js';

export interface InferencePrompt {
  readonly systemPrompt: string;
  readonly userPrompt: string;
  readonly temperature?: number;
  readonly maxTokens?: number;
}

export interface InferenceOutput {
  readonly text: string;
  readonly modelName: string;
  readonly durationMs: number;
}

export interface IInferenceEngine {
  complete(prompt: InferencePrompt): Promise<Result<InferenceOutput, InfrastructureError>>;
}
