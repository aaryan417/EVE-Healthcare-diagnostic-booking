import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User } from '../types/api';
import type { CentreAdminProfile } from '../types/centreAdmin';
import { authApi } from '../api/auth';
import { centreAdminApi } from '../api/centreAdmin';
import type { LoginPayload, RegisterPayload } from '../api/auth';
import { getErrorMessage } from '../utils/errorHandler';

interface AuthContextType {
  user: User | null;
  centreAdminProfile: CentreAdminProfile | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (payload: LoginPayload) => Promise<CentreAdminProfile | null>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [centreAdminProfile, setCentreAdminProfile] = useState<CentreAdminProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchCentreAdminProfile = async () => {
    try {
      const profile = await centreAdminApi.getProfile();
      setCentreAdminProfile(profile);
      return profile;
    } catch {
      setCentreAdminProfile(null);
      return null;
    }
  };

  const restoreAuth = async () => {
    const token = localStorage.getItem('access_token');
    if (token) {
      try {
        const currentUser = await authApi.getCurrentUser();
        setUser(currentUser);
        await fetchCentreAdminProfile();
      } catch {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        setUser(null);
        setCentreAdminProfile(null);
      }
    }
    setLoading(false);
  };

  useEffect(() => {
    restoreAuth();

    const handleLogoutEvent = () => {
      setUser(null);
      setCentreAdminProfile(null);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    };

    window.addEventListener('auth:logout', handleLogoutEvent);
    return () => {
      window.removeEventListener('auth:logout', handleLogoutEvent);
    };
  }, []);

  const login = async (payload: LoginPayload) => {
    try {
      const response = await authApi.login(payload);
      localStorage.setItem('access_token', response.access);
      localStorage.setItem('refresh_token', response.refresh);
      setUser(response.user);
      const profile = await fetchCentreAdminProfile();
      return profile;
    } catch (err) {
      throw new Error(getErrorMessage(err, 'Login failed. Please check your credentials.'));
    }
  };

  const register = async (payload: RegisterPayload) => {
    try {
      await authApi.register(payload);
      await login({ email: payload.email, password: payload.password });
    } catch (err) {
      throw new Error(getErrorMessage(err, 'Registration failed. Please check form inputs.'));
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    setCentreAdminProfile(null);
  };

  const refreshProfile = async () => {
    await fetchCentreAdminProfile();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        centreAdminProfile,
        isAuthenticated: !!user,
        loading,
        login,
        register,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
