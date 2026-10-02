import React, { useState, useEffect } from 'react';
import { bookingsApi } from '../api/bookings';
import type { Booking, PaginatedResponse } from '../types/api';
import { BookingCard } from '../components/bookings/BookingCard';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { EmptyState } from '../components/common/EmptyState';
import { Pagination } from '../components/common/Pagination';
import { getErrorMessage } from '../utils/errorHandler';
import { Calendar, Building2 } from 'lucide-react';
import { Link } from 'react-router-dom';

export const MyBookingsPage: React.FC = () => {
  const [data, setData] = useState<PaginatedResponse<Booking> | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBookings = async (page: number) => {
    try {
      setLoading(true);
      setError(null);
      const res = await bookingsApi.getBookings(page);
      setData(res);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to fetch bookings list.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBookings(currentPage);
  }, [currentPage]);

  const handleCancelBooking = async (bookingId: number) => {
    try {
      await bookingsApi.cancelBooking(bookingId);
      // Refresh list after cancellation
      fetchBookings(currentPage);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to cancel booking.'));
    }
  };

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="space-y-8 py-4">
      {/* Header */}
      <div className="border-b border-slate-200 pb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            My Appointments
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            View your upcoming and past diagnostic test appointments
          </p>
        </div>

        <Link
          to="/centres"
          className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-sm rounded-xl transition-all shadow-sm"
        >
          <Building2 className="w-4 h-4" />
          Book New Test
        </Link>
      </div>

      {error && <ErrorAlert message={error} onRetry={() => fetchBookings(currentPage)} />}

      {loading ? (
        <div className="py-16">
          <LoadingSpinner label="Retrieving your bookings..." size="lg" />
        </div>
      ) : !data || data.results.length === 0 ? (
        <EmptyState
          icon={<Calendar className="w-12 h-12 text-slate-400" />}
          title="No Appointments Found"
          message="You haven't booked any diagnostic tests yet. Find a centre to get started."
          actionLabel="Browse Centres"
          onAction={() => window.location.href = '/centres'}
        />
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data.results.map((booking) => (
              <BookingCard
                key={booking.id}
                booking={booking}
                onCancelBooking={handleCancelBooking}
              />
            ))}
          </div>

          <Pagination
            count={data.count}
            currentPage={currentPage}
            pageSize={20}
            onPageChange={handlePageChange}
            disabled={loading}
          />
        </>
      )}
    </div>
  );
};
