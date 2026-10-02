import React from 'react';
import { Link } from 'react-router-dom';
import { Building2, TestTube, Calendar, CreditCard, ArrowRight, ShieldCheck, Clock, Award } from 'lucide-react';

export const HomePage: React.FC = () => {
  return (
    <div className="space-y-16 py-8">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-teal-900 via-slate-900 to-slate-950 text-white rounded-3xl p-8 sm:p-12 lg:p-16 shadow-xl">
        <div className="max-w-3xl relative z-10 space-y-6">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-teal-500/20 text-teal-300 border border-teal-500/30 backdrop-blur-sm">
            <ShieldCheck className="w-4 h-4 text-teal-400" />
            Verified Diagnostic Network
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight">
            Book Diagnostic Tests With <span className="text-teal-400">Confidence</span>
          </h1>

          <p className="text-lg text-slate-300 leading-relaxed max-w-2xl">
            Access top diagnostic centers near you, transparent pricing, real-time appointment slot availability, and instant confirmation.
          </p>

          <div className="flex flex-wrap gap-4 pt-4">
            <Link
              to="/centres"
              className="inline-flex items-center gap-2 px-6 py-3.5 bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-base rounded-xl transition-all shadow-lg shadow-teal-500/25 hover:scale-[1.02]"
            >
              Find a Diagnostic Centre
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </div>

        {/* Decorative background grid */}
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-96 h-96 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />
      </section>

      {/* 4-Step Process Section */}
      <section className="space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <h2 className="text-3xl font-extrabold text-slate-900">How It Works</h2>
          <p className="text-slate-600 text-sm">
            Simple, seamless diagnostic booking in four easy steps
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-all">
            <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center font-bold text-lg mb-4">
              <Building2 className="w-6 h-6" />
            </div>
            <span className="text-xs font-bold text-teal-600 uppercase tracking-wider block mb-1">Step 1</span>
            <h3 className="text-lg font-bold text-slate-900 mb-2">Choose Centre</h3>
            <p className="text-sm text-slate-600">
              Browse accredited diagnostic centers in your area with full address and details.
            </p>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-all">
            <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center font-bold text-lg mb-4">
              <TestTube className="w-6 h-6" />
            </div>
            <span className="text-xs font-bold text-teal-600 uppercase tracking-wider block mb-1">Step 2</span>
            <h3 className="text-lg font-bold text-slate-900 mb-2">Select Test</h3>
            <p className="text-sm text-slate-600">
              View available diagnostic test packages and transparent centre-specific pricing.
            </p>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-all">
            <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center font-bold text-lg mb-4">
              <Calendar className="w-6 h-6" />
            </div>
            <span className="text-xs font-bold text-teal-600 uppercase tracking-wider block mb-1">Step 3</span>
            <h3 className="text-lg font-bold text-slate-900 mb-2">Pick Slot</h3>
            <p className="text-sm text-slate-600">
              Select your preferred appointment date and real-time available time slot.
            </p>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-all">
            <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center font-bold text-lg mb-4">
              <CreditCard className="w-6 h-6" />
            </div>
            <span className="text-xs font-bold text-teal-600 uppercase tracking-wider block mb-1">Step 4</span>
            <h3 className="text-lg font-bold text-slate-900 mb-2">Pay & Confirm</h3>
            <p className="text-sm text-slate-600">
              Complete simulated payment to lock your slot and receive instant confirmation.
            </p>
          </div>
        </div>
      </section>

      {/* Feature Highlights */}
      <section className="bg-slate-100 rounded-3xl p-8 sm:p-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-white rounded-xl text-teal-600 shadow-sm">
              <Clock className="w-6 h-6" />
            </div>
            <div>
              <h4 className="font-bold text-slate-900 mb-1">Real-Time Availability</h4>
              <p className="text-xs text-slate-600 leading-relaxed">
                Slot capacities update live to guarantee zero double bookings.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="p-3 bg-white rounded-xl text-teal-600 shadow-sm">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <h4 className="font-bold text-slate-900 mb-1">Price Guarantee</h4>
              <p className="text-xs text-slate-600 leading-relaxed">
                Server-side price snapshots ensure the price at booking never changes.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="p-3 bg-white rounded-xl text-teal-600 shadow-sm">
              <Award className="w-6 h-6" />
            </div>
            <div>
              <h4 className="font-bold text-slate-900 mb-1">Instant Confirmation</h4>
              <p className="text-xs text-slate-600 leading-relaxed">
                Receive booking IDs and confirmation details immediately after payment.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
