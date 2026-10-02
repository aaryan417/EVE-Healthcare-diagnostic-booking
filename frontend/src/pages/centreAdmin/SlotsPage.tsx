import React, { useState, useEffect } from 'react';
import { useCentreAdminContext } from '../../components/centreAdmin/CentreAdminLayout';
import { centreAdminApi, type BulkGenerateSlotsResponse } from '../../api/centreAdmin';
import type { AppointmentSlot, CentreTest } from '../../types/api';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../components/common/ErrorAlert';
import { EmptyState } from '../../components/common/EmptyState';
import { getErrorMessage } from '../../utils/errorHandler';
import {
  Calendar as CalendarIcon,
  Plus,
  Clock,
  FlaskConical,
  X,
  Users,
  Layers,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';

export const SlotsPage: React.FC = () => {
  const { activeCentre } = useCentreAdminContext();
  const [slots, setSlots] = useState<AppointmentSlot[]>([]);
  const [centreTests, setCentreTests] = useState<CentreTest[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Single Slot Modal State
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [selectedCentreTestId, setSelectedCentreTestId] = useState<number | ''>('');
  const [slotDate, setSlotDate] = useState<string>('');
  const [startTime, setStartTime] = useState<string>('09:00');
  const [endTime, setEndTime] = useState<string>('09:30');
  const [capacity, setCapacity] = useState<number>(5);
  const [modalError, setModalError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);

  // Bulk Slot Generation Modal State
  const [showBulkModal, setShowBulkModal] = useState<boolean>(false);
  const [bulkCentreTestId, setBulkCentreTestId] = useState<number | ''>('');
  const [bulkStartDate, setBulkStartDate] = useState<string>('');
  const [bulkEndDate, setBulkEndDate] = useState<string>('');
  const [bulkStartTime, setBulkStartTime] = useState<string>('09:00');
  const [bulkEndTime, setBulkEndTime] = useState<string>('17:00');
  const [bulkDuration, setBulkDuration] = useState<number>(30);
  const [bulkCapacity, setBulkCapacity] = useState<number>(5);
  const [bulkSubmitting, setBulkSubmitting] = useState<boolean>(false);
  const [bulkError, setBulkError] = useState<string | null>(null);
  const [bulkSuccessResult, setBulkSuccessResult] = useState<BulkGenerateSlotsResponse | null>(null);

  const fetchData = async () => {
    if (!activeCentre) return;
    try {
      setLoading(true);
      setError(null);
      const [slotsRes, ctRes] = await Promise.all([
        centreAdminApi.getCentreSlots(activeCentre.id),
        centreAdminApi.getCentreTests(activeCentre.id),
      ]);
      setSlots(slotsRes.results || []);
      setCentreTests(ctRes.results || []);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load appointment slots.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeCentre?.id]);

  const handleCreateSlot = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCentreTestId || !slotDate || !startTime || !endTime) {
      setModalError('Please fill in all required slot fields.');
      return;
    }

    try {
      setSubmitting(true);
      setModalError(null);
      await centreAdminApi.createSlot({
        centre_test: Number(selectedCentreTestId),
        date: slotDate,
        start_time: startTime.length === 5 ? `${startTime}:00` : startTime,
        end_time: endTime.length === 5 ? `${endTime}:00` : endTime,
        capacity: Number(capacity),
      });
      setShowAddModal(false);
      setSelectedCentreTestId('');
      setSlotDate('');
      await fetchData();
    } catch (err) {
      setModalError(getErrorMessage(err, 'Failed to create appointment slot. Please check for time conflicts.'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleBulkGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bulkCentreTestId || !bulkStartDate || !bulkEndDate || !bulkStartTime || !bulkEndTime) {
      setBulkError('Please fill in all required fields for bulk generation.');
      return;
    }

    try {
      setBulkSubmitting(true);
      setBulkError(null);
      setBulkSuccessResult(null);

      const response = await centreAdminApi.bulkGenerateSlots({
        centre_test: Number(bulkCentreTestId),
        start_date: bulkStartDate,
        end_date: bulkEndDate,
        start_time: bulkStartTime.length === 5 ? `${bulkStartTime}:00` : bulkStartTime,
        end_time: bulkEndTime.length === 5 ? `${bulkEndTime}:00` : bulkEndTime,
        slot_duration_minutes: Number(bulkDuration),
        capacity: Number(bulkCapacity),
      });

      setBulkSuccessResult(response);
      await fetchData();
    } catch (err) {
      setBulkError(getErrorMessage(err, 'Failed to bulk generate appointment slots.'));
    } finally {
      setBulkSubmitting(false);
    }
  };

  // Live preview calculations for Bulk Generator
  const calculatePreview = () => {
    if (!bulkStartDate || !bulkEndDate || !bulkStartTime || !bulkEndTime || !bulkDuration) {
      return null;
    }
    const start = new Date(bulkStartDate);
    const end = new Date(bulkEndDate);
    if (isNaN(start.getTime()) || isNaN(end.getTime()) || end < start) {
      return null;
    }
    const dateCount = Math.max(0, Math.floor((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1);

    const [sh, sm] = bulkStartTime.split(':').map(Number);
    const [eh, em] = bulkEndTime.split(':').map(Number);
    if (isNaN(sh) || isNaN(sm) || isNaN(eh) || isNaN(em)) return null;

    const startMin = sh * 60 + sm;
    const endMin = eh * 60 + em;
    const windowMin = endMin - startMin;

    if (windowMin <= 0 || bulkDuration <= 0) return null;

    const slotsPerDay = Math.floor(windowMin / bulkDuration);
    const totalEst = dateCount * slotsPerDay;

    return { dateCount, slotsPerDay, totalEst };
  };

  const preview = calculatePreview();

  // Minimum allowed date (today)
  const todayStr = new Date().toISOString().split('T')[0];

  if (!activeCentre) {
    return (
      <EmptyState
        title="No Assigned Centre"
        message="Select an assigned diagnostic centre to manage appointment capacity."
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <h1 className="text-xl sm:text-2xl font-black text-slate-900">Appointment Slots</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Configure calendar date windows and patient capacity for <span className="font-bold text-slate-800">{activeCentre.name}</span>
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => {
              setShowAddModal(true);
              setModalError(null);
            }}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs sm:text-sm rounded-xl transition-all"
          >
            <Plus className="w-4 h-4 text-slate-600" /> Create Single Slot
          </button>

          <button
            onClick={() => {
              setShowBulkModal(true);
              setBulkError(null);
              setBulkSuccessResult(null);
              if (centreTests.length > 0 && !bulkCentreTestId) {
                setBulkCentreTestId(centreTests[0].id);
              }
            }}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs sm:text-sm rounded-xl transition-all shadow-sm shadow-teal-200"
          >
            <Layers className="w-4 h-4" /> Bulk Generate Slots
          </button>
        </div>
      </div>

      {error && <ErrorAlert message={error} />}

      {/* Main Content Table */}
      {loading ? (
        <div className="py-16">
          <LoadingSpinner label="Loading appointment slots..." />
        </div>
      ) : slots.length === 0 ? (
        <EmptyState
          title="No Appointment Slots Configured"
          message="There are currently no upcoming appointment slots for this centre."
          actionLabel="Generate Slots"
          onAction={() => setShowBulkModal(true)}
        />
      ) : (
        <div className="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="px-6 py-4">Slot ID</th>
                  <th className="px-6 py-4">Diagnostic Test</th>
                  <th className="px-6 py-4">Date</th>
                  <th className="px-6 py-4">Time Window</th>
                  <th className="px-6 py-4">Total Capacity</th>
                  <th className="px-6 py-4">Remaining Capacity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {slots.map((s) => {
                  const testOffering = centreTests.find((ct) => ct.id === s.centre_test);
                  return (
                    <tr key={s.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-6 py-4 font-bold text-slate-900">#{s.id}</td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2.5">
                          <FlaskConical className="w-4 h-4 text-teal-600 flex-shrink-0" />
                          <span className="font-bold text-slate-900">
                            {testOffering?.test?.name || `Offering #${s.centre_test}`}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <CalendarIcon className="w-4 h-4 text-slate-400" />
                          <span className="font-semibold text-slate-900">{s.date}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <Clock className="w-4 h-4 text-slate-400" />
                          <span className="font-semibold text-slate-800">
                            {s.start_time} - {s.end_time}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 font-bold text-slate-900">{s.capacity}</td>
                      <td className="px-6 py-4">
                        {s.remaining_capacity > 0 ? (
                          <span className="inline-flex items-center gap-1 px-3 py-1 text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full">
                            <Users className="w-3 h-3" /> {s.remaining_capacity} available
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-3 py-1 text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200 rounded-full">
                            Full (0 available)
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create Single Slot Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl border border-slate-200 max-w-lg w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <h3 className="text-lg font-extrabold text-slate-900">
                Create Single Appointment Slot
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {modalError && <ErrorAlert message={modalError} />}

            <form onSubmit={handleCreateSlot} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Diagnostic Test Offering
                </label>
                {centreTests.length === 0 ? (
                  <p className="text-xs text-amber-600 bg-amber-50 p-3 rounded-xl border border-amber-200 font-medium">
                    No active test offerings exist for this centre. Please add tests first under Tests & Pricing.
                  </p>
                ) : (
                  <select
                    required
                    value={selectedCentreTestId}
                    onChange={(e) => setSelectedCentreTestId(Number(e.target.value))}
                    className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="">-- Select Test Offering --</option>
                    {centreTests.map((ct) => (
                      <option key={ct.id} value={ct.id}>
                        {ct.test?.name} (₹{ct.price})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Appointment Date
                </label>
                <input
                  type="date"
                  min={todayStr}
                  required
                  value={slotDate}
                  onChange={(e) => setSlotDate(e.target.value)}
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    Start Time
                  </label>
                  <input
                    type="time"
                    required
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                    className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    End Time
                  </label>
                  <input
                    type="time"
                    required
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                    className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Capacity (Max Patients)
                </label>
                <input
                  type="number"
                  min="1"
                  required
                  value={capacity}
                  onChange={(e) => setCapacity(Number(e.target.value))}
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || centreTests.length === 0}
                  className="px-5 py-2.5 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs sm:text-sm rounded-xl transition-all shadow-sm shadow-teal-200 disabled:opacity-50"
                >
                  {submitting ? 'Creating...' : 'Create Slot'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Bulk Generate Slots Modal */}
      {showBulkModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl border border-slate-200 max-w-xl w-full p-6 shadow-2xl space-y-5 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div>
                <h3 className="text-lg font-extrabold text-slate-900 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-teal-600" />
                  Generate Multiple Slots
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Automatically create recurring appointment slots over a date range
                </p>
              </div>
              <button
                onClick={() => setShowBulkModal(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {bulkError && <ErrorAlert message={bulkError} />}

            {bulkSuccessResult && (
              <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl space-y-2">
                <div className="flex items-center gap-2 text-emerald-800 font-bold text-sm">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                  {bulkSuccessResult.message}
                </div>
                <div className="text-xs text-emerald-700 font-medium grid grid-cols-3 gap-2 pt-1 border-t border-emerald-200/60">
                  <div>
                    <span className="text-slate-500 block">Created:</span>
                    <strong className="text-emerald-900 text-sm">{bulkSuccessResult.created_count}</strong> slots
                  </div>
                  <div>
                    <span className="text-slate-500 block">Skipped:</span>
                    <strong className="text-amber-800 text-sm">{bulkSuccessResult.skipped_count}</strong> existing
                  </div>
                  <div>
                    <span className="text-slate-500 block">Days:</span>
                    <strong className="text-slate-800 text-sm">{bulkSuccessResult.date_count}</strong> days
                  </div>
                </div>
              </div>
            )}

            <form onSubmit={handleBulkGenerate} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Centre Test Offering
                </label>
                {centreTests.length === 0 ? (
                  <p className="text-xs text-amber-600 bg-amber-50 p-3 rounded-xl border border-amber-200 font-medium">
                    No active test offerings exist for this centre. Please add tests first under Tests & Pricing.
                  </p>
                ) : (
                  <select
                    required
                    value={bulkCentreTestId}
                    onChange={(e) => setBulkCentreTestId(Number(e.target.value))}
                    className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="">-- Select Diagnostic Test Offering --</option>
                    {centreTests.map((ct) => (
                      <option key={ct.id} value={ct.id}>
                        {ct.test?.name} (₹{ct.price})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {/* Date Range */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    Start Date
                  </label>
                  <input
                    type="date"
                    min={todayStr}
                    required
                    value={bulkStartDate}
                    onChange={(e) => setBulkStartDate(e.target.value)}
                    className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    End Date
                  </label>
                  <input
                    type="date"
                    min={bulkStartDate || todayStr}
                    required
                    value={bulkEndDate}
                    onChange={(e) => setBulkEndDate(e.target.value)}
                    className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
              </div>

              {/* Working Hours */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    Working Start Time
                  </label>
                  <input
                    type="time"
                    required
                    value={bulkStartTime}
                    onChange={(e) => setBulkStartTime(e.target.value)}
                    className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    Working End Time
                  </label>
                  <input
                    type="time"
                    required
                    value={bulkEndTime}
                    onChange={(e) => setBulkEndTime(e.target.value)}
                    className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
              </div>

              {/* Slot Duration & Capacity */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    Slot Duration
                  </label>
                  <select
                    required
                    value={bulkDuration}
                    onChange={(e) => setBulkDuration(Number(e.target.value))}
                    className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  >
                    <option value={15}>15 minutes</option>
                    <option value={20}>20 minutes</option>
                    <option value={30}>30 minutes</option>
                    <option value={45}>45 minutes</option>
                    <option value={60}>60 minutes (1 hour)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                    Capacity per Slot
                  </label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={bulkCapacity}
                    onChange={(e) => setBulkCapacity(Number(e.target.value))}
                    className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
              </div>

              {/* Estimated Preview Box */}
              {preview && (
                <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs text-slate-600 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-teal-600" />
                    <span>
                      <strong className="text-slate-800">{preview.dateCount} days</strong> ×{' '}
                      <strong className="text-slate-800">{preview.slotsPerDay} slots/day</strong>
                    </span>
                  </div>
                  <span className="font-bold text-teal-700 bg-teal-50 px-2.5 py-1 rounded-lg border border-teal-200">
                    Est. max {preview.totalEst} slots
                  </span>
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowBulkModal(false)}
                  className="px-4 py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={bulkSubmitting || centreTests.length === 0}
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs sm:text-sm rounded-xl transition-all shadow-sm shadow-teal-200 disabled:opacity-50"
                >
                  {bulkSubmitting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Generating...
                    </>
                  ) : (
                    'Generate Slots'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
