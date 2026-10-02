import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { diagnosticsApi } from '../api/diagnostics';
import { bookingsApi } from '../api/bookings';
import type { CentreTest, AppointmentSlot } from '../types/api';
import { CalendarSelector } from '../components/slots/CalendarSelector';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { EmptyState } from '../components/common/EmptyState';
import { getErrorMessage } from '../utils/errorHandler';
import { formatCentreAddress } from '../utils/address';
import { Building2, MapPin, Clock, ChevronLeft, Check, ArrowRight, AlertTriangle } from 'lucide-react';

export const BookingPage: React.FC = () => {
  const { centreTestId } = useParams<{ centreTestId: string }>();
  const idNum = parseInt(centreTestId || '0', 10);
  const navigate = useNavigate();

  const [centreTest, setCentreTest] = useState<CentreTest | null>(null);
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [slots, setSlots] = useState<AppointmentSlot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<AppointmentSlot | null>(null);

  const [loadingTest, setLoadingTest] = useState(true);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [slotConflictMsg, setSlotConflictMsg] = useState<string | null>(null);

  // Load test details & available dates
  const initBooking = async () => {
    if (!idNum) return;
    try {
      setLoadingTest(true);
      setError(null);

      const [ctRes, datesRes] = await Promise.all([
        diagnosticsApi.getCentreTestDetail(idNum),
        diagnosticsApi.getAvailableDates(idNum),
      ]);

      setCentreTest(ctRes);
      setAvailableDates(datesRes.dates);

      if (datesRes.dates.length > 0) {
        setSelectedDate(datesRes.dates[0]);
      }
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to initialize booking details.'));
    } finally {
      setLoadingTest(false);
    }
  };

  useEffect(() => {
    initBooking();
  }, [idNum]);

  // Load slots when selected date changes
  const fetchSlotsForDate = async (dateStr: string) => {
    if (!idNum || !dateStr) return;
    try {
      setLoadingSlots(true);
      setSlotConflictMsg(null);
      setSelectedSlot(null);

      const slotsRes = await diagnosticsApi.getSlots(idNum, dateStr);
      setSlots(slotsRes.results);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to fetch available slots for date.'));
    } finally {
      setLoadingSlots(false);
    }
  };

  useEffect(() => {
    if (selectedDate) {
      fetchSlotsForDate(selectedDate);
    }
  }, [selectedDate]);

  const handleDateSelect = (dateStr: string) => {
    setSelectedDate(dateStr);
  };

  const handleCreateBooking = async () => {
    if (!selectedSlot) return;

    try {
      setSubmitting(true);
      setError(null);
      setSlotConflictMsg(null);

      const booking = await bookingsApi.createBooking(selectedSlot.id);
      navigate(`/payment/${booking.id}`);
    } catch (err: any) {
      // Check for 409 Conflict (slot full / concurrent booking)
      if (err?.response?.status === 409) {
        setSlotConflictMsg(
          'This slot was just booked by another patient. Please select another available time.'
        );
        // Refresh available slots and dates
        fetchSlotsForDate(selectedDate);
        initBooking();
      } else {
        setError(getErrorMessage(err, 'Failed to create booking. Please try again.'));
      }
    } finally {
      setSubmitting(false);
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
    <div className="max-w-4xl mx-auto space-y-8 py-4">
      {/* Back Link */}
      <div>
        <Link
          to={centreTest ? `/centres/${centreTest.centre?.id}/tests` : '/centres'}
          className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-600 hover:text-teal-700 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Tests
        </Link>
      </div>

      {error && <ErrorAlert message={error} onRetry={initBooking} />}

      {loadingTest ? (
        <div className="py-16">
          <LoadingSpinner label="Loading test and calendar dates..." size="lg" />
        </div>
      ) : !centreTest ? (
        <EmptyState
          title="Test Not Found"
          message="The requested diagnostic test offering could not be found."
        />
      ) : (
        <div className="space-y-8">
          {/* Summary Banner */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-2 text-xs font-bold text-teal-700 bg-teal-50 px-3 py-1 rounded-full border border-teal-100">
                <Building2 className="w-3.5 h-3.5" />
                {centreTest.centre?.name}
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                {centreTest.test?.name}
              </h1>
              {formatCentreAddress(centreTest.centre) && (
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <MapPin className="w-4 h-4 text-slate-400 flex-shrink-0" />
                  <span>{formatCentreAddress(centreTest.centre)}</span>
                </div>
              )}
            </div>

            <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 text-right self-stretch md:self-auto flex md:flex-col justify-between items-center md:items-end">
              <span className="text-xs font-semibold text-slate-400 uppercase">Test Fee</span>
              <span className="text-3xl font-extrabold text-teal-700">₹{centreTest.price}</span>
            </div>
          </div>

          {/* Calendar Date Selector */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm">
            <CalendarSelector
              availableDates={availableDates}
              selectedDate={selectedDate}
              onSelectDate={handleDateSelect}
            />
          </div>

          {/* Conflict Alert */}
          {slotConflictMsg && (
            <div className="bg-amber-50 border border-amber-300 rounded-2xl p-4 flex items-start gap-3 text-amber-900">
              <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm font-semibold">{slotConflictMsg}</p>
            </div>
          )}

          {/* Slots List for Selected Date */}
          {selectedDate && (
            <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <h3 className="text-lg font-bold text-slate-900">
                  Available Time Slots for <span className="text-teal-700">{selectedDate}</span>
                </h3>
              </div>

              {loadingSlots ? (
                <div className="py-8">
                  <LoadingSpinner label="Fetching available slots..." size="md" />
                </div>
              ) : slots.length === 0 ? (
                <EmptyState
                  icon={<Clock className="w-10 h-10 text-slate-400" />}
                  title="No Open Slots"
                  message="All slots for this date are fully booked or past. Please select another date."
                />
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                  {slots.map((slot) => {
                    const isSelected = selectedSlot?.id === slot.id;
                    const isFull = slot.remaining_capacity <= 0;

                    return (
                      <button
                        key={slot.id}
                        type="button"
                        disabled={isFull}
                        onClick={() => setSelectedSlot(slot)}
                        className={`p-4 rounded-2xl border text-left transition-all relative ${
                          isSelected
                            ? 'bg-teal-600 border-teal-600 text-white shadow-md shadow-teal-200 ring-2 ring-teal-600 ring-offset-2'
                            : isFull
                            ? 'bg-slate-100 border-slate-200 text-slate-400 opacity-60 cursor-not-allowed'
                            : 'bg-white border-slate-200 text-slate-800 hover:border-teal-500 hover:bg-teal-50/50'
                        }`}
                      >
                        {isSelected && (
                          <div className="absolute top-3 right-3 w-5 h-5 bg-white text-teal-600 rounded-full flex items-center justify-center">
                            <Check className="w-3.5 h-3.5 stroke-[3]" />
                          </div>
                        )}
                        <div className="flex items-center gap-1.5 font-bold text-base mb-1">
                          <Clock className={`w-4 h-4 ${isSelected ? 'text-teal-200' : 'text-slate-400'}`} />
                          <span>
                            {formatTime(slot.start_time)} – {formatTime(slot.end_time)}
                          </span>
                        </div>
                        <span className={`text-xs font-medium block ${isSelected ? 'text-teal-100' : 'text-slate-500'}`}>
                          {isFull ? 'Fully Booked' : `${slot.remaining_capacity} slot${slot.remaining_capacity > 1 ? 's' : ''} remaining`}
                        </span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Confirm Booking CTA Bar */}
          {selectedSlot && (
            <div className="sticky bottom-4 z-30 bg-slate-900 text-white rounded-2xl p-4 sm:p-6 shadow-2xl flex flex-col sm:flex-row items-center justify-between gap-4 border border-slate-800 animate-in slide-in-from-bottom duration-200">
              <div>
                <span className="text-xs text-teal-400 font-semibold uppercase tracking-wider block">Selected Slot</span>
                <p className="text-base font-bold">
                  {selectedDate} ({formatTime(selectedSlot.start_time)} – {formatTime(selectedSlot.end_time)})
                </p>
              </div>

              <button
                onClick={handleCreateBooking}
                disabled={submitting}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-base rounded-xl transition-all shadow-lg shadow-teal-500/20 disabled:opacity-50"
              >
                {submitting ? (
                  'Creating Booking...'
                ) : (
                  <>
                    Confirm & Proceed to Payment
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
