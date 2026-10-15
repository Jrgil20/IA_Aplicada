import * as fs from 'node:fs/promises';
import * as path from 'node:path';
import { Result } from '../../shared/types/Result.js';
import { InfrastructureError } from '../../shared/errors/DomainError.js';

export class FileDiskReader {
  public async read(filePath: string): Promise<Result<string, InfrastructureError>> {
    try {
      const resolvedPath = path.resolve(process.cwd(), filePath);
      const content = await fs.readFile(resolvedPath, 'utf-8');
      return Result.ok(content);
    } catch (error) {
      return Result.fail(
        new InfrastructureError(
          `Unable to read file at "${filePath}": ${(error as Error).message}`,
          'FILE_READ_ERROR',
          error
        )
      );
    }
  }
}
