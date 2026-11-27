import { useState, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { Bell, ChevronRight } from 'lucide-react';

export interface BreadcrumbItem {
  label: string;
  to?: string;
}

export function Breadcrumb({ items }: { items: BreadcrumbItem[] }) {
  return (
    <nav className="dc-breadcrumb" aria-label="Breadcrumb">
      {items.map((item, idx) => {
        const isLast = idx === items.length - 1;
        return (
          <span key={item.label} style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
            {idx > 0 && <ChevronRight size={14} />}
            {item.to && !isLast ? (
              <Link to={item.to}>{item.label}</Link>
            ) : (
              <span className={isLast ? 'dc-breadcrumb-current' : ''}>{item.label}</span>
            )}
          </span>
        );
      })}
    </nav>
  );
}

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="dc-page-header">
      <div>
        <h1 className="dc-page-title">{title}</h1>
        {subtitle && <p className="dc-page-subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="dc-page-actions">{actions}</div>}
    </div>
  );
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  time: string;
  to?: string;
}

export function NotificationDropdown({
  notifications,
}: {
  notifications: NotificationItem[];
}) {
  const [open, setOpen] = useState(false);

  return (
    <div style={{ position: 'relative' }}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="dc-btn dc-btn-secondary dc-btn-sm"
        style={{ position: 'relative', minHeight: 40, width: 40, padding: 0 }}
        aria-label="Thông báo"
        title="Thông báo"
      >
        <Bell size={18} />
        {notifications.length > 0 && (
          <span
            style={{
              position: 'absolute',
              top: 6,
              right: 7,
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: 'var(--dc-danger)',
            }}
          />
        )}
      </button>

      {open && (
        <div
          className="dc-card"
          style={{
            position: 'absolute',
            right: 0,
            top: 48,
            width: 320,
            padding: 14,
            zIndex: 60,
            boxShadow: 'var(--dc-shadow-md)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <strong style={{ fontSize: 14 }}>Thông báo</strong>
            <button
              type="button"
              onClick={() => setOpen(false)}
              style={{ background: 'none', border: 'none', fontSize: 12, color: 'var(--dc-text-secondary)', cursor: 'pointer' }}
            >
              Đóng
            </button>
          </div>
          {notifications.length === 0 ? (
            <p style={{ fontSize: 13, color: 'var(--dc-text-secondary)' }}>Chưa có thông báo mới.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {notifications.map((n) => (
                <Link
                  key={n.id}
                  to={n.to || '/nutrition'}
                  onClick={() => setOpen(false)}
                  style={{
                    padding: 10,
                    borderRadius: 8,
                    background: 'var(--dc-bg)',
                    display: 'block',
                    textDecoration: 'none',
                  }}
                >
                  <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--dc-text-primary)' }}>
                    {n.title}
                  </div>
                  <div style={{ fontSize: 12.5, color: 'var(--dc-text-secondary)', marginTop: 2 }}>
                    {n.message}
                  </div>
                  <div style={{ fontSize: 11.5, color: 'var(--dc-text-muted)', marginTop: 4 }}>
                    {n.time}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
