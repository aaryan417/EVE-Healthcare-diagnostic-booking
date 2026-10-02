import React, { useState, useEffect, createContext, useContext } from 'react';
import { Link, useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  LayoutDashboard,
  FlaskConical,
  Calendar,
  ClipboardList,
  Building2,
  LogOut,
  ExternalLink,
  ChevronDown,
  Menu,
  X,
  User as UserIcon,
} from 'lucide-react';
import type { CentreAdminCentreItem } from '../../types/centreAdmin';

interface CentreAdminContextType {
  activeCentre: CentreAdminCentreItem | null;
  setActiveCentre: (centre: CentreAdminCentreItem) => void;
  centres: CentreAdminCentreItem[];
}

const CentreAdminContext = createContext<CentreAdminContextType | undefined>(undefined);

export const useCentreAdminContext = () => {
  const context = useContext(CentreAdminContext);
  if (!context) {
    throw new Error('useCentreAdminContext must be used within CentreAdminLayout');
  }
  return context;
};

export const CentreAdminLayout: React.FC = () => {
  const { user, centreAdminProfile, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const centres = centreAdminProfile?.centres || [];

  const [activeCentre, setActiveCentreState] = useState<CentreAdminCentreItem | null>(() => {
    const storedId = localStorage.getItem('active_centre_id');
    if (storedId && centres.length > 0) {
      const found = centres.find((c) => c.id === Number(storedId));
      if (found) return found;
    }
    return centres[0] || null;
  });

  useEffect(() => {
    if (centres.length > 0) {
      if (!activeCentre || !centres.some((c) => c.id === activeCentre.id)) {
        setActiveCentreState(centres[0]);
        localStorage.setItem('active_centre_id', String(centres[0].id));
      }
    }
  }, [centres, activeCentre]);

  const handleCentreChange = (centreId: number) => {
    const selected = centres.find((c) => c.id === centreId);
    if (selected) {
      setActiveCentreState(selected);
      localStorage.setItem('active_centre_id', String(selected.id));
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const navItems = [
    { label: 'Dashboard', path: '/centre-admin', icon: LayoutDashboard },
    { label: 'Tests & Pricing', path: '/centre-admin/tests', icon: FlaskConical },
    { label: 'Appointment Slots', path: '/centre-admin/slots', icon: Calendar },
    { label: 'Bookings', path: '/centre-admin/bookings', icon: ClipboardList },
  ];

  const isActive = (path: string) => {
    if (path === '/centre-admin') {
      return location.pathname === '/centre-admin';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <CentreAdminContext.Provider
      value={{
        activeCentre,
        setActiveCentre: (c) => {
          setActiveCentreState(c);
          localStorage.setItem('active_centre_id', String(c.id));
        },
        centres,
      }}
    >
      <div className="min-h-screen bg-slate-100 flex flex-col md:flex-row">
        {/* Desktop Sidebar */}
        <aside className="hidden md:flex md:w-64 bg-slate-900 text-white flex-col flex-shrink-0 border-r border-slate-800">
          {/* Brand Header */}
          <div className="p-6 border-b border-slate-800">
            <Link to="/centre-admin" className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-teal-500 flex items-center justify-center text-slate-950 font-bold shadow-md shadow-teal-500/20">
                <Building2 className="w-5 h-5" />
              </div>
              <div>
                <span className="font-extrabold text-base tracking-tight block">EVE Healthcare</span>
                <span className="text-xs font-semibold text-teal-400 uppercase tracking-wider block">
                  Centre Admin
                </span>
              </div>
            </Link>
          </div>

          {/* Centre Selector */}
          <div className="p-4 border-b border-slate-800">
            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Managed Centre
            </label>
            {centres.length > 1 ? (
              <div className="relative">
                <select
                  value={activeCentre?.id || ''}
                  onChange={(e) => handleCentreChange(Number(e.target.value))}
                  className="w-full bg-slate-800 border border-slate-700 text-slate-100 text-xs font-medium rounded-xl p-2.5 pr-8 focus:outline-none focus:ring-2 focus:ring-teal-500 appearance-none cursor-pointer"
                >
                  {centres.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
                <ChevronDown className="w-4 h-4 text-slate-400 absolute right-2.5 top-3 pointer-events-none" />
              </div>
            ) : (
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-3 text-xs font-semibold text-slate-200 flex items-center gap-2">
                <Building2 className="w-4 h-4 text-teal-400 flex-shrink-0" />
                <span className="truncate">{activeCentre?.name || 'No Assigned Centre'}</span>
              </div>
            )}
          </div>

          {/* Navigation Links */}
          <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                    active
                      ? 'bg-teal-600 text-white shadow-md shadow-teal-600/30'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/80'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${active ? 'text-white' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Footer Actions */}
          <div className="p-4 border-t border-slate-800 space-y-2">
            <Link
              to="/"
              className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <span className="flex items-center gap-2">
                <ExternalLink className="w-4 h-4 text-slate-400" />
                Patient Portal
              </span>
            </Link>

            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl text-xs font-semibold text-rose-400 hover:text-rose-300 hover:bg-rose-950/40 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              <span>Sign Out</span>
            </button>
          </div>
        </aside>

        {/* Mobile Header */}
        <header className="md:hidden bg-slate-900 text-white border-b border-slate-800 px-4 py-3 flex items-center justify-between sticky top-0 z-50">
          <Link to="/centre-admin" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-teal-500 flex items-center justify-center text-slate-950 font-bold">
              <Building2 className="w-4 h-4" />
            </div>
            <div>
              <span className="font-extrabold text-sm block leading-tight">EVE Healthcare</span>
              <span className="text-[10px] font-semibold text-teal-400 uppercase tracking-wider block">
                Centre Admin
              </span>
            </div>
          </Link>

          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </header>

        {/* Mobile Menu Overlay */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-slate-900 text-white border-b border-slate-800 p-4 space-y-4 shadow-2xl">
            {centres.length > 1 && (
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                  Switch Centre
                </label>
                <select
                  value={activeCentre?.id || ''}
                  onChange={(e) => {
                    handleCentreChange(Number(e.target.value));
                    setMobileMenuOpen(false);
                  }}
                  className="w-full bg-slate-800 border border-slate-700 text-white text-xs font-medium rounded-xl p-2.5"
                >
                  {centres.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <nav className="space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.path);
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold ${
                      active ? 'bg-teal-600 text-white' : 'text-slate-400 hover:bg-slate-800'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>

            <div className="pt-3 border-t border-slate-800 space-y-2">
              <Link
                to="/"
                onClick={() => setMobileMenuOpen(false)}
                className="block text-center px-4 py-2 text-xs font-semibold text-slate-300 bg-slate-800 rounded-xl"
              >
                Go to Patient Portal
              </Link>
              <button
                onClick={handleLogout}
                className="w-full text-center px-4 py-2 text-xs font-semibold text-rose-400 bg-rose-950/40 rounded-xl"
              >
                Sign Out
              </button>
            </div>
          </div>
        )}

        {/* Main Section */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Top Bar for Desktop */}
          <header className="hidden md:flex h-16 bg-white border-b border-slate-200 px-6 items-center justify-between sticky top-0 z-30 shadow-xs">
            <div className="flex items-center gap-3">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Active Centre:
              </span>
              <span className="text-sm font-bold text-slate-800 bg-slate-100 px-3 py-1 rounded-lg border border-slate-200">
                {activeCentre?.name || 'Loading...'}
              </span>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2.5 text-xs font-medium text-slate-700">
                <div className="w-8 h-8 rounded-full bg-teal-50 text-teal-700 font-bold flex items-center justify-center border border-teal-200">
                  <UserIcon className="w-4 h-4" />
                </div>
                <div>
                  <span className="font-bold text-slate-900 block">{user?.name || user?.email}</span>
                  <span className="text-[10px] text-slate-500 block">Centre Admin</span>
                </div>
              </div>

              <Link
                to="/"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-teal-700 bg-teal-50 hover:bg-teal-100 rounded-lg transition-colors border border-teal-200"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                Patient Portal
              </Link>
            </div>
          </header>

          {/* Page Content */}
          <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto max-w-7xl w-full mx-auto">
            <Outlet />
          </main>
        </div>
      </div>
    </CentreAdminContext.Provider>
  );
};
