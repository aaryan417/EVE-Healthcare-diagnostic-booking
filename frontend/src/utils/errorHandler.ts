import { AxiosError } from 'axios';
import type { ApiErrorPayload } from '../types/api';

export function getErrorMessage(error: unknown, fallbackMessage = 'An unexpected error occurred. Please try again.'): string {
  if (!error) return fallbackMessage;

  if (typeof error === 'string') return error;

  const axiosError = error as AxiosError<ApiErrorPayload>;

  if (axiosError.response && axiosError.response.data) {
    const data = axiosError.response.data;

    // Standardized error wrapper response
    if (data.error && data.error.message) {
      if (data.error.details && typeof data.error.details === 'object') {
        const detailValues = Object.values(data.error.details).flat();
        if (detailValues.length > 0 && typeof detailValues[0] === 'string') {
          return detailValues[0];
        }
      }
      return data.error.message;
    }

    // Direct detail key
    if (data.detail && typeof data.detail === 'string') {
      return data.detail;
    }

    // DRF field-level errors dictionary
    if (typeof data === 'object') {
      const entries = Object.entries(data);
      for (const [key, val] of entries) {
        if (key === 'error') continue;
        if (Array.isArray(val) && val.length > 0 && typeof val[0] === 'string') {
          return `${key}: ${val[0]}`;
        }
        if (typeof val === 'string') {
          return `${key}: ${val}`;
        }
      }
    }
  }

  if (axiosError.message) {
    if (axiosError.message === 'Network Error') {
      return 'Unable to connect to EVE Healthcare servers. Please check your network connection.';
    }
    return axiosError.message;
  }

  return fallbackMessage;
}
