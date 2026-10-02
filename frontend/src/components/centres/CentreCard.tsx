import React from 'react';
import { Link } from 'react-router-dom';
import type { DiagnosticCentre } from '../../types/api';
import { formatCentreAddress } from '../../utils/address';
import { Building2, MapPin, ArrowRight } from 'lucide-react';

interface CentreCardProps {
  centre: DiagnosticCentre;
}

export const CentreCard: React.FC<CentreCardProps> = ({ centre }) => {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-all flex flex-col justify-between group">
      <div>
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="p-3 bg-teal-50 rounded-xl text-teal-700 group-hover:bg-teal-600 group-hover:text-white transition-colors">
            <Building2 className="w-6 h-6" />
          </div>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            Verified Centre
          </span>
        </div>

        <h3 className="text-lg font-bold text-slate-900 mb-2 group-hover:text-teal-700 transition-colors">
          {centre.name}
        </h3>

        {formatCentreAddress(centre, { includePincode: true }) && (
          <div className="flex items-start gap-2 text-sm text-slate-600 mb-4">
            <MapPin className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
            <span>{formatCentreAddress(centre, { includePincode: true })}</span>
          </div>
        )}
      </div>

      <Link
        to={`/centres/${centre.id}/tests`}
        className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-900 hover:bg-teal-600 text-white font-semibold text-sm rounded-xl transition-colors shadow-sm"
      >
        View Available Tests
        <ArrowRight className="w-4 h-4" />
      </Link>
    </div>
  );
};
