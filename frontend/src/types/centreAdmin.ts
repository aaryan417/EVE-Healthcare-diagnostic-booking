export interface CentreAdminCentreItem {
  id: number;
  name: string;
  role: string;
}

export interface CentreAdminProfile {
  is_centre_admin: boolean;
  centres: CentreAdminCentreItem[];
}

export interface CentreAdminRecentBooking {
  id: number;
  patient_name: string;
  patient_email: string;
  test_name: string;
  slot_date: string;
  slot_time: string;
  amount: string;
  status: string;
}

export interface CentreAdminDashboardSummary {
  active_tests: number;
  today_bookings: number;
  upcoming_bookings: number;
  upcoming_slots: number;
  recent_bookings: CentreAdminRecentBooking[];
}
