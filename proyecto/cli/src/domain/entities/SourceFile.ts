import { ValidationError } from '../../shared/errors/DomainError.js';

export interface SourceFileProps {
  readonly filePath: string;
  readonly content: string;
  readonly language?: string;
}

export class SourceFile {
  private static readonly MAX_CHARACTERS = 50_000;
  private static readonly ALLOWED_EXTENSIONS = ['.ts', '.tsx', '.js', '.jsx'];

  private constructor(
    public readonly filePath: string,
    public readonly content: string,
    public readonly language: string
  ) {}

  public static create(props: SourceFileProps): SourceFile {
    if (!props.filePath || props.filePath.trim().length === 0) {
      throw new ValidationError('File path cannot be empty.');
    }

    if (!props.content || props.content.trim().length === 0) {
      throw new ValidationError(`Source file "${props.filePath}" is empty.`);
    }

    if (props.content.length > this.MAX_CHARACTERS) {
      throw new ValidationError(
        `File size (${props.content.length} chars) exceeds maximum allowed context limit (${this.MAX_CHARACTERS} chars).`
      );
    }

    const detectedLang = props.language ?? this.detectLanguage(props.filePath);

    return new SourceFile(props.filePath.trim(), props.content, detectedLang);
  }

  private static detectLanguage(filePath: string): string {
    const extIndex = filePath.lastIndexOf('.');
    if (extIndex === -1) {
      return 'typescript';
    }
    const ext = filePath.slice(extIndex).toLowerCase();
    if (!this.ALLOWED_EXTENSIONS.includes(ext)) {
      throw new ValidationError(
        `Unsupported file extension "${ext}". Allowed: ${this.ALLOWED_EXTENSIONS.join(', ')}`
      );
    }
    return ext.includes('ts') ? 'typescript' : 'javascript';
  }

  public get lineCount(): number {
    return this.content.split('\n').length;
  }
}
