import React from 'react';
import { Calendar as CalendarIcon, Check } from 'lucide-react';

interface CalendarSelectorProps {
  availableDates: string[];
  selectedDate: string;
  onSelectDate: (date: string) => void;
}

export const CalendarSelector: React.FC<CalendarSelectorProps> = ({
  availableDates,
  selectedDate,
  onSelectDate,
}) => {
  if (!availableDates || availableDates.length === 0) {
    return (
      <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 text-center text-amber-900">
        <CalendarIcon className="w-8 h-8 text-amber-600 mx-auto mb-2" />
        <p className="font-semibold text-sm">No appointment dates available</p>
        <p className="text-xs text-amber-700 mt-1">
          There are currently no open slots for this test. Please check back later or select another test.
        </p>
      </div>
    );
  }

  // Format date helper (YYYY-MM-DD to friendly label e.g., Mon, Oct 5)
  const formatDateLabel = (dateStr: string) => {
    try {
      const [year, month, day] = dateStr.split('-').map(Number);
      const date = new Date(year, month - 1, day);
      const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });
      const monthName = date.toLocaleDateString('en-US', { month: 'short' });
      return { dayName, monthName, dayNumber: day };
    } catch {
      return { dayName: '', monthName: '', dayNumber: dateStr };
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="block text-sm font-semibold text-slate-900">
          Select Appointment Date
        </label>
        <span className="text-xs text-slate-500">
          {availableDates.length} date{availableDates.length > 1 ? 's' : ''} available
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {availableDates.map((dateStr) => {
          const { dayName, monthName, dayNumber } = formatDateLabel(dateStr);
          const isSelected = selectedDate === dateStr;

          return (
            <button
              key={dateStr}
              type="button"
              onClick={() => onSelectDate(dateStr)}
              className={`p-4 rounded-xl border text-left transition-all flex flex-col justify-between relative ${
                isSelected
                  ? 'bg-teal-600 border-teal-600 text-white shadow-md shadow-teal-200 ring-2 ring-teal-600 ring-offset-2'
                  : 'bg-white border-slate-200 text-slate-800 hover:border-teal-500 hover:bg-teal-50/50'
              }`}
            >
              {isSelected && (
                <div className="absolute top-2 right-2 w-5 h-5 bg-white text-teal-600 rounded-full flex items-center justify-center">
                  <Check className="w-3.5 h-3.5 stroke-[3]" />
                </div>
              )}
              <span className={`text-xs font-semibold uppercase tracking-wider ${isSelected ? 'text-teal-100' : 'text-slate-400'}`}>
                {dayName}
              </span>
              <div className="my-1">
                <span className="text-2xl font-bold tracking-tight">{dayNumber}</span>
                <span className={`text-sm font-medium ml-1.5 ${isSelected ? 'text-teal-100' : 'text-slate-500'}`}>
                  {monthName}
                </span>
              </div>
              <span className={`text-[11px] ${isSelected ? 'text-teal-100 font-medium' : 'text-slate-400'}`}>
                {dateStr}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
