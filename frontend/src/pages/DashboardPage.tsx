import { useState, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Bot,
  Dumbbell,
  LayoutDashboard,
  LogOut,
  ShieldCheck,
  TrendingUp,
  UserCircle,
  Utensils,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

type MenuKey =
  | 'overview'
  | 'ai'
  | 'nutrition'
  | 'exercise'
  | 'progress'
  | 'profile';

interface MenuItem {
  key: MenuKey;
  label: string;
  icon: ReactNode;
  description: string;
  colorClass: 'blue' | 'teal';
}

const MENU_ITEMS: MenuItem[] = [
  {
    key: 'overview',
    label: 'Tổng quan',
    icon: <LayoutDashboard size={18} />,
    description: 'Theo dõi nhanh tình trạng đường huyết, mục tiêu dinh dưỡng và nhắc nhở hằng ngày.',
    colorClass: 'blue',
  },
  {
    key: 'ai',
    label: 'Trợ lý AI',
    icon: <Bot size={18} />,
    description: 'Đặt câu hỏi về chế độ sinh hoạt, đọc hiểu chỉ số đường huyết và nhận giải đáp an toàn.',
    colorClass: 'teal',
  },
  {
    key: 'nutrition',
    label: 'Dinh dưỡng',
    icon: <Utensils size={18} />,
    description: 'Gợi ý thực đơn cân bằng đường huyết, kiểm soát natri, chất béo bão hòa và dị ứng thực phẩm.',
    colorClass: 'blue',
  },
  {
    key: 'exercise',
    label: 'Tập luyện',
    icon: <Dumbbell size={18} />,
    description: 'Lịch vận động phù hợp thể trạng giúp cải thiện độ nhạy insulin an toàn.',
    colorClass: 'teal',
  },
  {
    key: 'progress',
    label: 'Tiến trình',
    icon: <TrendingUp size={18} />,
    description: 'Biểu đồ xu hướng đường huyết đói, sau ăn và lịch sử tuân thủ mục tiêu.',
    colorClass: 'blue',
  },
  {
    key: 'profile',
    label: 'Hồ sơ',
    icon: <UserCircle size={18} />,
    description: 'Quản lý thông tin cá nhân, dị ứng thực phẩm, chế độ ăn (chay/thuần chay) và mục tiêu năng lượng.',
    colorClass: 'teal',
  },
];

export function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<MenuKey>('overview');

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  const userInitial = user?.full_name?.trim().charAt(0).toUpperCase() || 'U';
  const activeMenu = MENU_ITEMS.find((item) => item.key === activeTab) || MENU_ITEMS[0];
  const shortcutCards = MENU_ITEMS.filter((item) => item.key !== 'overview');

  return (
    <div className="dashboard-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="topbar-brand">
            <div className="brand-icon" style={{ width: 38, height: 38 }}>
              <Activity size={20} />
            </div>
            <div>
              <div className="brand-title">DiaCare AI</div>
              <div className="brand-subtitle">Quản lý Đái tháo đường Type 2</div>
            </div>
          </div>

          <div className="topbar-user">
            <div className="user-badge">
              <div className="user-avatar" aria-hidden="true">
                {userInitial}
              </div>
              <div className="user-info">
                <span className="user-name">{user?.full_name || 'Người dùng'}</span>
                <span className="user-email">{user?.email}</span>
              </div>
            </div>

            <button type="button" className="btn btn-outline" onClick={handleLogout}>
              <LogOut size={16} />
              <span>Đăng xuất</span>
            </button>
          </div>
        </div>
      </header>

      <nav className="nav-bar" aria-label="Menu chính">
        <div className="nav-bar-inner">
          {MENU_ITEMS.map((item) => (
            <button
              key={item.key}
              type="button"
              className={`nav-item ${activeTab === item.key ? 'active' : ''}`}
              onClick={() => setActiveTab(item.key)}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      </nav>

      <main className="dashboard-main">
        <section className="hero-banner">
          <div>
            <h1 className="hero-title">
              Xin chào, {user?.full_name || 'bạn'}!
            </h1>
            <p className="hero-desc">
              Chào mừng bạn đến với bảng điều khiển chăm sóc sức khỏe. Hệ thống giúp bạn
              theo dõi đường huyết và gợi ý thực đơn an toàn theo đúng hồ sơ cá nhân.
            </p>
          </div>
          <div className="hero-pill">
            <ShieldCheck size={18} />
            <span>Đã kích hoạt bảo vệ ràng buộc dị ứng</span>
          </div>
        </section>

        {activeTab !== 'overview' && (
          <section className="section-panel" aria-live="polite">
            <h2>Phân hệ: {activeMenu.label}</h2>
            <p>{activeMenu.description}</p>
          </section>
        )}

        <h2 className="section-title">Lối tắt chức năng</h2>
        <div className="shortcut-grid">
          {shortcutCards.map((card) => (
            <button
              key={card.key}
              type="button"
              className="shortcut-card"
              onClick={() => setActiveTab(card.key)}
            >
              <div className={`shortcut-icon ${card.colorClass}`}>{card.icon}</div>
              <h3>{card.label}</h3>
              <p>{card.description}</p>
              <span className="shortcut-action">
                Mở {card.label.toLowerCase()} <ArrowRight size={15} />
              </span>
            </button>
          ))}
        </div>

        <aside className="disclaimer-box" role="note" aria-label="Khuyến cáo y tế">
          <AlertTriangle size={22} className="disclaimer-icon" />
          <div>
            <p className="disclaimer-title">Khuyến cáo miễn trừ trách nhiệm y tế</p>
            <p className="disclaimer-text">
              Ứng dụng <strong>DiaCare AI</strong> chỉ đóng vai trò công cụ hỗ trợ tự quản lý
              dinh dưỡng, vận động và theo dõi chỉ số cho người bệnh Đái tháo đường Type 2.
              Các thông tin và gợi ý từ hệ thống <strong>không thay thế</strong> chẩn đoán,
              tư vấn y khoa hay phác đồ điều trị của bác sĩ chuyên khoa. Khi có dấu hiệu hạ
              hoặc tăng đường huyết bất thường, vui lòng liên hệ ngay cơ sở y tế gần nhất.
            </p>
          </div>
        </aside>
      </main>
    </div>
  );
}
