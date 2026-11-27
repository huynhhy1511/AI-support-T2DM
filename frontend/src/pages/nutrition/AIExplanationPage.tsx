import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bot, ExternalLink, FileCheck2 } from 'lucide-react';
import { AppLayout } from '../../components/layout/AppLayout';
import { useAuth } from '../../context/AuthContext';
import { PrimaryButton, SecondaryButton } from '../../components/ui/Buttons';
import { StatCard, WarningCard } from '../../components/ui/Cards';
import { EmptyState, LoadingSkeleton } from '../../components/ui/Feedback';
import { PageHeader } from '../../components/ui/NavigationUI';
import { StatusBadge } from '../../components/ui/Badges';
import {
  healthProfileApi,
  nutritionBackendApi,
  VERIFIED_RAG_REFERENCES,
} from '../../services/nutritionApi';
import type {
  DailyRecommendationsResponse,
  HealthProfile,
} from '../../types/nutrition';

function todayStr(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

export function AIExplanationPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const today = todayStr();

  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<HealthProfile | null>(null);
  const [dailyPlan, setDailyPlan] = useState<DailyRecommendationsResponse | null>(null);

  useEffect(() => {
    if (!user) return;
    let active = true;
    setLoading(true);
    Promise.all([
      healthProfileApi.getMe().catch(() => null),
      nutritionBackendApi.getToday(today).catch(() => null),
    ])
      .then(([hp, todayRecs]) => {
        if (!active) return;
        setProfile(hp);
        setDailyPlan(todayRecs);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [user, today]);

  if (!user) return null;

  const targetKcal =
    profile?.target_energy_kcal != null ? Math.round(profile.target_energy_kcal) : null;
  const mealValues = dailyPlan?.meals ?? [];
  const summary = dailyPlan?.daily_summary;
  const totalKcal = Math.round(summary?.total_energy_kcal ?? 0);
  const totalCarb = Number((summary?.total_carbohydrate_g ?? 0).toFixed(1));
  const totalProtein = Number((summary?.total_protein_g ?? 0).toFixed(1));
  const totalFat = Number((summary?.total_fat_g ?? 0).toFixed(1));
  const totalFiber = Number((summary?.total_fiber_g ?? 0).toFixed(1));
  const totalSodium = Math.round(summary?.total_sodium_mg ?? 0);
  const profileAllergies = profile?.allergies ?? [];
  const latestGeneratedAt = mealValues[0]?.generated_at;

  return (
    <AppLayout
      breadcrumbs={[
        { label: 'Diabetes Care', to: '/dashboard' },
        { label: 'Dinh dưỡng', to: '/nutrition' },
        { label: 'Giải thích đề xuất AI' },
      ]}
    >
      <PageHeader
        title="Giải thích đề xuất dinh dưỡng (RAG & Citations)"
        subtitle="Minh bạch hóa số liệu từ Nutrition Engine, tri thức RAG và tài liệu y khoa gốc"
        actions={
          <SecondaryButton onClick={() => navigate('/nutrition/daily')}>
            Quay lại thực đơn
          </SecondaryButton>
        }
      />

      {loading ? (
        <LoadingSkeleton rows={4} />
      ) : mealValues.length === 0 ? (
        <EmptyState
          icon={<Bot size={26} />}
          title="Chưa có thực đơn để giải thích"
          description="Hãy tạo thực đơn hằng ngày trước để hệ thống phân tích lý do lựa chọn món và nguồn tham khảo y khoa."
          actionLabel="Tạo thực đơn ngay"
          onAction={() => navigate('/nutrition/generate')}
        />
      ) : (
        <>
          {/* A. Recommendation Overview */}
          <section className="dc-card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
              <h2 style={{ fontSize: 17 }}>A. Tổng quan thực đơn đang giải thích</h2>
              <StatusBadge tone="info">Nguồn giải thích: Engine + RAG Adapter</StatusBadge>
            </div>
            <div className="dc-grid-3">
              <StatCard
                label="Ngày thực đơn"
                value={dailyPlan?.date || today}
                subtitle={
                  latestGeneratedAt
                    ? `Tạo lúc: ${new Date(latestGeneratedAt).toLocaleString('vi-VN')}`
                    : undefined
                }
              />
              <StatCard
                label="Chế độ & Mục tiêu"
                value={profile?.dietary_preference || 'Cân bằng ĐTĐ'}
                subtitle={`Mục tiêu: ${profile?.nutrition_goal === 'weight_loss' ? 'Giảm cân' : 'Duy trì'}`}
              />
              <StatCard
                label="Tổng năng lượng từ Engine"
                value={`${totalKcal} kcal`}
                subtitle={`Mục tiêu tham khảo: ${targetKcal ?? 'Chưa đủ hồ sơ'} kcal`}
              />
            </div>
          </section>

          {/* B. Why This Meal Plan */}
          <section className="dc-card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <h2 style={{ fontSize: 17 }}>B. Vì sao thực đơn này được lựa chọn?</h2>
            <ul style={{ margin: 0, paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 8, fontSize: 14.5 }}>
              <li>
                <strong>Mục tiêu năng lượng:</strong> Dựa trên cấu trúc Đĩa ăn Đái tháo đường (Plate Method) gồm {mealValues.length} bữa với tổng {totalKcal} kcal (không để AI tự ý thay đổi định lượng).
              </li>
              <li>
                <strong>Phù hợp chế độ ăn:</strong> Áp dụng chế độ <strong>{profile?.dietary_preference || 'Cân bằng ĐTĐ'}</strong>; ưu tiên thực phẩm có chỉ số đường huyết (GI) thấp–trung bình và giàu chất xơ ({totalFiber}g).
              </li>
              <li>
                <strong>Loại bỏ thực phẩm gây dị ứng:</strong>{' '}
                {profileAllergies.length > 0
                  ? `Đã loại bỏ 100% món chứa hoặc liên quan tới: ${profileAllergies.join(', ')}.`
                  : 'Không có dị ứng thực phẩm nào được khai báo.'}
              </li>
              <li>
                <strong>Kiểm soát ràng buộc dinh dưỡng:</strong> Tổng Carb {totalCarb}g, Đạm {totalProtein}g, Béo {totalFat}g, Natri {totalSodium}mg.
              </li>
            </ul>
          </section>

          {/* C. Nutrition Reasoning (3 tách biệt rõ ràng) */}
          <section className="dc-card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <h2 style={{ fontSize: 17 }}>C. Phân tách trách nhiệm: Engine — RAG — LLM</h2>
            <WarningCard level="info" title="Trạng thái kết nối RAG Explanation">
              Hệ thống hiện đọc số liệu thực đơn trực tiếp từ PostgreSQL (<code>GET /api/v1/nutrition/recommendations/today</code>). Phần diễn giải ngôn ngữ tự nhiên đang chạy qua danh mục nguồn trích dẫn xác minh sẵn để chuẩn bị ghép nối endpoint <code>/nutrition/explain</code> từ nhánh AI.
            </WarningCard>

            <div className="dc-grid-3">
              <div className="dc-card dc-card-compact" style={{ background: 'var(--dc-surface-subtle)' }}>
                <h3 style={{ fontSize: 15, marginBottom: 8 }}>1. Số liệu từ Nutrition Engine</h3>
                <p style={{ fontSize: 13.5, color: 'var(--dc-text-secondary)' }}>
                  {totalKcal} kcal · Carb {totalCarb}g · Đạm {totalProtein}g · Béo {totalFat}g · Xơ {totalFiber}g · Natri {totalSodium}mg.
                </p>
              </div>
              <div className="dc-card dc-card-compact" style={{ background: 'var(--dc-surface-subtle)' }}>
                <h3 style={{ fontSize: 15, marginBottom: 8 }}>2. Tri thức RAG truy xuất</h3>
                <p style={{ fontSize: 13.5, color: 'var(--dc-text-secondary)' }}>
                  Áp dụng các khuyến nghị [K001] Cá thể hóa, [K003] Chất xơ &ge;14g/1000kcal, [K014] Ưu tiên GI thấp, [K025] Giới hạn natri &lt;2000mg.
                </p>
              </div>
              <div className="dc-card dc-card-compact" style={{ background: 'var(--dc-surface-subtle)' }}>
                <h3 style={{ fontSize: 15, marginBottom: 8 }}>3. Diễn giải cho người bệnh</h3>
                <p style={{ fontSize: 13.5, color: 'var(--dc-text-secondary)' }}>
                  Thực đơn chia nhỏ bữa ăn giúp hạn chế tăng vọt đường huyết sau ăn; cần kết hợp đo đường huyết định kỳ và hỏi bác sĩ trước khi thay đổi phác đồ.
                </p>
              </div>
            </div>
          </section>

          {/* D. References */}
          <section className="dc-card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <FileCheck2 size={18} color="var(--dc-primary)" />
              <h2 style={{ fontSize: 17 }}>D. Nguồn tài liệu tham khảo y khoa</h2>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {VERIFIED_RAG_REFERENCES.map((ref) => (
                <div
                  key={ref.kb_id}
                  style={{
                    padding: 14,
                    borderRadius: 12,
                    border: '1px solid var(--dc-border)',
                    background: 'var(--dc-surface-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                    <strong style={{ fontSize: 14.5 }}>
                      [{ref.kb_id}] {ref.title}
                    </strong>
                    <StatusBadge tone="success">{ref.organization} ({ref.year})</StatusBadge>
                  </div>
                  <p style={{ fontSize: 13.5, color: 'var(--dc-text-secondary)', marginTop: 6 }}>
                    {ref.excerpt}
                  </p>
                  <a
                    href={ref.url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 13, marginTop: 6 }}
                  >
                    <span>Xem tài liệu gốc</span>
                    <ExternalLink size={13} />
                  </a>
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 8 }}>
              <PrimaryButton onClick={() => navigate('/nutrition/daily')}>
                Quay lại thực đơn hằng ngày
              </PrimaryButton>
            </div>
          </section>
        </>
      )}
    </AppLayout>
  );
}
