import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { diagnosticsApi } from '../api/diagnostics';
import type { DiagnosticCentre, CentreTest, PaginatedResponse } from '../types/api';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { EmptyState } from '../components/common/EmptyState';
import { Pagination } from '../components/common/Pagination';
import { getErrorMessage } from '../utils/errorHandler';
import { formatCentreAddress } from '../utils/address';
import { Building2, MapPin, TestTube, ArrowRight, ChevronLeft } from 'lucide-react';

export const CentreTestsPage: React.FC = () => {
  const { centreId } = useParams<{ centreId: string }>();
  const idNum = parseInt(centreId || '0', 10);

  const [centre, setCentre] = useState<DiagnosticCentre | null>(null);
  const [data, setData] = useState<PaginatedResponse<CentreTest> | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async (page: number) => {
    if (!idNum) return;
    try {
      setLoading(true);
      setError(null);

      const [centreRes, testsRes] = await Promise.all([
        diagnosticsApi.getCentreDetail(idNum),
        diagnosticsApi.getCentreTests(idNum, page),
      ]);

      setCentre(centreRes);
      setData(testsRes);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load centre tests.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(currentPage);
  }, [idNum, currentPage]);

  return (
    <div className="space-y-8 py-4">
      {/* Back Link */}
      <div>
        <Link
          to="/centres"
          className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-600 hover:text-teal-700 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to Diagnostic Centres
        </Link>
      </div>

      {error && <ErrorAlert message={error} onRetry={() => fetchData(currentPage)} />}

      {loading ? (
        <div className="py-16">
          <LoadingSpinner label="Loading test offerings..." size="lg" />
        </div>
      ) : (
        <>
          {/* Centre Details Banner */}
          {centre && (
            <div className="bg-white rounded-3xl border border-slate-200 p-6 sm:p-8 shadow-sm">
              <div className="flex items-start gap-4">
                <div className="p-4 bg-teal-600 text-white rounded-2xl shadow-md shadow-teal-200">
                  <Building2 className="w-8 h-8" />
                </div>
                <div>
                  <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                    {centre.name}
                  </h1>
                  {formatCentreAddress(centre, { includePincode: true }) && (
                    <div className="flex items-center gap-2 text-sm text-slate-600 mt-2">
                      <MapPin className="w-4 h-4 text-slate-400 flex-shrink-0" />
                      <span>{formatCentreAddress(centre, { includePincode: true })}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Test List Section */}
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-slate-900">Available Diagnostic Tests</h2>

            {!data || data.results.length === 0 ? (
              <EmptyState
                icon={<TestTube className="w-12 h-12 text-slate-400" />}
                title="No Tests Available"
                message="This centre currently has no active diagnostic test offerings."
              />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {data.results.map((ct) => (
                  <div
                    key={ct.id}
                    className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <div className="p-2.5 bg-slate-100 rounded-xl text-teal-700">
                          <TestTube className="w-5 h-5" />
                        </div>
                        <span className="text-xl font-extrabold text-teal-700 bg-teal-50 px-3 py-1 rounded-xl border border-teal-100">
                          ₹{ct.price}
                        </span>
                      </div>

                      <h3 className="text-lg font-bold text-slate-900 mb-2">
                        {ct.test?.name}
                      </h3>
                      {ct.test?.description && (
                        <p className="text-sm text-slate-600 line-clamp-3 mb-4">
                          {ct.test.description}
                        </p>
                      )}
                    </div>

                    <Link
                      to={`/book/${ct.id}`}
                      className="w-full inline-flex items-center justify-center gap-2 px-4 py-3 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-sm rounded-xl transition-all shadow-md shadow-teal-200 mt-4"
                    >
                      Book Test
                      <ArrowRight className="w-4 h-4" />
                    </Link>
                  </div>
                ))}
              </div>
            )}

            {data && (
              <Pagination
                count={data.count}
                currentPage={currentPage}
                pageSize={20}
                onPageChange={setCurrentPage}
                disabled={loading}
              />
            )}
          </div>
        </>
      )}
    </div>
  );
};
