import type { ReactNode } from 'react';

export type BadgeTone = 'success' | 'warning' | 'danger' | 'info' | 'neutral';

export function StatusBadge({
  tone = 'neutral',
  children,
  icon,
}: {
  tone?: BadgeTone;
  children: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <span className={`dc-badge dc-badge-${tone}`}>
      {icon}
      <span>{children}</span>
    </span>
  );
}

export function NutrientBadge({
  label,
  value,
  unit = 'g',
  tone = 'neutral',
}: {
  label: string;
  value: number | null | undefined;
  unit?: string;
  tone?: BadgeTone;
}) {
  const display = value === null || value === undefined ? 'Chưa có' : `${value}${unit}`;
  return (
    <span className={`dc-badge dc-badge-${tone}`}>
      <span>{label}:</span>
      <strong>{display}</strong>
    </span>
  );
}
