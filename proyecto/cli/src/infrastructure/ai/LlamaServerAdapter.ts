import { IInferenceEngine, InferencePrompt, InferenceOutput } from '../../application/ports/IInferenceEngine.js';
import { Result } from '../../shared/types/Result.js';
import { InfrastructureError } from '../../shared/errors/DomainError.js';

export interface LlamaServerConfig {
  readonly baseUrl?: string;
  readonly modelName?: string;
  readonly timeoutMs?: number;
}

export class LlamaServerAdapter implements IInferenceEngine {
  private readonly baseUrl: string;
  private readonly modelName: string;
  private readonly timeoutMs: number;

  constructor(config?: LlamaServerConfig) {
    this.baseUrl = (config?.baseUrl || process.env.LLAMA_SERVER_URL || 'http://127.0.0.1:8080').replace(/\/+$/, '');
    this.modelName = config?.modelName || process.env.LLAMA_MODEL_NAME || 'edge-clean-copilot-q4_k_m';
    this.timeoutMs = config?.timeoutMs || 60_000;
  }

  public async complete(
    prompt: InferencePrompt
  ): Promise<Result<InferenceOutput, InfrastructureError>> {
    const startTime = Date.now();
    const endpoint = `${this.baseUrl}/v1/chat/completions`;

    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), this.timeoutMs);

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: this.modelName,
          temperature: prompt.temperature ?? 0.1,
          max_tokens: prompt.maxTokens ?? 2048,
          messages: [
            { role: 'system', content: prompt.systemPrompt },
            { role: 'user', content: prompt.userPrompt }
          ]
        }),
        signal: controller.signal
      }).finally(() => clearTimeout(timer));

      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown error body');
        return Result.fail(
          new InfrastructureError(
            `llama-server HTTP ${response.status}: ${errorText}`,
            'LLAMA_SERVER_HTTP_ERROR'
          )
        );
      }

      interface ChatCompletionResponse {
        choices?: Array<{
          message?: {
            content?: string;
          };
        }>;
        model?: string;
      }

      const json = (await response.json()) as ChatCompletionResponse;
      const text = json.choices?.[0]?.message?.content;

      if (!text) {
        return Result.fail(
          new InfrastructureError('llama-server returned an empty completion choice', 'EMPTY_COMPLETION_ERROR')
        );
      }

      return Result.ok({
        text,
        modelName: json.model || this.modelName,
        durationMs: Date.now() - startTime
      });
    } catch (error) {
      return Result.fail(
        new InfrastructureError(
          `Failed to connect to llama-server at ${endpoint}. Ensure llama-server is running.`,
          'LLAMA_CONNECTION_ERROR',
          error
        )
      );
    }
  }
}
