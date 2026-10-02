import { apiClient } from './axios';
import type {
  CentreAdminProfile,
  CentreAdminDashboardSummary,
} from '../types/centreAdmin';
import type {
  CentreTest,
  DiagnosticTest,
  AppointmentSlot,
  Booking,
  PaginatedResponse,
} from '../types/api';

export interface CreateCentreTestPayload {
  centre: number;
  test: number;
  price: string;
  is_available?: boolean;
}

export interface UpdateCentreTestPayload {
  price?: string;
  is_available?: boolean;
}

export interface CreateSlotPayload {
  centre_test: number;
  date: string;
  start_time: string;
  end_time: string;
  capacity: number;
}

export interface BulkGenerateSlotsPayload {
  centre_test: number;
  start_date: string;
  end_date: string;
  start_time: string;
  end_time: string;
  slot_duration_minutes: number;
  capacity: number;
}

export interface BulkGenerateSlotsResponse {
  message: string;
  created_count: number;
  skipped_count: number;
  date_count: number;
  centre_test: number;
  start_date: string;
  end_date: string;
}

export const centreAdminApi = {
  getProfile: async (): Promise<CentreAdminProfile> => {
    const response = await apiClient.get<CentreAdminProfile>('/centre-admin/me/');
    return response.data;
  },

  getDashboardSummary: async (centreId: number): Promise<CentreAdminDashboardSummary> => {
    const response = await apiClient.get<CentreAdminDashboardSummary>('/centre-admin/dashboard/', {
      params: { centre: centreId },
    });
    return response.data;
  },

  getCentreTests: async (centreId: number, page = 1): Promise<PaginatedResponse<CentreTest>> => {
    const response = await apiClient.get<PaginatedResponse<CentreTest>>('/centre-tests/', {
      params: { centre: centreId, page },
    });
    return response.data;
  },

  getGlobalTests: async (): Promise<PaginatedResponse<DiagnosticTest>> => {
    const response = await apiClient.get<PaginatedResponse<DiagnosticTest>>('/tests/');
    return response.data;
  },

  createCentreTest: async (payload: CreateCentreTestPayload): Promise<CentreTest> => {
    const response = await apiClient.post<CentreTest>('/centre-tests/', payload);
    return response.data;
  },

  updateCentreTest: async (id: number, payload: UpdateCentreTestPayload): Promise<CentreTest> => {
    const response = await apiClient.patch<CentreTest>(`/centre-tests/${id}/`, payload);
    return response.data;
  },

  getCentreSlots: async (centreId: number, page = 1): Promise<PaginatedResponse<AppointmentSlot>> => {
    const response = await apiClient.get<PaginatedResponse<AppointmentSlot>>('/slots/', {
      params: { centre: centreId, page },
    });
    return response.data;
  },

  createSlot: async (payload: CreateSlotPayload): Promise<AppointmentSlot> => {
    const response = await apiClient.post<AppointmentSlot>('/slots/', payload);
    return response.data;
  },

  bulkGenerateSlots: async (payload: BulkGenerateSlotsPayload): Promise<BulkGenerateSlotsResponse> => {
    const response = await apiClient.post<BulkGenerateSlotsResponse>(
      '/centre-admin/slots/bulk-generate/',
      payload
    );
    return response.data;
  },

  getCentreBookings: async (
    centreId: number,
    params?: { status?: string; date?: string; test?: number; page?: number }
  ): Promise<PaginatedResponse<Booking>> => {
    const response = await apiClient.get<PaginatedResponse<Booking>>('/bookings/', {
      params: { centre: centreId, ...params },
    });
    return response.data;
  },
};

