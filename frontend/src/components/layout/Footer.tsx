import React from 'react';
import { Activity } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 text-slate-400 py-10 border-t border-slate-800 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-2.5 text-white font-bold text-lg">
            <div className="w-7 h-7 rounded-lg bg-teal-500 flex items-center justify-center text-slate-900">
              <Activity className="w-4 h-4" />
            </div>
            <span>EVE Healthcare</span>
          </div>

          <p className="text-xs text-slate-500 text-center md:text-right">
            © {new Date().getFullYear()} EVE Healthcare Diagnostic Booking Platform. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};
