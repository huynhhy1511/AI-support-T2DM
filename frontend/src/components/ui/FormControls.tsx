import type { ReactNode } from 'react';
import { Calendar, ChevronLeft, ChevronRight } from 'lucide-react';

export function FormField({
  label,
  required = false,
  error,
  hint,
  children,
}: {
  label: string;
  required?: boolean;
  error?: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <div className="dc-form-field">
      <label className="dc-form-label">
        {label}
        {required && <span className="dc-form-required">*</span>}
      </label>
      {children}
      {error && <span className="dc-form-error">{error}</span>}
      {!error && hint && <span className="dc-form-hint">{hint}</span>}
    </div>
  );
}

export function DateSelector({
  value,
  onChange,
}: {
  value: string; // YYYY-MM-DD
  onChange: (nextDate: string) => void;
}) {
  const shiftDate = (delta: number) => {
    const d = new Date(`${value}T00:00:00`);
    d.setDate(d.getDate() + delta);
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    onChange(`${yyyy}-${mm}-${dd}`);
  };

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
      <button
        type="button"
        onClick={() => shiftDate(-1)}
        className="dc-btn dc-btn-secondary dc-btn-sm"
        aria-label="Ngày trước"
        title="Ngày trước"
      >
        <ChevronLeft size={16} />
      </button>
      <div style={{ position: 'relative', display: 'inline-flex', alignItems: 'center' }}>
        <Calendar
          size={15}
          style={{
            position: 'absolute',
            left: 10,
            color: 'var(--dc-text-secondary)',
            pointerEvents: 'none',
          }}
        />
        <input
          type="date"
          value={value}
          onChange={(e) => e.target.value && onChange(e.target.value)}
          className="dc-input"
          style={{ minHeight: 36, paddingLeft: 32, paddingRight: 10, fontSize: 13.5, width: 155 }}
        />
      </div>
      <button
        type="button"
        onClick={() => shiftDate(1)}
        className="dc-btn dc-btn-secondary dc-btn-sm"
        aria-label="Ngày sau"
        title="Ngày sau"
      >
        <ChevronRight size={16} />
      </button>
    </div>
  );
}
