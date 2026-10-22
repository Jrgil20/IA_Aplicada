import { describe, it, expect } from 'vitest';
import { SourceFile } from '../../../src/domain/entities/SourceFile.js';
import { ValidationError } from '../../../src/shared/errors/DomainError.js';

describe('SourceFile Domain Entity', () => {
  describe('Valid Creation', () => {
    it('should create a valid SourceFile for a TypeScript (.ts) file', () => {
      // Arrange
      const props = {
        filePath: 'src/domain/entities/User.ts',
        content: 'export class User {\n  constructor(public readonly id: string) {}\n}'
      };

      // Act
      const file = SourceFile.create(props);

      // Assert
      expect(file.filePath).toBe('src/domain/entities/User.ts');
      expect(file.content).toBe(props.content);
      expect(file.language).toBe('typescript');
      expect(file.lineCount).toBe(3);
    });

    it('should detect typescript for .tsx files', () => {
      // Arrange & Act
      const file = SourceFile.create({
        filePath: 'src/components/Button.tsx',
        content: 'export const Button = () => <button>Click</button>;'
      });

      // Assert
      expect(file.language).toBe('typescript');
      expect(file.lineCount).toBe(1);
    });

    it('should detect javascript for .js and .jsx files', () => {
      // Arrange & Act
      const jsFile = SourceFile.create({
        filePath: 'legacy/utils.js',
        content: 'function sum(a, b) { return a + b; }'
      });
      const jsxFile = SourceFile.create({
        filePath: 'legacy/Widget.jsx',
        content: 'export default function Widget() {}'
      });

      // Assert
      expect(jsFile.language).toBe('javascript');
      expect(jsxFile.language).toBe('javascript');
    });

    it('should trim surrounding whitespace from filePath', () => {
      // Arrange & Act
      const file = SourceFile.create({
        filePath: '   src/app.ts   ',
        content: 'console.log("hello");'
      });

      // Assert
      expect(file.filePath).toBe('src/app.ts');
    });

    it('should respect explicit language override if provided', () => {
      // Arrange & Act
      const file = SourceFile.create({
        filePath: 'src/custom.ts',
        content: 'const x = 1;',
        language: 'custom-ts'
      });

      // Assert
      expect(file.language).toBe('custom-ts');
    });
  });

  describe('Invariant Validation & Edge Cases', () => {
    it('should throw ValidationError if filePath is empty or whitespace', () => {
      // Arrange & Act & Assert
      expect(() => SourceFile.create({ filePath: '', content: 'const a = 1;' })).toThrow(ValidationError);
      expect(() => SourceFile.create({ filePath: '   ', content: 'const a = 1;' })).toThrow(
        'File path cannot be empty.'
      );
    });

    it('should throw ValidationError if content is empty or whitespace', () => {
      // Arrange & Act & Assert
      expect(() => SourceFile.create({ filePath: 'src/empty.ts', content: '' })).toThrow(ValidationError);
      expect(() => SourceFile.create({ filePath: 'src/empty.ts', content: '   \n  \t ' })).toThrow(
        'Source file "src/empty.ts" is empty.'
      );
    });

    it('should throw ValidationError if file content exceeds 50,000 characters', () => {
      // Arrange
      const oversizedContent = 'a'.repeat(50_001);

      // Act & Assert
      expect(() =>
        SourceFile.create({
          filePath: 'src/huge.ts',
          content: oversizedContent
        })
      ).toThrow(ValidationError);

      expect(() =>
        SourceFile.create({
          filePath: 'src/huge.ts',
          content: oversizedContent
        })
      ).toThrow(/exceeds maximum allowed context limit/);
    });

    it('should allow file content exactly at the 50,000 character limit', () => {
      // Arrange
      const boundaryContent = 'a'.repeat(50_000);

      // Act
      const file = SourceFile.create({
        filePath: 'src/limit.ts',
        content: boundaryContent
      });

      // Assert
      expect(file.content.length).toBe(50_000);
    });

    it('should throw ValidationError for unsupported file extensions', () => {
      // Arrange & Act & Assert
      const unsupported = ['script.py', 'App.java', 'main.cpp', 'lib.rs', 'data.json'];

      for (const path of unsupported) {
        expect(() => SourceFile.create({ filePath: path, content: 'code' })).toThrow(ValidationError);
        expect(() => SourceFile.create({ filePath: path, content: 'code' })).toThrow(
          /Unsupported file extension/
        );
      }
    });
  });
});
