import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import type { Booking, BookingStatus } from '../../types/api';
import { Calendar, Clock, MapPin, TestTube, CreditCard, XCircle, AlertTriangle } from 'lucide-react';

interface BookingCardProps {
  booking: Booking;
  onCancelBooking: (bookingId: number) => Promise<void>;
}

export const BookingCard: React.FC<BookingCardProps> = ({ booking, onCancelBooking }) => {
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [cancelling, setCancelling] = useState(false);

  const renderStatusBadge = (status: BookingStatus) => {
    const badgeStyles: Record<BookingStatus, string> = {
      PENDING: 'bg-amber-50 text-amber-800 border-amber-200',
      CONFIRMED: 'bg-emerald-50 text-emerald-800 border-emerald-200',
      FAILED: 'bg-rose-50 text-rose-800 border-rose-200',
      CANCELLED: 'bg-slate-100 text-slate-600 border-slate-300',
    };

    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold border ${badgeStyles[status]}`}>
        <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${
          status === 'CONFIRMED' ? 'bg-emerald-500' :
          status === 'PENDING' ? 'bg-amber-500' :
          status === 'FAILED' ? 'bg-rose-500' : 'bg-slate-400'
        }`}></span>
        {status}
      </span>
    );
  };

  const handleConfirmCancel = async () => {
    try {
      setCancelling(true);
      await onCancelBooking(booking.id);
      setShowCancelModal(false);
    } finally {
      setCancelling(false);
    }
  };

  const formatTime = (timeStr: string) => {
    try {
      const [hours, minutes] = timeStr.split(':');
      const h = parseInt(hours, 10);
      const ampm = h >= 12 ? 'PM' : 'AM';
      const formattedH = h % 12 || 12;
      return `${formattedH}:${minutes} ${ampm}`;
    } catch {
      return timeStr;
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between gap-3 mb-4 pb-4 border-b border-slate-100">
          <div>
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">Booking Reference</span>
            <span className="text-sm font-bold text-slate-900 font-mono">#BK-{booking.id}</span>
          </div>
          {renderStatusBadge(booking.status)}
        </div>

        {/* Details Grid */}
        <div className="space-y-3 mb-6">
          <div className="flex items-center gap-2.5 text-slate-700">
            <TestTube className="w-4 h-4 text-teal-600 flex-shrink-0" />
            <span className="text-base font-bold text-slate-900">{booking.test?.name}</span>
          </div>

          <div className="flex items-start gap-2.5 text-slate-600 text-sm">
            <MapPin className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
            <span>{booking.centre?.name}</span>
          </div>

          <div className="flex items-center gap-2.5 text-slate-600 text-sm">
            <Calendar className="w-4 h-4 text-slate-400 flex-shrink-0" />
            <span>{booking.slot?.date}</span>
          </div>

          <div className="flex items-center gap-2.5 text-slate-600 text-sm">
            <Clock className="w-4 h-4 text-slate-400 flex-shrink-0" />
            <span>
              {formatTime(booking.slot?.start_time)} – {formatTime(booking.slot?.end_time)}
            </span>
          </div>
        </div>

        {/* Amount */}
        <div className="flex items-center justify-between bg-slate-50 rounded-xl p-3 mb-6 border border-slate-100">
          <span className="text-xs font-semibold text-slate-500 uppercase">Amount</span>
          <span className="text-lg font-bold text-teal-700">₹{booking.amount}</span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 pt-2">
        {booking.status === 'PENDING' && (
          <Link
            to={`/payment/${booking.id}`}
            className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-sm rounded-xl transition-colors shadow-sm"
          >
            <CreditCard className="w-4 h-4" />
            Pay Now
          </Link>
        )}

        {(booking.status === 'PENDING' || booking.status === 'CONFIRMED') && (
          <button
            onClick={() => setShowCancelModal(true)}
            className="px-4 py-2.5 border border-slate-200 text-slate-600 hover:text-rose-600 hover:bg-rose-50 hover:border-rose-200 text-sm font-semibold rounded-xl transition-colors inline-flex items-center gap-1.5"
          >
            <XCircle className="w-4 h-4" />
            Cancel
          </button>
        )}
      </div>

      {/* Cancel Confirmation Modal */}
      {showCancelModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100 animate-in fade-in zoom-in duration-150">
            <div className="w-12 h-12 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mb-4">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">Cancel Appointment?</h3>
            <p className="text-sm text-slate-600 mb-6">
              Are you sure you want to cancel booking <strong className="text-slate-900">#BK-{booking.id}</strong> for{' '}
              <strong>{booking.test?.name}</strong> at <strong>{booking.centre?.name}</strong>?
            </p>

            <div className="flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowCancelModal(false)}
                disabled={cancelling}
                className="px-4 py-2 border border-slate-300 text-slate-700 text-sm font-medium rounded-xl hover:bg-slate-50 transition-colors disabled:opacity-50"
              >
                Keep Booking
              </button>
              <button
                type="button"
                onClick={handleConfirmCancel}
                disabled={cancelling}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-sm font-semibold rounded-xl transition-colors shadow-sm disabled:opacity-50"
              >
                {cancelling ? 'Cancelling...' : 'Confirm Cancellation'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
