import { apiClient } from './axios';
import type { Payment, PaginatedResponse } from '../types/api';

export interface ProcessPaymentPayload {
  booking: number;
  simulate_result: 'SUCCESS' | 'FAILED';
}

export const paymentsApi = {
  processPayment: async (payload: ProcessPaymentPayload): Promise<Payment> => {
    const response = await apiClient.post<Payment>('/payments/', payload);
    return response.data;
  },

  getPayments: async (page = 1): Promise<PaginatedResponse<Payment>> => {
    const response = await apiClient.get<PaginatedResponse<Payment>>('/payments/', {
      params: { page },
    });
    return response.data;
  },

  getPaymentDetail: async (id: number): Promise<Payment> => {
    const response = await apiClient.get<Payment>(`/payments/${id}/`);
    return response.data;
  },
};
