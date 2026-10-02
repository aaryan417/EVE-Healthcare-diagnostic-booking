export interface User {
  id: number;
  email: string;
  name: string;
  is_staff: boolean;
  is_superuser: boolean;
}

export interface DiagnosticCentre {
  id: number;
  name: string;
  address: string;
  city: string;
  state: string;
  pincode: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DiagnosticTest {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
}

export interface CentreTest {
  id: number;
  centre: DiagnosticCentre;
  test: DiagnosticTest;
  price: string;
  is_available: boolean;
}

export interface AppointmentSlot {
  id: number;
  centre_test: number;
  date: string;
  start_time: string;
  end_time: string;
  capacity: number;
  remaining_capacity: number;
}

export interface AvailableDatesResponse {
  centre_test: number;
  dates: string[];
}

export type BookingStatus = 'PENDING' | 'CONFIRMED' | 'FAILED' | 'CANCELLED';

export interface Booking {
  id: number;
  status: BookingStatus;
  amount: string;
  user: {
    id: number;
    name: string;
    email: string;
  };
  centre: {
    id: number;
    name: string;
    address?: string;
    city?: string;
    state?: string;
    pincode?: string;
  };
  test: {
    id: number;
    name: string;
  };
  slot: {
    id: number;
    date: string;
    start_time: string;
    end_time: string;
  };
  created_at: string;
  updated_at: string;
  cancelled_at?: string | null;
}

export type PaymentStatus = 'PENDING' | 'SUCCESS' | 'FAILED';

export interface Payment {
  id: number;
  transaction_id: string;
  booking: number;
  amount: string;
  status: PaymentStatus;
  booking_status: BookingStatus;
  created_at: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiErrorPayload {
  error?: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
  detail?: string;
  [key: string]: any;
}
