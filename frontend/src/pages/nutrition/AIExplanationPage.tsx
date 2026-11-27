import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bot, ExternalLink, FileCheck2 } from 'lucide-react';
import { AppLayout } from '../../components/layout/AppLayout';
import { useAuth } from '../../context/AuthContext';
import { PrimaryButton, SecondaryButton } from '../../components/ui/Buttons';
import { StatCard, WarningCard } from '../../components/ui/Cards';
import { EmptyState } from '../../components/ui/Feedback';
import { PageHeader } from '../../components/ui/NavigationUI';
import { StatusBadge } from '../../components/ui/Badges';
import {
  estimateReferenceDailyKcal,
  healthProfileApi,
  localPrefsAdapter,
  mealPlanStorage,
  sumMealSodium,
  VERIFIED_RAG_REFERENCES,
} from '../../services/nutritionApi';
import type { DailyMealPlan, HealthProfile } from '../../types/nutrition';

function todayStr(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

export function AIExplanationPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const today = todayStr();

  const [profile, setProfile] = useState<HealthProfile | null>(null);
  const [plan, setPlan] = useState<DailyMealPlan | null>(null);

  useEffect(() => {
    if (!user) return;
    setPlan(mealPlanStorage.getByDate(user.id, today));
    healthProfileApi.getByUser(user.id).then(setProfile).catch(() => setProfile(null));
  }, [user, today]);

  if (!user) return null;
  const prefs = localPrefsAdapter.get(user.id);
  const targetKcal = estimateReferenceDailyKcal(profile, prefs.nutrition_goal);

  const mealValues = plan ? Object.values(plan.meals).filter(Boolean) : [];
  const totalKcal = Math.round(mealValues.reduce((s, m) => s + (m?.total_energy_kcal ?? 0), 0));
  const totalCarb = Number(mealValues.reduce((s, m) => s + (m?.total_carbohydrate_g ?? 0), 0).toFixed(1));
  const totalProtein = Number(mealValues.reduce((s, m) => s + (m?.total_protein_g ?? 0), 0).toFixed(1));
  const totalFat = Number(mealValues.reduce((s, m) => s + (m?.total_fat_g ?? 0), 0).toFixed(1));
  const totalFiber = Number(mealValues.reduce((s, m) => s + (m?.total_fiber_g ?? 0), 0).toFixed(1));
  const totalSodium = mealValues.reduce((s, m) => s + (m ? sumMealSodium(m.items) : 0), 0);

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

      {!plan || mealValues.length === 0 ? (
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
              <StatCard label="Ngày thực đơn" value={plan.date} subtitle={`Tạo lúc: ${new Date(plan.generated_at).toLocaleString('vi-VN')}`} />
              <StatCard label="Chế độ & Mục tiêu" value={plan.applied_preference || 'Cân bằng ĐTĐ'} subtitle={`Mục tiêu: ${prefs.nutrition_goal === 'weight_loss' ? 'Giảm cân' : 'Duy trì'}`} />
              <StatCard label="Tổng năng lượng từ Engine" value={`${totalKcal} kcal`} subtitle={`Mục tiêu tham khảo: ${targetKcal ?? 'Chưa đủ hồ sơ'} kcal`} />
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
                <strong>Phù hợp chế độ ăn:</strong> Áp dụng chế độ <strong>{plan.applied_preference || 'Cân bằng ĐTĐ'}</strong>; ưu tiên thực phẩm có chỉ số đường huyết (GI) thấp–trung bình và giàu chất xơ ({totalFiber}g).
              </li>
              <li>
                <strong>Loại bỏ thực phẩm gây dị ứng:</strong>{' '}
                {prefs.allergies.length > 0
                  ? `Đã loại bỏ 100% món chứa hoặc liên quan tới: ${prefs.allergies.join(', ')}.`
                  : 'Không có dị ứng thực phẩm nào được khai báo.'}
              </li>
              <li>
                <strong>Kiểm soát ràng buộc dinh dưỡng:</strong> Tổng Carb {totalCarb}g, Đạm {totalProtein}g, Béo {totalFat}g, Natri ước tính {totalSodium}mg.
              </li>
            </ul>
          </section>

          {/* C. Nutrition Reasoning (3 tách biệt rõ ràng) */}
          <section className="dc-card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <h2 style={{ fontSize: 17 }}>C. Phân tách trách nhiệm: Engine — RAG — LLM</h2>
            <WarningCard level="info" title="Trạng thái kết nối RAG Explanation trên nhánh main">
              Nhánh <code>main</code> hiện cung cấp API tạo thực đơn (<code>POST /api/v1/nutrition/recommend</code>). Phần diễn giải ngôn ngữ tự nhiên đang chạy qua Adapter chuẩn bị sẵn để ghép nối endpoint <code>/nutrition/explain</code> từ nhánh AI, đảm bảo giữ nguyên 100% số liệu của Engine.
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
