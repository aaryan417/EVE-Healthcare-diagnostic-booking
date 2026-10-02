import { apiClient } from './axios';
import type {
  DiagnosticCentre,
  CentreTest,
  AppointmentSlot,
  AvailableDatesResponse,
  PaginatedResponse,
} from '../types/api';


export const diagnosticsApi = {
  getCentres: async (page = 1): Promise<PaginatedResponse<DiagnosticCentre>> => {
    const response = await apiClient.get<PaginatedResponse<DiagnosticCentre>>('/centres/', {
      params: { page },
    });
    return response.data;
  },

  getCentreDetail: async (id: number): Promise<DiagnosticCentre> => {
    const response = await apiClient.get<DiagnosticCentre>(`/centres/${id}/`);
    return response.data;
  },

  getCentreTests: async (centreId: number, page = 1): Promise<PaginatedResponse<CentreTest>> => {
    const response = await apiClient.get<PaginatedResponse<CentreTest>>('/centre-tests/', {
      params: { centre: centreId, page },
    });
    return response.data;
  },

  getCentreTestDetail: async (id: number): Promise<CentreTest> => {
    const response = await apiClient.get<CentreTest>(`/centre-tests/${id}/`);
    return response.data;
  },

  getAvailableDates: async (centreTestId: number): Promise<AvailableDatesResponse> => {
    const response = await apiClient.get<AvailableDatesResponse>('/slots/available-dates/', {
      params: { centre_test: centreTestId },
    });
    return response.data;
  },

  getSlots: async (centreTestId: number, date: string, page = 1): Promise<PaginatedResponse<AppointmentSlot>> => {
    const response = await apiClient.get<PaginatedResponse<AppointmentSlot>>('/slots/', {
      params: { centre_test: centreTestId, date, page },
    });
    return response.data;
  },
};
