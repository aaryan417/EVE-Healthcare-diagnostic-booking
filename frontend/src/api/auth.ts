import { apiClient } from './axios';
import type { User } from '../types/api';


export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
  password_confirm?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
}

export const authApi = {
  register: async (payload: RegisterPayload): Promise<User> => {
    const response = await apiClient.post<User>('/auth/register/', payload);
    return response.data;
  },

  login: async (payload: LoginPayload): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/auth/login/', payload);
    return response.data;
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/auth/me/');
    return response.data;
  },
};
