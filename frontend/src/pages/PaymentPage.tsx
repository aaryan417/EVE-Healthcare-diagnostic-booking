import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { bookingsApi } from '../api/bookings';
import { paymentsApi } from '../api/payments';
import type { Booking, Payment } from '../types/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { getErrorMessage } from '../utils/errorHandler';
import { CheckCircle2, XCircle, CreditCard, ShieldAlert, ArrowRight, Calendar, Clock, MapPin, TestTube } from 'lucide-react';

export const PaymentPage: React.FC = () => {
  const { bookingId } = useParams<{ bookingId: string }>();
  const idNum = parseInt(bookingId || '0', 10);

  const [booking, setBooking] = useState<Booking | null>(null);
  const [paymentResult, setPaymentResult] = useState<Payment | null>(null);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBooking = async () => {
    if (!idNum) return;
    try {
      setLoading(true);
      setError(null);
      const res = await bookingsApi.getBookingDetail(idNum);
      setBooking(res);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load booking details.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBooking();
  }, [idNum]);

  const handleSimulatePayment = async (resultType: 'SUCCESS' | 'FAILED') => {
    if (!idNum) return;

    try {
      setSubmitting(true);
      setError(null);
      const res = await paymentsApi.processPayment({
        booking: idNum,
        simulate_result: resultType,
      });
      setPaymentResult(res);

      // Refresh booking object to reflect updated status
      const updatedBooking = await bookingsApi.getBookingDetail(idNum);
      setBooking(updatedBooking);
    } catch (err) {
      setError(getErrorMessage(err, 'Payment simulation request failed.'));
    } finally {
      setSubmitting(false);
    }
  };

  const formatTime = (timeStr?: string) => {
    if (!timeStr) return '';
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
    <div className="max-w-2xl mx-auto space-y-8 py-6">
      {error && <ErrorAlert message={error} onRetry={fetchBooking} />}

      {loading ? (
        <div className="py-16">
          <LoadingSpinner label="Retrieving booking confirmation..." size="lg" />
        </div>
      ) : !booking ? (
        <div className="bg-white rounded-3xl p-8 border border-slate-200 text-center">
          <h2 className="text-xl font-bold text-slate-900">Booking Not Found</h2>
        </div>
      ) : paymentResult && paymentResult.status === 'SUCCESS' ? (
        /* SUCCESS STATE */
        <div className="bg-white rounded-3xl border border-slate-200 p-8 shadow-md text-center space-y-6">
          <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto shadow-inner">
            <CheckCircle2 className="w-10 h-10" />
          </div>

          <div>
            <span className="text-xs font-bold text-emerald-700 uppercase tracking-widest bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
              Payment Successful
            </span>
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight mt-3">
              Booking Confirmed
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Your appointment has been locked and confirmed.
            </p>
          </div>

          <div className="bg-slate-50 rounded-2xl p-6 text-left border border-slate-200 space-y-3">
            <div className="flex justify-between items-center text-sm py-1 border-b border-slate-200">
              <span className="text-slate-500 font-medium">Transaction ID</span>
              <span className="font-mono font-bold text-slate-900">{paymentResult.transaction_id}</span>
            </div>
            <div className="flex justify-between items-center text-sm py-1 border-b border-slate-200">
              <span className="text-slate-500 font-medium">Booking ID</span>
              <span className="font-mono font-bold text-slate-900">#BK-{booking.id}</span>
            </div>
            <div className="flex justify-between items-center text-sm py-1 border-b border-slate-200">
              <span className="text-slate-500 font-medium">Diagnostic Test</span>
              <span className="font-semibold text-slate-900">{booking.test?.name}</span>
            </div>
            <div className="flex justify-between items-center text-sm py-1 border-b border-slate-200">
              <span className="text-slate-500 font-medium">Centre</span>
              <span className="font-semibold text-slate-900">{booking.centre?.name}</span>
            </div>
            <div className="flex justify-between items-center text-sm py-1 border-b border-slate-200">
              <span className="text-slate-500 font-medium">Date & Time</span>
              <span className="font-semibold text-slate-900">
                {booking.slot?.date} ({formatTime(booking.slot?.start_time)})
              </span>
            </div>
            <div className="flex justify-between items-center text-sm py-1 pt-2">
              <span className="text-slate-900 font-bold">Amount Paid</span>
              <span className="text-xl font-extrabold text-teal-700">₹{booking.amount}</span>
            </div>
          </div>

          <Link
            to="/my-bookings"
            className="w-full inline-flex items-center justify-center gap-2 px-6 py-3.5 bg-teal-600 hover:bg-teal-700 text-white font-bold text-sm rounded-xl transition-all shadow-md shadow-teal-200"
          >
            View My Bookings
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      ) : paymentResult && paymentResult.status === 'FAILED' ? (
        /* FAILED STATE */
        <div className="bg-white rounded-3xl border border-slate-200 p-8 shadow-md text-center space-y-6">
          <div className="w-16 h-16 bg-rose-100 text-rose-600 rounded-full flex items-center justify-center mx-auto shadow-inner">
            <XCircle className="w-10 h-10" />
          </div>

          <div>
            <span className="text-xs font-bold text-rose-700 uppercase tracking-widest bg-rose-50 px-3 py-1 rounded-full border border-rose-200">
              Payment Failed
            </span>
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight mt-3">
              Booking Not Confirmed
            </h1>
            <p className="text-sm text-slate-600 mt-2 max-w-md mx-auto">
              The payment attempt failed. Per platform policy, the reserved slot capacity for this booking has been automatically released for other patients.
            </p>
          </div>

          <div className="bg-rose-50/50 border border-rose-200 rounded-2xl p-4 text-left text-sm text-rose-900 space-y-1">
            <p className="font-semibold">Terminal Booking Failure</p>
            <p className="text-xs text-rose-700">
              This booking record (#BK-{booking.id}) is marked FAILED and cannot be retried. Please select another time slot to book afresh.
            </p>
          </div>

          <Link
            to={booking.centre ? `/centres` : '/centres'}
            className="w-full inline-flex items-center justify-center gap-2 px-6 py-3.5 bg-slate-900 hover:bg-teal-600 text-white font-bold text-sm rounded-xl transition-all shadow-md"
          >
            Choose Another Slot
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      ) : (
        /* PENDING STATE REVIEW & SIMULATED PAYMENTS */
        <div className="bg-white rounded-3xl border border-slate-200 p-8 shadow-md space-y-8">
          <div className="border-b border-slate-100 pb-6 text-center sm:text-left">
            <span className="text-xs font-bold text-amber-700 uppercase tracking-wider bg-amber-50 px-3 py-1 rounded-full border border-amber-200">
              Status: PENDING PAYMENT
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight mt-3">
              Review & Pay Booking #BK-{booking.id}
            </h1>
          </div>

          {/* Booking Summary */}
          <div className="space-y-4 bg-slate-50 rounded-2xl p-6 border border-slate-200">
            <div className="flex items-center gap-3">
              <TestTube className="w-5 h-5 text-teal-600 flex-shrink-0" />
              <div>
                <span className="text-xs text-slate-400 font-semibold uppercase">Diagnostic Test</span>
                <p className="text-base font-bold text-slate-900">{booking.test?.name}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <MapPin className="w-5 h-5 text-slate-400 flex-shrink-0" />
              <div>
                <span className="text-xs text-slate-400 font-semibold uppercase">Centre</span>
                <p className="text-sm font-semibold text-slate-800">{booking.centre?.name}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Calendar className="w-5 h-5 text-slate-400 flex-shrink-0" />
              <div>
                <span className="text-xs text-slate-400 font-semibold uppercase">Appointment Date</span>
                <p className="text-sm font-semibold text-slate-800">{booking.slot?.date}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Clock className="w-5 h-5 text-slate-400 flex-shrink-0" />
              <div>
                <span className="text-xs text-slate-400 font-semibold uppercase">Time Slot</span>
                <p className="text-sm font-semibold text-slate-800">
                  {formatTime(booking.slot?.start_time)} – {formatTime(booking.slot?.end_time)}
                </p>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-200 flex justify-between items-center">
              <span className="text-sm font-bold text-slate-900">Total Payable</span>
              <span className="text-2xl font-extrabold text-teal-700">₹{booking.amount}</span>
            </div>
          </div>

          {/* Simulation Disclaimer Box */}
          <div className="bg-teal-50/70 border border-teal-200 rounded-2xl p-4 text-xs text-teal-900 space-y-1">
            <div className="flex items-center gap-1.5 font-bold text-teal-800 text-sm">
              <ShieldAlert className="w-4 h-4 text-teal-600" />
              Simulated Payment Environment
            </div>
            <p>
              This environment simulates gateway processing. Click below to test successful or failed payment outcomes.
            </p>
          </div>

          {/* Simulation Action Buttons */}
          <div className="space-y-3 pt-2">
            <button
              onClick={() => handleSimulatePayment('SUCCESS')}
              disabled={submitting}
              className="w-full inline-flex items-center justify-center gap-2 py-4 px-6 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-base rounded-2xl transition-all shadow-md shadow-emerald-200 disabled:opacity-50"
            >
              <CreditCard className="w-5 h-5" />
              {submitting ? 'Processing Payment...' : 'Simulate Successful Payment'}
            </button>

            <button
              onClick={() => handleSimulatePayment('FAILED')}
              disabled={submitting}
              className="w-full inline-flex items-center justify-center gap-2 py-3 px-6 bg-slate-100 hover:bg-rose-50 text-slate-700 hover:text-rose-700 border border-slate-200 hover:border-rose-200 font-semibold text-sm rounded-2xl transition-all disabled:opacity-50"
            >
              Simulate Failed Payment
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
