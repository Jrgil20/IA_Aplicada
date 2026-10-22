import { describe, it, expect, vi, afterEach } from 'vitest';
import { LlamaServerAdapter } from '../../../src/infrastructure/ai/LlamaServerAdapter.js';
import { InfrastructureError } from '../../../src/shared/errors/DomainError.js';

describe('LlamaServerAdapter Infrastructure Adapter', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Defensive Endpoint Normalization', () => {
    it('should normalize bare host and port to canonical /v1/chat/completions', () => {
      const adapter = new LlamaServerAdapter({ baseUrl: 'http://192.168.6.35:8085' });
      expect(adapter.endpoint).toBe('http://192.168.6.35:8085/v1/chat/completions');
    });

    it('should strip trailing slashes before normalizing', () => {
      const adapter = new LlamaServerAdapter({ baseUrl: 'http://192.168.6.35:8085///' });
      expect(adapter.endpoint).toBe('http://192.168.6.35:8085/v1/chat/completions');
    });

    it('should append only /chat/completions if caller passes a /v1 URL', () => {
      const adapter = new LlamaServerAdapter({ baseUrl: 'http://192.168.6.35:8085/v1' });
      expect(adapter.endpoint).toBe('http://192.168.6.35:8085/v1/chat/completions');
    });

    it('should not duplicate path if caller passes full /v1/chat/completions URL', () => {
      const adapter = new LlamaServerAdapter({ baseUrl: 'http://192.168.6.35:8085/v1/chat/completions' });
      expect(adapter.endpoint).toBe('http://192.168.6.35:8085/v1/chat/completions');
    });
  });

  describe('ChatML Request & Response Parsing', () => {
    it('should format ChatML payload correctly and return Result.ok on HTTP 200', async () => {
      // Arrange
      const mockResponseBody = {
        id: 'chatcmpl-test',
        choices: [
          {
            index: 0,
            message: {
              role: 'assistant',
              content: 'export class CleanEntity {}'
            }
          }
        ]
      };

      const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponseBody
      } as unknown as Response);

      const adapter = new LlamaServerAdapter({
        baseUrl: 'http://127.0.0.1:8080',
        modelName: 'qwen3-coder-test'
      });

      // Act
      const result = await adapter.complete({
        systemPrompt: 'You are Clean Copilot.',
        userPrompt: 'Refactor this.',
        temperature: 0.2,
        maxTokens: 1024
      });

      // Assert
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.text).toBe('export class CleanEntity {}');
        expect(result.data.modelName).toBe('qwen3-coder-test');
        expect(result.data.durationMs).toBeGreaterThanOrEqual(0);
      }

      // Verify HTTP request payload sent to fetch
      expect(fetchSpy).toHaveBeenCalledTimes(1);
      const [calledUrl, requestInit] = fetchSpy.mock.calls[0];
      expect(calledUrl).toBe('http://127.0.0.1:8080/v1/chat/completions');

      const parsedBody = JSON.parse(requestInit?.body as string);
      expect(parsedBody.model).toBe('qwen3-coder-test');
      expect(parsedBody.temperature).toBe(0.2);
      expect(parsedBody.max_tokens).toBe(1024);
      expect(parsedBody.messages).toEqual([
        { role: 'system', content: 'You are Clean Copilot.' },
        { role: 'user', content: 'Refactor this.' }
      ]);
    });

    it('should return Result.fail with LLAMA_SERVER_HTTP_ERROR when server responds with 500 error', async () => {
      // Arrange
      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: false,
        status: 500,
        text: async () => 'Context size exceeded'
      } as unknown as Response);

      const adapter = new LlamaServerAdapter({ baseUrl: 'http://127.0.0.1:8080' });

      // Act
      const result = await adapter.complete({
        systemPrompt: 'System',
        userPrompt: 'User'
      });

      // Assert
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toBeInstanceOf(InfrastructureError);
        expect(result.error.code).toBe('LLAMA_SERVER_HTTP_ERROR');
        expect(result.error.message).toContain('HTTP 500: Context size exceeded');
      }
    });

    it('should return Result.fail with LLAMA_SERVER_NETWORK_ERROR on network disconnect or abort', async () => {
      // Arrange
      vi.spyOn(globalThis, 'fetch').mockRejectedValueOnce(new Error('Connection refused (ECONNREFUSED)'));

      const adapter = new LlamaServerAdapter({ baseUrl: 'http://127.0.0.1:8080' });

      // Act
      const result = await adapter.complete({
        systemPrompt: 'System',
        userPrompt: 'User'
      });

      // Assert
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toBeInstanceOf(InfrastructureError);
        expect(result.error.code).toBe('LLAMA_CONNECTION_ERROR');
        expect(result.error.message).toContain('Failed to connect to llama-server');
      }
    });
  });
});
