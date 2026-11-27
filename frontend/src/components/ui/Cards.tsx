import type { ReactNode } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  Apple,
  Beef,
  CheckCircle2,
  Droplets,
  Info,
  Salad,
  ShieldAlert,
  Utensils,
  Wheat,
} from 'lucide-react';
import { NutrientBadge, StatusBadge, type BadgeTone } from './Badges';
import type { RecommendedFoodItem } from '../../types/nutrition';

/** Hình minh họa đồng nhất theo nhóm thực phẩm (không dùng ảnh ngẫu nhiên từ Internet) */
export function FoodVisual({
  category,
  size = 'md',
}: {
  category: string;
  size?: 'sm' | 'md' | 'lg';
}) {
  const cat = category.toLowerCase();
  let Icon = Utensils;
  let bg = 'var(--dc-primary-soft)';
  let fg = 'var(--dc-primary)';

  if (cat.includes('staple') || cat.includes('tinh bột')) {
    Icon = Wheat;
    bg = '#FEF3C7';
    fg = '#B45309';
  } else if (cat.includes('protein') || cat.includes('đạm')) {
    Icon = Beef;
    bg = '#EBF3FC';
    fg = '#2875C7';
  } else if (cat.includes('veg') || cat.includes('rau')) {
    Icon = Salad;
    bg = '#E8F5EF';
    fg = '#16865A';
  } else if (cat.includes('fruit') || cat.includes('trái')) {
    Icon = Apple;
    bg = '#ECFDF3';
    fg = '#16A34A';
  } else if (cat.includes('fat') || cat.includes('dầu') || cat.includes('snack')) {
    Icon = Droplets;
    bg = '#F1F5F9';
    fg = '#475569';
  }

  const dims =
    size === 'lg'
      ? { width: '100%', height: 260, iconSize: 64, radius: 16 }
      : size === 'sm'
        ? { width: 48, height: 48, iconSize: 22, radius: 10 }
        : { width: 64, height: 64, iconSize: 28, radius: 12 };

  return (
    <div
      style={{
        width: dims.width,
        height: dims.height,
        borderRadius: dims.radius,
        background: bg,
        color: fg,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
        border: '1px solid var(--dc-border)',
      }}
    >
      <Icon size={dims.iconSize} />
    </div>
  );
}

export function StatCard({
  label,
  value,
  unit,
  subtitle,
  icon,
  tone = 'primary',
}: {
  label: string;
  value: string | number;
  unit?: string;
  subtitle?: string;
  icon?: ReactNode;
  tone?: 'primary' | 'secondary' | 'warning' | 'danger';
}) {
  const iconBg =
    tone === 'secondary'
      ? 'var(--dc-secondary-soft)'
      : tone === 'warning'
        ? 'var(--dc-warning-bg)'
        : tone === 'danger'
          ? 'var(--dc-danger-bg)'
          : 'var(--dc-primary-soft)';
  const iconColor =
    tone === 'secondary'
      ? 'var(--dc-secondary)'
      : tone === 'warning'
        ? 'var(--dc-warning-text)'
        : tone === 'danger'
          ? 'var(--dc-danger)'
          : 'var(--dc-primary)';

  return (
    <div className="dc-card dc-card-compact" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
        <span style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--dc-text-secondary)' }}>
          {label}
        </span>
        {icon && (
          <div
            style={{
              width: 34,
              height: 34,
              borderRadius: 9,
              background: iconBg,
              color: iconColor,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {icon}
          </div>
        )}
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
        <span style={{ fontSize: 26, fontWeight: 700, color: 'var(--dc-text-primary)' }}>{value}</span>
        {unit && <span style={{ fontSize: 13.5, color: 'var(--dc-text-secondary)' }}>{unit}</span>}
      </div>
      {subtitle && (
        <span style={{ fontSize: 12.5, color: 'var(--dc-text-secondary)' }}>{subtitle}</span>
      )}
    </div>
  );
}

export function NutritionProgressCard({
  title,
  planned,
  actual,
  target,
  unit = 'kcal',
  color = 'var(--dc-primary)',
}: {
  title: string;
  planned: number | null;
  actual: number | null;
  target: number | null;
  unit?: string;
  color?: string;
}) {
  const pct =
    target && target > 0 && actual !== null
      ? Math.min(100, Math.round((actual / target) * 100))
      : target && target > 0 && planned !== null
        ? Math.min(100, Math.round((planned / target) * 100))
        : 0;

  return (
    <div className="dc-card dc-card-compact" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: 14, fontWeight: 600 }}>{title}</span>
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--dc-text-secondary)' }}>
          {target !== null ? `Mục tiêu: ${target} ${unit}` : 'Chưa đủ hồ sơ tính mục tiêu'}
        </span>
      </div>

      <div className="dc-progress-track">
        <div className="dc-progress-fill" style={{ width: `${pct}%`, background: color }} />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: 'var(--dc-text-secondary)', flexWrap: 'wrap', gap: 8 }}>
        <span>Kế hoạch: <strong style={{ color: 'var(--dc-text-primary)' }}>{planned !== null ? `${planned} ${unit}` : 'Chưa tạo'}</strong></span>
        <span>Thực tế: <strong style={{ color: 'var(--dc-primary)' }}>{actual !== null ? `${actual} ${unit}` : 'Chưa ghi nhận'}</strong></span>
      </div>
    </div>
  );
}

export function WarningCard({
  level = 'warning',
  title,
  children,
  action,
}: {
  level?: 'info' | 'warning' | 'error' | 'critical' | 'success';
  title: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  const Icon =
    level === 'critical'
      ? ShieldAlert
      : level === 'error'
        ? AlertCircle
        : level === 'warning'
          ? AlertTriangle
          : level === 'success'
            ? CheckCircle2
            : Info;

  return (
    <div className={`dc-alert dc-alert-${level}`} role="alert">
      <Icon size={20} style={{ flexShrink: 0, marginTop: 2 }} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 700, fontSize: 14.5, marginBottom: 4 }}>{title}</div>
        <div style={{ fontSize: 13.5, lineHeight: 1.5 }}>{children}</div>
        {action && <div style={{ marginTop: 10 }}>{action}</div>}
      </div>
    </div>
  );
}

export function FoodCard({
  item,
  actions,
}: {
  item: RecommendedFoodItem;
  actions?: ReactNode;
}) {
  const kcal = Math.round(item.energy_kcal * item.serving_multiplier);
  const carb = Number((item.carbohydrate_g * item.serving_multiplier).toFixed(1));
  const protein = Number((item.protein_g * item.serving_multiplier).toFixed(1));
  const fat = Number((item.fat_g * item.serving_multiplier).toFixed(1));
  const fiber = item.fiber_g !== null ? Number((item.fiber_g * item.serving_multiplier).toFixed(1)) : null;

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        gap: 14,
        padding: 14,
        borderRadius: 12,
        border: '1px solid var(--dc-border)',
        background: 'var(--dc-surface-subtle)',
        flexWrap: 'wrap',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, flex: 1, minWidth: 220 }}>
        <FoodVisual category={item.category} size="sm" />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <div style={{ fontWeight: 600, fontSize: 15, color: 'var(--dc-text-primary)' }}>
            {item.food_name}
          </div>
          <div style={{ fontSize: 13, color: 'var(--dc-text-secondary)' }}>
            Khẩu phần: <strong>{Math.round(item.serving_size_g * item.serving_multiplier)}g</strong>{' '}
            ({item.serving_multiplier}x suất chuẩn) · <strong>{kcal} kcal</strong>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            <NutrientBadge label="Carb" value={carb} tone="info" />
            <NutrientBadge label="Đạm" value={protein} tone="success" />
            <NutrientBadge label="Béo" value={fat} tone="neutral" />
            <NutrientBadge label="Xơ" value={fiber} tone="neutral" />
            {item.glycemic_index !== null && item.glycemic_index !== undefined && (
              <NutrientBadge
                label="GI"
                value={item.glycemic_index}
                unit=""
                tone={item.glycemic_index <= 55 ? 'success' : item.glycemic_index <= 69 ? 'warning' : 'danger'}
              />
            )}
          </div>
          {item.item_warning && (
            <div style={{ fontSize: 12.5, color: 'var(--dc-warning-text)' }}>
              Lưu ý: {item.item_warning}
            </div>
          )}
        </div>
      </div>
      {actions && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          {actions}
        </div>
      )}
    </div>
  );
}

export function MealCard({
  title,
  timeRange,
  totalKcal,
  statusLabel,
  statusTone = 'neutral',
  categoryHint = 'vegetables',
  children,
  footer,
}: {
  title: string;
  timeRange: string;
  totalKcal: number;
  statusLabel: string;
  statusTone?: BadgeTone;
  categoryHint?: string;
  children?: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="dc-card" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <FoodVisual category={categoryHint} size="sm" />
          <div>
            <h3 style={{ fontSize: 17 }}>{title}</h3>
            <span style={{ fontSize: 13, color: 'var(--dc-text-secondary)' }}>
              {timeRange} · <strong>{Math.round(totalKcal)} kcal</strong>
            </span>
          </div>
        </div>
        <StatusBadge tone={statusTone}>{statusLabel}</StatusBadge>
      </div>

      {children}

      {footer && (
        <div
          style={{
            borderTop: '1px solid var(--dc-border)',
            paddingTop: 12,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 10,
            flexWrap: 'wrap',
          }}
        >
          {footer}
        </div>
      )}
    </div>
  );
}
