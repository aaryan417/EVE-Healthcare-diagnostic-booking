import { apiClient } from './axios';
import type { Booking, PaginatedResponse } from '../types/api';


export const bookingsApi = {
  createBooking: async (slotId: number): Promise<Booking> => {
    const response = await apiClient.post<Booking>('/bookings/', { slot: slotId });
    return response.data;
  },

  getBookings: async (page = 1): Promise<PaginatedResponse<Booking>> => {
    const response = await apiClient.get<PaginatedResponse<Booking>>('/bookings/', {
      params: { page },
    });
    return response.data;
  },

  getBookingDetail: async (id: number): Promise<Booking> => {
    const response = await apiClient.get<Booking>(`/bookings/${id}/`);
    return response.data;
  },

  cancelBooking: async (id: number): Promise<Booking> => {
    const response = await apiClient.post<Booking>(`/bookings/${id}/cancel/`);
    return response.data;
  },
};
