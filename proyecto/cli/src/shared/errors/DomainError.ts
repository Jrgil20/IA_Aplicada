export class DomainError extends Error {
  constructor(
    message: string,
    public readonly code: string = 'DOMAIN_ERROR'
  ) {
    super(message);
    this.name = 'DomainError';
  }
}

export class ValidationError extends DomainError {
  constructor(message: string) {
    super(message, 'VALIDATION_ERROR');
    this.name = 'ValidationError';
  }
}

export class InfrastructureError extends Error {
  constructor(
    message: string,
    public readonly code: string = 'INFRASTRUCTURE_ERROR',
    public readonly originalError?: unknown
  ) {
    super(message);
    this.name = 'InfrastructureError';
  }
}
