import { DomainError } from '../errors/DomainError.js';

export type Result<T, E = DomainError> =
  | { success: true; data: T }
  | { success: false; error: E };

export const Result = {
  ok<T>(data: T): Result<T, never> {
    return { success: true, data };
  },
  fail<E>(error: E): Result<never, E> {
    return { success: false, error };
  }
};
