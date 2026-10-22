import { describe, it, expect } from 'vitest';
import { FileDiskReader } from '../../../src/infrastructure/fs/FileDiskReader.js';
import { InfrastructureError } from '../../../src/shared/errors/DomainError.js';

describe('FileDiskReader Infrastructure Adapter', () => {
  const reader = new FileDiskReader();

  it('should successfully read an existing file from disk', async () => {
    // Arrange
    const targetFile = 'package.json';

    // Act
    const result = await reader.read(targetFile);

    // Assert
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data).toContain('edge-clean-copilot-cli');
      expect(result.data).toContain('"name":');
    }
  });

  it('should return Result.fail with InfrastructureError when the file does not exist', async () => {
    // Arrange
    const nonExistentFile = 'src/domain/ghost/NonExistentFile.ts';

    // Act
    const result = await reader.read(nonExistentFile);

    // Assert
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error).toBeInstanceOf(InfrastructureError);
      expect(result.error.code).toBe('FILE_READ_ERROR');
      expect(result.error.message).toContain('Unable to read file at "src/domain/ghost/NonExistentFile.ts"');
    }
  });
});
