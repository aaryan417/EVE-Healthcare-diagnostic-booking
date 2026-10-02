import React, { useState, useEffect } from 'react';
import { useCentreAdminContext } from '../../components/centreAdmin/CentreAdminLayout';
import { centreAdminApi } from '../../api/centreAdmin';
import type { CentreAdminDashboardSummary } from '../../types/centreAdmin';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../components/common/ErrorAlert';
import { EmptyState } from '../../components/common/EmptyState';
import { getErrorMessage } from '../../utils/errorHandler';
import { Link } from 'react-router-dom';
import {
  FlaskConical,
  Calendar,
  Clock,
  CheckCircle2,
  AlertCircle,
  PlusCircle,
  ArrowRight,
  ClipboardList,
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { activeCentre } = useCentreAdminContext();
  const [summary, setSummary] = useState<CentreAdminDashboardSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = async () => {
    if (!activeCentre) return;
    try {
      setLoading(true);
      setError(null);
      const data = await centreAdminApi.getDashboardSummary(activeCentre.id);
      setSummary(data);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load dashboard summary for the selected centre.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, [activeCentre?.id]);

  if (!activeCentre) {
    return (
      <EmptyState
        title="No Assigned Centre"
        message="Your account is not assigned to any active diagnostic centre."
      />
    );
  }

  if (loading) {
    return (
      <div className="py-16">
        <LoadingSpinner label="Loading dashboard metrics..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <ErrorAlert message={error} />
        <button
          onClick={fetchSummary}
          className="px-4 py-2 bg-teal-600 text-white font-semibold text-sm rounded-xl hover:bg-teal-700 transition-all shadow-sm"
        >
          Retry
        </button>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'CONFIRMED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full">
            <CheckCircle2 className="w-3.5 h-3.5" /> Confirmed
          </span>
        );
      case 'PENDING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200 rounded-full">
            <Clock className="w-3.5 h-3.5" /> Pending
          </span>
        );
      case 'CANCELLED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200 rounded-full">
            <AlertCircle className="w-3.5 h-3.5" /> Cancelled
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold bg-slate-100 text-slate-700 border border-slate-200 rounded-full">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-teal-800 to-slate-900 rounded-3xl p-6 sm:p-8 text-white shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-6">
        <div>
          <span className="text-xs font-bold text-teal-300 uppercase tracking-wider block mb-1">
            Centre Dashboard
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            {activeCentre.name}
          </h1>
          <p className="text-xs sm:text-sm text-slate-300 mt-1">
            Real-time overview of diagnostic tests, appointment capacity, and patient bookings.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 flex-shrink-0">
          <Link
            to="/centre-admin/slots"
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-xs sm:text-sm rounded-xl transition-all shadow-md"
          >
            <PlusCircle className="w-4 h-4" /> Add Slot
          </Link>
          <Link
            to="/centre-admin/tests"
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs sm:text-sm rounded-xl transition-all border border-slate-700"
          >
            <FlaskConical className="w-4 h-4 text-teal-400" /> Manage Tests
          </Link>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Active Tests */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-teal-50 text-teal-700 flex items-center justify-center border border-teal-100 flex-shrink-0">
            <FlaskConical className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
              Active Tests
            </span>
            <span className="text-2xl font-black text-slate-900 block mt-0.5">
              {summary?.active_tests ?? 0}
            </span>
          </div>
        </div>

        {/* Today's Bookings */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-700 flex items-center justify-center border border-amber-100 flex-shrink-0">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
              Today's Bookings
            </span>
            <span className="text-2xl font-black text-slate-900 block mt-0.5">
              {summary?.today_bookings ?? 0}
            </span>
          </div>
        </div>

        {/* Upcoming Bookings */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-700 flex items-center justify-center border border-emerald-100 flex-shrink-0">
            <ClipboardList className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
              Upcoming Bookings
            </span>
            <span className="text-2xl font-black text-slate-900 block mt-0.5">
              {summary?.upcoming_bookings ?? 0}
            </span>
          </div>
        </div>

        {/* Upcoming Slots */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-sky-50 text-sky-700 flex items-center justify-center border border-sky-100 flex-shrink-0">
            <Calendar className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
              Upcoming Slots
            </span>
            <span className="text-2xl font-black text-slate-900 block mt-0.5">
              {summary?.upcoming_slots ?? 0}
            </span>
          </div>
        </div>
      </div>

      {/* Recent Bookings Section */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-xs space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-extrabold text-slate-900">Recent Bookings</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Latest patient reservations created for {activeCentre.name}
            </p>
          </div>

          <Link
            to="/centre-admin/bookings"
            className="inline-flex items-center gap-1.5 text-xs font-bold text-teal-700 hover:text-teal-900 transition-colors"
          >
            View All Bookings <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {!summary?.recent_bookings || summary.recent_bookings.length === 0 ? (
          <EmptyState
            title="No Bookings Yet"
            message="There are no patient bookings recorded for this centre yet."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3.5 rounded-l-xl">Booking ID</th>
                  <th className="px-4 py-3.5">Patient</th>
                  <th className="px-4 py-3.5">Diagnostic Test</th>
                  <th className="px-4 py-3.5">Appointment Window</th>
                  <th className="px-4 py-3.5">Amount</th>
                  <th className="px-4 py-3.5 rounded-r-xl">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {summary.recent_bookings.map((booking) => (
                  <tr key={booking.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-4 py-4 font-bold text-slate-900">#{booking.id}</td>
                    <td className="px-4 py-4">
                      <span className="font-bold text-slate-900 block">{booking.patient_name}</span>
                      <span className="text-xs text-slate-500 block">{booking.patient_email}</span>
                    </td>
                    <td className="px-4 py-4 text-slate-800 font-semibold">{booking.test_name}</td>
                    <td className="px-4 py-4 text-xs text-slate-600">
                      <span className="font-bold text-slate-800 block">{booking.slot_date}</span>
                      <span>{booking.slot_time}</span>
                    </td>
                    <td className="px-4 py-4 font-extrabold text-slate-900">₹{booking.amount}</td>
                    <td className="px-4 py-4">{getStatusBadge(booking.status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
