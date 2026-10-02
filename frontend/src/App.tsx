import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './routes/ProtectedRoute';
import { CentreAdminProtectedRoute } from './routes/CentreAdminProtectedRoute';
import { Navbar } from './components/layout/Navbar';
import { Footer } from './components/layout/Footer';
import { CentreAdminLayout } from './components/centreAdmin/CentreAdminLayout';

import { HomePage } from './pages/HomePage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { CentresPage } from './pages/CentresPage';
import { CentreTestsPage } from './pages/CentreTestsPage';
import { BookingPage } from './pages/BookingPage';
import { PaymentPage } from './pages/PaymentPage';
import { MyBookingsPage } from './pages/MyBookingsPage';

import { DashboardPage } from './pages/centreAdmin/DashboardPage';
import { TestsPricingPage } from './pages/centreAdmin/TestsPricingPage';
import { SlotsPage } from './pages/centreAdmin/SlotsPage';
import { BookingsPage } from './pages/centreAdmin/BookingsPage';
import { CentreAdminLoginPage } from './pages/centreAdmin/CentreAdminLoginPage';

export const App: React.FC = () => {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Protected Centre Admin Dashboard Routes (Full Layout) */}
          <Route
            path="/centre-admin"
            element={
              <CentreAdminProtectedRoute>
                <CentreAdminLayout />
              </CentreAdminProtectedRoute>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="tests" element={<TestsPricingPage />} />
            <Route path="slots" element={<SlotsPage />} />
            <Route path="bookings" element={<BookingsPage />} />
          </Route>

          {/* Patient App Layout Routes */}
          <Route
            path="*"
            element={
              <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans antialiased">
                <Navbar />
                <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
                  <Routes>
                    {/* Public Routes */}
                    <Route path="/" element={<HomePage />} />
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/register" element={<RegisterPage />} />
                    <Route path="/centre-admin/login" element={<CentreAdminLoginPage />} />
                    <Route path="/centres" element={<CentresPage />} />
                    <Route path="/centres/:centreId/tests" element={<CentreTestsPage />} />

                    {/* Protected Patient Routes */}
                    <Route
                      path="/book/:centreTestId"
                      element={
                        <ProtectedRoute>
                          <BookingPage />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/payment/:bookingId"
                      element={
                        <ProtectedRoute>
                          <PaymentPage />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/my-bookings"
                      element={
                        <ProtectedRoute>
                          <MyBookingsPage />
                        </ProtectedRoute>
                      }
                    />

                    {/* Fallback 404 Route */}
                    <Route path="*" element={<CentresPage />} />
                  </Routes>
                </main>
                <Footer />
              </div>
            }
          />
        </Routes>
      </AuthProvider>
    </Router>
  );
};

export default App;
