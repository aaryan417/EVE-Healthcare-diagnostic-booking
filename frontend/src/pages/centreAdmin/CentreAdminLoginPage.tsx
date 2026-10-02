import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ErrorAlert } from '../../components/common/ErrorAlert';
import { Mail, Lock, LogIn, Building2, ShieldAlert, ArrowLeft } from 'lucide-react';

export const CentreAdminLoginPage: React.FC = () => {
  const { login, isAuthenticated, centreAdminProfile } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [accessDenied, setAccessDenied] = useState<boolean>(false);
  const [loading, setLoading] = useState(false);

  const from = (location.state as any)?.from?.pathname || '/centre-admin';

  // If already logged in as Centre Admin, redirect immediately
  useEffect(() => {
    if (isAuthenticated && centreAdminProfile?.is_centre_admin) {
      navigate('/centre-admin', { replace: true });
    }
  }, [isAuthenticated, centreAdminProfile, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setAccessDenied(false);

    if (!email.trim() || !password) {
      setError('Please fill in all required fields.');
      return;
    }

    try {
      setLoading(true);
      const profile = await login({ email: email.trim(), password });

      if (profile?.is_centre_admin) {
        navigate(from.startsWith('/centre-admin') ? from : '/centre-admin', { replace: true });
      } else {
        setAccessDenied(true);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to authenticate. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto my-12">
      <div className="bg-white rounded-3xl border border-slate-200 p-8 shadow-sm">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-2xl bg-teal-700 text-white flex items-center justify-center mx-auto mb-3 shadow-md shadow-teal-200">
            <Building2 className="w-6 h-6" />
          </div>
          <span className="inline-block px-3 py-1 bg-teal-50 text-teal-700 border border-teal-200 text-xs font-bold rounded-full mb-2">
            Centre Admin Portal
          </span>
          <h2 className="text-2xl font-black text-slate-900">EVE Healthcare</h2>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Manage your diagnostic centre, tests, appointment slots and bookings.
          </p>
        </div>

        {error && <ErrorAlert message={error} />}

        {/* Access Denied State for Non-Admin Authenticated Users */}
        {accessDenied ? (
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 text-center space-y-4 my-4">
            <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center mx-auto">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Access Restricted</h3>
              <p className="text-xs text-slate-600 mt-1">
                Your account does not have Centre Admin access. No active CentreMembership is assigned to your account.
              </p>
            </div>
            <div className="pt-2">
              <Link
                to="/"
                className="inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl transition-all shadow-sm"
              >
                <ArrowLeft className="w-4 h-4" /> Go to Patient Portal
              </Link>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                Administrator Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Mail className="w-5 h-5" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="centreadmin@clinic.com"
                  className="w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Lock className="w-5 h-5" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition-all"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full inline-flex items-center justify-center gap-2 py-3.5 px-4 bg-teal-700 hover:bg-teal-800 text-white font-bold text-sm rounded-xl transition-all shadow-md shadow-teal-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                'Authenticating...'
              ) : (
                <>
                  <LogIn className="w-4 h-4" />
                  Sign in to Centre Portal
                </>
              )}
            </button>
          </form>
        )}

        <div className="mt-8 pt-6 border-t border-slate-100 text-center space-y-3">
          <p className="text-xs text-slate-400">
            Only authorized centre administrators can access this portal.
          </p>
          <p className="text-sm text-slate-600">
            Patient?{' '}
            <Link to="/login" className="font-semibold text-teal-600 hover:text-teal-800">
              Go to Patient Login
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};
