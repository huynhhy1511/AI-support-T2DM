import { useNavigate } from 'react-router-dom';
import {
  Activity,
  ArrowRight,
  Bot,
  Dumbbell,
  ShieldCheck,
  Utensils,
} from 'lucide-react';
import { AppLayout } from '../components/layout/AppLayout';
import { useAuth } from '../context/AuthContext';
import { PrimaryButton, SecondaryButton } from '../components/ui/Buttons';
import { StatCard, WarningCard } from '../components/ui/Cards';
import { PageHeader } from '../components/ui/NavigationUI';

export function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <AppLayout breadcrumbs={[{ label: 'Diabetes Care' }, { label: 'Tổng quan' }]}>
      <PageHeader
        title={`Xin chào, ${user?.full_name || 'bạn'}`}
        subtitle="Nền tảng AI hỗ trợ tự quản lý đái tháo đường type 2"
        actions={
          <PrimaryButton icon={<Utensils size={16} />} onClick={() => navigate('/nutrition')}>
            Mở phân hệ Dinh dưỡng
          </PrimaryButton>
        }
      />

      <WarningCard level="info" title="Phạm vi hỗ trợ tự quản lý">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <ShieldCheck size={16} />
          <span>
            Ứng dụng hỗ trợ theo dõi dinh dưỡng, kiến thức y khoa và vận động — không thay thế
            chẩn đoán hay chỉ định điều trị của bác sĩ.
          </span>
        </div>
      </WarningCard>

      <section className="dc-grid-3">
        <StatCard
          label="Dinh dưỡng cá nhân hóa"
          value="9 màn hình"
          subtitle="Tổng quan, Hồ sơ, Tạo thực đơn AI, Nhật ký, Tiến triển, An toàn & Giải thích"
          icon={<Utensils size={18} />}
          tone="primary"
        />
        <StatCard
          label="Tư vấn tri thức AI"
          value="RAG + Safety"
          subtitle="Trích dẫn nguồn ADA, WHO, IDF, Bộ Y tế"
          icon={<Bot size={18} />}
          tone="secondary"
        />
        <StatCard
          label="Giám sát tập luyện"
          value="MediaPipe Pose"
          subtitle="Đánh giá tư thế an toàn (đang phát triển)"
          icon={<Dumbbell size={18} />}
        />
      </section>

      <section className="dc-grid-3">
        <div className="dc-card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <h3 style={{ fontSize: 17 }}>Dinh dưỡng & Thực đơn</h3>
          <p style={{ fontSize: 14, color: 'var(--dc-text-secondary)', flex: 1 }}>
            Thiết lập hồ sơ, tạo thực đơn theo Plate Method, theo dõi nhật ký ăn uống và kiểm tra an toàn.
          </p>
          <PrimaryButton icon={<ArrowRight size={15} />} onClick={() => navigate('/nutrition')}>
            Truy cập Dinh dưỡng
          </PrimaryButton>
        </div>

        <div className="dc-card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <h3 style={{ fontSize: 17 }}>Tư vấn tri thức AI</h3>
          <p style={{ fontSize: 14, color: 'var(--dc-text-secondary)', flex: 1 }}>
            Hỏi đáp thông tin y khoa đái tháo đường type 2 kèm nguồn tham khảo đáng tin cậy.
          </p>
          <SecondaryButton variant="blue" onClick={() => navigate('/ai-consultation')}>
            Mở Tư vấn AI
          </SecondaryButton>
        </div>

        <div className="dc-card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <h3 style={{ fontSize: 17 }}>Theo dõi sức khỏe</h3>
          <p style={{ fontSize: 14, color: 'var(--dc-text-secondary)', flex: 1 }}>
            Ghi nhận chỉ số đường huyết và theo dõi xu hướng cân nặng theo thời gian.
          </p>
          <SecondaryButton icon={<Activity size={15} />} onClick={() => navigate('/nutrition/progress')}>
            Xem tiến triển
          </SecondaryButton>
        </div>
      </section>
    </AppLayout>
  );
}
