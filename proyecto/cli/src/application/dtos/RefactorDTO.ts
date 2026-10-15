export interface RefactorInputDTO {
  readonly filePath: string;
  readonly fileContent: string;
}

export interface RefactorOutputDTO {
  readonly filePath: string;
  readonly originalLineCount: number;
  readonly refactoredCode: string;
  readonly modelUsed: string;
  readonly durationMs: number;
}
