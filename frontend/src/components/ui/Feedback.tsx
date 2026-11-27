import type { ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';
import { PrimaryButton, SecondaryButton } from './Buttons';

export function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  onAction,
}: {
  icon: ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <div
      className="dc-card"
      style={{
        textAlign: 'center',
        padding: '40px 24px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 12,
      }}
    >
      <div
        style={{
          width: 52,
          height: 52,
          borderRadius: 14,
          background: 'var(--dc-primary-soft)',
          color: 'var(--dc-primary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {icon}
      </div>
      <h3 style={{ fontSize: 18 }}>{title}</h3>
      <p style={{ color: 'var(--dc-text-secondary)', maxWidth: 460, fontSize: 14.5 }}>
        {description}
      </p>
      {actionLabel && onAction && (
        <div style={{ marginTop: 8 }}>
          <PrimaryButton onClick={onAction}>{actionLabel}</PrimaryButton>
        </div>
      )}
    </div>
  );
}

export function LoadingSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="dc-card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div className="dc-skeleton" style={{ height: 22, width: '40%' }} />
      {Array.from({ length: rows }).map((_, idx) => (
        <div key={idx} className="dc-skeleton" style={{ height: 54, width: '100%' }} />
      ))}
    </div>
  );
}

export function ConfirmationDialog({
  open,
  title,
  message,
  confirmLabel = 'Xác nhận',
  cancelLabel = 'Hủy',
  onConfirm,
  onCancel,
  danger = false,
}: {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  danger?: boolean;
}) {
  if (!open) return null;

  return (
    <div className="dc-modal-backdrop" role="dialog" aria-modal="true">
      <div className="dc-modal">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
          <AlertTriangle size={22} color={danger ? 'var(--dc-danger)' : 'var(--dc-warning)'} />
          <h3 style={{ fontSize: 18 }}>{title}</h3>
        </div>
        <p style={{ color: 'var(--dc-text-secondary)', fontSize: 14.5, marginBottom: 20 }}>
          {message}
        </p>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
          <SecondaryButton onClick={onCancel}>{cancelLabel}</SecondaryButton>
          <SecondaryButton variant={danger ? 'danger' : 'blue'} onClick={onConfirm}>
            {confirmLabel}
          </SecondaryButton>
        </div>
      </div>
    </div>
  );
}
