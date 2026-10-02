import React, { useState, useEffect } from 'react';
import { useCentreAdminContext } from '../../components/centreAdmin/CentreAdminLayout';
import { centreAdminApi } from '../../api/centreAdmin';
import type { Booking } from '../../types/api';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../components/common/ErrorAlert';
import { EmptyState } from '../../components/common/EmptyState';
import { getErrorMessage } from '../../utils/errorHandler';
import {
  CheckCircle2,
  Clock,
  AlertCircle,
  XCircle,
  ChevronLeft,
  ChevronRight,
  Filter,
} from 'lucide-react';

export const BookingsPage: React.FC = () => {
  const { activeCentre } = useCentreAdminContext();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filter & Pagination State
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [totalCount, setTotalCount] = useState<number>(0);

  const fetchBookings = async () => {
    if (!activeCentre) return;
    try {
      setLoading(true);
      setError(null);
      const params: { status?: string; page?: number } = { page };
      if (statusFilter) {
        params.status = statusFilter;
      }
      const res = await centreAdminApi.getCentreBookings(activeCentre.id, params);
      setBookings(res.results || []);
      setTotalCount(res.count || 0);
      setTotalPages(Math.ceil((res.count || 0) / 20));
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load bookings for the selected centre.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBookings();
  }, [activeCentre?.id, statusFilter, page]);

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
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold bg-slate-100 text-slate-700 border border-slate-200 rounded-full">
            <XCircle className="w-3.5 h-3.5" /> Failed
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

  if (!activeCentre) {
    return (
      <EmptyState
        title="No Assigned Centre"
        message="Select an assigned diagnostic centre to view patient bookings."
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <h1 className="text-xl sm:text-2xl font-black text-slate-900">Patient Bookings</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            View patient reservations and appointment history for <span className="font-bold text-slate-800">{activeCentre.name}</span>
          </p>
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-2 bg-slate-50 p-1.5 rounded-2xl border border-slate-200">
          <Filter className="w-4 h-4 text-slate-400 ml-2" />
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="bg-transparent text-xs sm:text-sm font-bold text-slate-700 focus:outline-none cursor-pointer pr-4"
          >
            <option value="">All Statuses</option>
            <option value="CONFIRMED">Confirmed</option>
            <option value="PENDING">Pending</option>
            <option value="CANCELLED">Cancelled</option>
            <option value="FAILED">Failed</option>
          </select>
        </div>
      </div>

      {error && <ErrorAlert message={error} />}

      {/* Main Content */}
      {loading ? (
        <div className="py-16">
          <LoadingSpinner label="Loading patient bookings..." />
        </div>
      ) : bookings.length === 0 ? (
        <EmptyState
          title="No Bookings Found"
          message={
            statusFilter
              ? `No bookings match status "${statusFilter}".`
              : 'There are no patient bookings recorded for this centre.'
          }
        />
      ) : (
        <div className="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-xs space-y-4">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="px-6 py-4">Booking ID</th>
                  <th className="px-6 py-4">Patient Details</th>
                  <th className="px-6 py-4">Diagnostic Test</th>
                  <th className="px-6 py-4">Appointment Date & Time</th>
                  <th className="px-6 py-4">Snapshot Amount</th>
                  <th className="px-6 py-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {bookings.map((b) => (
                  <tr key={b.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-6 py-4 font-bold text-slate-900">#{b.id}</td>
                    <td className="px-6 py-4">
                      <span className="font-bold text-slate-900 block">{b.user.name || 'Patient'}</span>
                      <span className="text-xs text-slate-500 block">{b.user.email}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-bold text-slate-900 block">{b.test?.name || 'Diagnostic Test'}</span>
                      <span className="text-xs text-slate-500 block">{b.centre?.name}</span>
                    </td>
                    <td className="px-6 py-4 text-xs">
                      <span className="font-bold text-slate-900 block">{b.slot.date}</span>
                      <span className="text-slate-500">{b.slot.start_time} - {b.slot.end_time}</span>
                    </td>
                    <td className="px-6 py-4 font-black text-slate-900 text-base">₹{b.amount}</td>
                    <td className="px-6 py-4">{getStatusBadge(b.status)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
              <span className="text-xs text-slate-500 font-medium">
                Showing page <strong className="text-slate-900">{page}</strong> of <strong className="text-slate-900">{totalPages}</strong> ({totalCount} total bookings)
              </span>

              <div className="flex items-center gap-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="p-2 rounded-xl bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                  className="p-2 rounded-xl bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
