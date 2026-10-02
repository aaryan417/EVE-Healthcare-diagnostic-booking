import React, { useState, useEffect } from 'react';
import { diagnosticsApi } from '../api/diagnostics';
import type { DiagnosticCentre, PaginatedResponse } from '../types/api';
import { CentreCard } from '../components/centres/CentreCard';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ErrorAlert } from '../components/common/ErrorAlert';
import { EmptyState } from '../components/common/EmptyState';
import { Pagination } from '../components/common/Pagination';
import { getErrorMessage } from '../utils/errorHandler';
import { Building2 } from 'lucide-react';

export const CentresPage: React.FC = () => {
  const [data, setData] = useState<PaginatedResponse<DiagnosticCentre> | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCentres = async (page: number) => {
    try {
      setLoading(true);
      setError(null);
      const res = await diagnosticsApi.getCentres(page);
      setData(res);
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load diagnostic centres.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCentres(currentPage);
  }, [currentPage]);

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="space-y-8 py-4">
      {/* Header */}
      <div className="border-b border-slate-200 pb-6">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Diagnostic Centres
        </h1>
        <p className="text-sm text-slate-600 mt-1">
          Select a verified centre to view available tests and schedule your appointment.
        </p>
      </div>

      {error && <ErrorAlert message={error} onRetry={() => fetchCentres(currentPage)} />}

      {loading ? (
        <div className="py-16">
          <LoadingSpinner label="Fetching diagnostic centres..." size="lg" />
        </div>
      ) : !data || data.results.length === 0 ? (
        <EmptyState
          icon={<Building2 className="w-12 h-12 text-slate-400" />}
          title="No Diagnostic Centres Found"
          message="There are currently no active diagnostic centres listed in the network."
        />
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data.results.map((centre) => (
              <CentreCard key={centre.id} centre={centre} />
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
