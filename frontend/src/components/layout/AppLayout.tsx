import { useState, type ReactNode } from 'react';
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom';
import {
  Activity,
  Bot,
  CalendarDays,
  ClipboardList,
  Dumbbell,
  HeartPulse,
  LayoutDashboard,
  LogOut,
  Menu,
  Settings,
  ShieldAlert,
  Sparkles,
  TrendingUp,
  UserCircle,
  Utensils,
  X,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import {
  Breadcrumb,
  NotificationDropdown,
  type BreadcrumbItem,
  type NotificationItem,
} from '../ui/NavigationUI';

const SIDEBAR_ITEMS = [
  { to: '/dashboard', label: 'Tổng quan', icon: LayoutDashboard },
  { to: '/nutrition', label: 'Dinh dưỡng', icon: Utensils },
  { to: '/ai-consultation', label: 'Tư vấn AI', icon: Bot },
  { to: '/exercise', label: 'Luyện tập', icon: Dumbbell },
  { to: '/health-tracking', label: 'Theo dõi sức khỏe', icon: Activity },
  { to: '/nutrition/profile', label: 'Hồ sơ cá nhân', icon: UserCircle },
];

const NUTRITION_SUBNAV = [
  { to: '/nutrition', label: 'Tổng quan', end: true, icon: LayoutDashboard },
  { to: '/nutrition/daily', label: 'Thực đơn ngày', end: false, icon: CalendarDays },
  { to: '/nutrition/generate', label: 'Tạo thực đơn AI', end: false, icon: Sparkles },
  { to: '/nutrition/diary', label: 'Nhật ký ăn uống', end: false, icon: ClipboardList },
  { to: '/nutrition/progress', label: 'Tiến triển', end: false, icon: TrendingUp },
  { to: '/nutrition/profile', label: 'Hồ sơ dinh dưỡng', end: false, icon: UserCircle },
  { to: '/nutrition/safety', label: 'Cảnh báo an toàn', end: false, icon: ShieldAlert },
  { to: '/nutrition/explanation', label: 'Giải thích AI', end: false, icon: Bot },
];

const DEFAULT_NOTIFICATIONS: NotificationItem[] = [
  {
    id: 'n1',
    title: 'Kiểm tra hồ sơ dinh dưỡng',
    message: 'Cập nhật chiều cao, cân nặng và dị ứng để tính năng lượng chính xác.',
    time: 'Hôm nay',
    to: '/nutrition/profile',
  },
  {
    id: 'n2',
    title: 'Nhắc ghi nhận nhật ký ăn uống',
    message: 'Ghi nhận bữa ăn thực tế giúp theo dõi kế hoạch dinh dưỡng tốt hơn.',
    time: 'Hôm nay',
    to: '/nutrition/diary',
  },
];

export function AppLayout({
  breadcrumbs,
  children,
}: {
  breadcrumbs: BreadcrumbItem[];
  children: ReactNode;
}) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);

  const isNutritionSection = location.pathname.startsWith('/nutrition');
  const initials = (user?.full_name || 'U')
    .split(' ')
    .filter(Boolean)
    .slice(-2)
    .map((p) => p[0]?.toUpperCase())
    .join('');

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="dc-app-shell">
      {/* Mobile Drawer Backdrop */}
      <div
        className={`dc-drawer-backdrop ${mobileMenuOpen ? 'open' : ''}`}
        onClick={() => setMobileMenuOpen(false)}
      />

      {/* Unified Fixed Left Sidebar (240px) */}
      <aside className={`dc-sidebar ${mobileMenuOpen ? 'open' : ''}`} aria-label="Menu chính">
        <div>
          <div className="dc-brand">
            <div className="dc-brand-logo">
              <HeartPulse size={22} />
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="dc-brand-name">Diabetes Care</div>
              <div className="dc-brand-sub">Quản lý ĐTĐ Type 2</div>
            </div>
            <button
              type="button"
              className="dc-mobile-menu-btn"
              onClick={() => setMobileMenuOpen(false)}
              aria-label="Đóng menu"
              style={{ width: 32, height: 32 }}
            >
              <X size={16} />
            </button>
          </div>

          <nav className="dc-nav-group">
            {SIDEBAR_ITEMS.map((item) => {
              const Icon = item.icon;
              const isNutritionMenu = item.to === '/nutrition';
              const isActive = isNutritionMenu
                ? location.pathname.startsWith('/nutrition') &&
                  location.pathname !== '/nutrition/profile'
                : location.pathname === item.to;

              return (
                <Link
                  key={item.to}
                  to={item.to}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`dc-nav-item ${isActive ? 'active' : ''}`}
                  title={item.label}
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="dc-sidebar-footer">
          <Link
            to="/settings"
            onClick={() => setMobileMenuOpen(false)}
            className={`dc-nav-item ${location.pathname === '/settings' ? 'active' : ''}`}
            title="Cài đặt"
          >
            <Settings size={18} />
            <span>Cài đặt</span>
          </Link>
          <button
            type="button"
            onClick={handleLogout}
            className="dc-nav-item danger"
            title="Đăng xuất"
          >
            <LogOut size={18} />
            <span>Đăng xuất</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="dc-main-wrapper">
        {/* Unified Top Header (70px) */}
        <header className="dc-header">
          <div className="dc-header-left">
            <button
              type="button"
              className="dc-mobile-menu-btn"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Mở menu điều hướng"
            >
              <Menu size={20} />
            </button>
            <Breadcrumb items={breadcrumbs} />
          </div>

          <div className="dc-header-right">
            <NotificationDropdown notifications={DEFAULT_NOTIFICATIONS} />

            <div style={{ position: 'relative' }}>
              <button
                type="button"
                onClick={() => setAccountMenuOpen((v) => !v)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '5px 10px 5px 6px',
                  borderRadius: 999,
                  border: '1px solid var(--dc-border)',
                  background: 'var(--dc-surface)',
                  cursor: 'pointer',
                }}
              >
                <span
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    background: 'var(--dc-primary-soft)',
                    color: 'var(--dc-primary)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                    fontSize: 13,
                  }}
                >
                  {initials}
                </span>
                <span style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--dc-text-primary)' }}>
                  {user?.full_name || 'Người dùng'}
                </span>
              </button>

              {accountMenuOpen && (
                <div
                  className="dc-card"
                  style={{
                    position: 'absolute',
                    right: 0,
                    top: 48,
                    width: 220,
                    padding: 8,
                    zIndex: 60,
                    boxShadow: 'var(--dc-shadow-md)',
                  }}
                >
                  <div style={{ padding: '8px 12px', borderBottom: '1px solid var(--dc-border)', marginBottom: 6 }}>
                    <div style={{ fontSize: 13.5, fontWeight: 700 }}>{user?.full_name}</div>
                    <div style={{ fontSize: 12, color: 'var(--dc-text-secondary)' }}>{user?.email}</div>
                  </div>
                  <Link
                    to="/nutrition/profile"
                    className="dc-nav-item"
                    onClick={() => setAccountMenuOpen(false)}
                  >
                    <UserCircle size={16} />
                    <span>Hồ sơ dinh dưỡng</span>
                  </Link>
                  <Link
                    to="/settings"
                    className="dc-nav-item"
                    onClick={() => setAccountMenuOpen(false)}
                  >
                    <Settings size={16} />
                    <span>Cài đặt</span>
                  </Link>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="dc-nav-item danger"
                  >
                    <LogOut size={16} />
                    <span>Đăng xuất</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        <main className="dc-main-content">
          {isNutritionSection && (
            <nav className="dc-subnav" aria-label="Điều hướng phân hệ Dinh dưỡng">
              {NUTRITION_SUBNAV.map((tab) => {
                const Icon = tab.icon;
                return (
                  <NavLink
                    key={tab.to}
                    to={tab.to}
                    end={tab.end}
                    className={({ isActive }) => `dc-subnav-link ${isActive ? 'active' : ''}`}
                  >
                    <Icon size={15} />
                    <span>{tab.label}</span>
                  </NavLink>
                );
              })}
            </nav>
          )}
          {children}
        </main>
      </div>
    </div>
  );
}
