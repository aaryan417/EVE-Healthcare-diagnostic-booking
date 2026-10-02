import React from 'react';
import { Navigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ShieldAlert, ArrowLeft } from 'lucide-react';

export const CentreAdminProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, centreAdminProfile, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <LoadingSpinner label="Verifying Centre Admin permissions..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/centre-admin/login" state={{ from: location }} replace />;
  }

  if (!centreAdminProfile?.is_centre_admin) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-3xl border border-slate-200 p-8 shadow-sm text-center">
          <div className="w-14 h-14 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center mx-auto mb-4 border border-amber-200">
            <ShieldAlert className="w-7 h-7" />
          </div>
          <h2 className="text-xl font-bold text-slate-900 mb-2">Access Restricted</h2>
          <p className="text-sm text-slate-600 mb-6">
            Your account is authenticated as a Patient. You do not have permission to access the Centre Admin Dashboard because no active Centre Admin membership is assigned to your account.
          </p>
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-sm rounded-xl transition-all shadow-sm shadow-teal-200"
          >
            <ArrowLeft className="w-4 h-4" />
            Return to Patient Portal
          </Link>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};
