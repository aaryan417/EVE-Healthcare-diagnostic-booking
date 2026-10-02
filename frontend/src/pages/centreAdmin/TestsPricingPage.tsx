import React, { useState, useEffect } from 'react';
import { useCentreAdminContext } from '../../components/centreAdmin/CentreAdminLayout';
import { centreAdminApi } from '../../api/centreAdmin';
import type { CentreTest, DiagnosticTest } from '../../types/api';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { ErrorAlert } from '../../components/common/ErrorAlert';
import { EmptyState } from '../../components/common/EmptyState';
import { getErrorMessage } from '../../utils/errorHandler';
import {
  FlaskConical,
  Plus,
  Edit2,
  CheckCircle2,
  XCircle,
  X,
  Search,
} from 'lucide-react';

export const TestsPricingPage: React.FC = () => {
  const { activeCentre } = useCentreAdminContext();
  const [centreTests, setCentreTests] = useState<CentreTest[]>([]);
  const [globalTests, setGlobalTests] = useState<DiagnosticTest[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');

  // Add Test Modal State
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [selectedGlobalTestId, setSelectedGlobalTestId] = useState<number | ''>('');
  const [newPrice, setNewPrice] = useState<string>('');
  const [modalError, setModalError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);

  // Edit Test Modal State
  const [editingTest, setEditingTest] = useState<CentreTest | null>(null);
  const [editPrice, setEditPrice] = useState<string>('');
  const [editAvailable, setEditAvailable] = useState<boolean>(true);
  const [editModalError, setEditModalError] = useState<string | null>(null);
  const [editSubmitting, setEditSubmitting] = useState<boolean>(false);

  const fetchTestsData = async () => {
    if (!activeCentre) return;
    try {
      setLoading(true);
      setError(null);
      const [ctRes, gtRes] = await Promise.all([
        centreAdminApi.getCentreTests(activeCentre.id),
        centreAdminApi.getGlobalTests(),
      ]);
      setCentreTests(ctRes.results || []);
      setGlobalTests(gtRes.results || []);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load test offerings.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTestsData();
  }, [activeCentre?.id]);

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCentre || !selectedGlobalTestId || !newPrice) {
      setModalError('Please select a test and specify a valid price.');
      return;
    }

    try {
      setSubmitting(true);
      setModalError(null);
      await centreAdminApi.createCentreTest({
        centre: activeCentre.id,
        test: Number(selectedGlobalTestId),
        price: newPrice.trim(),
        is_available: true,
      });
      setShowAddModal(false);
      setSelectedGlobalTestId('');
      setNewPrice('');
      await fetchTestsData();
    } catch (err) {
      setModalError(getErrorMessage(err, 'Failed to add test to centre.'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingTest || !editPrice) {
      setEditModalError('Please specify a valid price.');
      return;
    }

    try {
      setEditSubmitting(true);
      setEditModalError(null);
      await centreAdminApi.updateCentreTest(editingTest.id, {
        price: editPrice.trim(),
        is_available: editAvailable,
      });
      setEditingTest(null);
      await fetchTestsData();
    } catch (err) {
      setEditModalError(getErrorMessage(err, 'Failed to update test details.'));
    } finally {
      setEditSubmitting(false);
    }
  };

  const filteredCentreTests = centreTests.filter((ct) => {
    const testName = ct.test?.name || '';
    const testDesc = ct.test?.description || '';
    return (
      testName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      testDesc.toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  // Filter out global tests that are already offered by this centre
  const availableGlobalTests = globalTests.filter(
    (gt) => !centreTests.some((ct) => ct.test.id === gt.id)
  );

  if (!activeCentre) {
    return (
      <EmptyState
        title="No Assigned Centre"
        message="Select an assigned diagnostic centre to manage test offerings."
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-xs">
        <div>
          <h1 className="text-xl sm:text-2xl font-black text-slate-900">Tests & Pricing</h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            Manage test catalog offerings and custom pricing for <span className="font-bold text-slate-800">{activeCentre.name}</span>
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs sm:text-sm rounded-xl transition-all shadow-sm shadow-teal-200"
        >
          <Plus className="w-4 h-4" /> Add Test to Centre
        </button>
      </div>

      {error && <ErrorAlert message={error} />}

      {/* Search Bar */}
      <div className="relative max-w-md">
        <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Filter tests by name or description..."
          className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-xs sm:text-sm font-medium focus:outline-none focus:ring-2 focus:ring-teal-500"
        />
      </div>

      {/* Main Content */}
      {loading ? (
        <div className="py-16">
          <LoadingSpinner label="Loading centre test catalog..." />
        </div>
      ) : filteredCentreTests.length === 0 ? (
        <EmptyState
          title="No Diagnostic Tests Found"
          message={
            searchTerm
              ? 'No tests match your filter criteria.'
              : 'This diagnostic centre currently has no test offerings configured.'
          }
          actionLabel={searchTerm ? undefined : 'Add First Test'}
          onAction={searchTerm ? undefined : () => setShowAddModal(true)}
        />
      ) : (
        <div className="bg-white rounded-3xl border border-slate-200 overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 text-xs font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="px-6 py-4">Diagnostic Test</th>
                  <th className="px-6 py-4">Description</th>
                  <th className="px-6 py-4">Centre Price</th>
                  <th className="px-6 py-4">Availability</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {filteredCentreTests.map((ct) => (
                  <tr key={ct.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center font-bold flex-shrink-0 border border-teal-100">
                          <FlaskConical className="w-4 h-4" />
                        </div>
                        <span className="font-bold text-slate-900">{ct.test?.name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-500 max-w-xs truncate">
                      {ct.test?.description || 'No description available'}
                    </td>
                    <td className="px-6 py-4 font-black text-slate-900 text-base">₹{ct.price}</td>
                    <td className="px-6 py-4">
                      {ct.is_available ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Available
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200 rounded-full">
                          <XCircle className="w-3.5 h-3.5" /> Disabled
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => {
                          setEditingTest(ct);
                          setEditPrice(ct.price);
                          setEditAvailable(ct.is_available);
                          setEditModalError(null);
                        }}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-teal-50 text-slate-700 hover:text-teal-700 font-semibold text-xs rounded-xl transition-all border border-slate-200"
                      >
                        <Edit2 className="w-3.5 h-3.5" /> Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add Test Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl border border-slate-200 max-w-lg w-full p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <h3 className="text-lg font-extrabold text-slate-900">Add Test to {activeCentre.name}</h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {modalError && <ErrorAlert message={modalError} />}

            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Select Diagnostic Test
                </label>
                {availableGlobalTests.length === 0 ? (
                  <p className="text-xs text-amber-600 bg-amber-50 p-3 rounded-xl border border-amber-200 font-medium">
                    All global catalog tests are already offered by this centre.
                  </p>
                ) : (
                  <select
                    required
                    value={selectedGlobalTestId}
                    onChange={(e) => setSelectedGlobalTestId(Number(e.target.value))}
                    className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="">-- Choose a test from catalog --</option>
                    {availableGlobalTests.map((gt) => (
                      <option key={gt.id} value={gt.id}>
                        {gt.name}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Centre Price (₹)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  required
                  value={newPrice}
                  onChange={(e) => setNewPrice(e.target.value)}
                  placeholder="e.g. 550.00"
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
                  disabled={submitting || availableGlobalTests.length === 0}
                  className="px-5 py-2.5 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs sm:text-sm rounded-xl transition-all shadow-sm shadow-teal-200 disabled:opacity-50"
                >
                  {submitting ? 'Adding...' : 'Add Test Offering'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Test Modal */}
      {editingTest && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl border border-slate-200 max-w-lg w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <h3 className="text-lg font-extrabold text-slate-900">
                Edit {editingTest.test?.name}
              </h3>
              <button
                onClick={() => setEditingTest(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {editModalError && <ErrorAlert message={editModalError} />}

            <form onSubmit={handleEditSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Price (₹)
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  required
                  value={editPrice}
                  onChange={(e) => setEditPrice(e.target.value)}
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="flex items-center gap-3 pt-2">
                <input
                  type="checkbox"
                  id="editAvailable"
                  checked={editAvailable}
                  onChange={(e) => setEditAvailable(e.target.checked)}
                  className="w-4 h-4 text-teal-600 border-slate-300 rounded focus:ring-teal-500"
                />
                <label htmlFor="editAvailable" className="text-sm font-semibold text-slate-800 cursor-pointer">
                  Available for patient booking
                </label>
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setEditingTest(null)}
                  className="px-4 py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={editSubmitting}
                  className="px-5 py-2.5 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs sm:text-sm rounded-xl transition-all shadow-sm shadow-teal-200 disabled:opacity-50"
                >
                  {editSubmitting ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
