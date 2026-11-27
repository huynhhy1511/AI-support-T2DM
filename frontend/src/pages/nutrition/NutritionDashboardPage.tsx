import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  BookOpen,
  CalendarDays,
  Flame,
  Sparkles,
  UserCheck,
  Utensils,
} from 'lucide-react';
import { AppLayout } from '../../components/layout/AppLayout';
import { useAuth } from '../../context/AuthContext';
import { PrimaryButton, SecondaryButton } from '../../components/ui/Buttons';
import {
  MealCard,
  NutritionProgressCard,
  StatCard,
  WarningCard,
} from '../../components/ui/Cards';
import { PageHeader } from '../../components/ui/NavigationUI';
import { LoadingSkeleton } from '../../components/ui/Feedback';
import {
  estimateReferenceDailyKcal,
  foodDiaryStorage,
  healthProfileApi,
  localPrefsAdapter,
  mealPlanStorage,
  sumMealSodium,
} from '../../services/nutritionApi';
import type { DailyMealPlan, HealthProfile, MealDiaryEntry, MealType } from '../../types/nutrition';

const MEAL_META: Array<{ key: MealType; title: string; time: string; cat: string }> = [
  { key: 'breakfast', title: 'Bữa sáng', time: '06:30 – 08:00', cat: 'staple' },
  { key: 'lunch', title: 'Bữa trưa', time: '11:30 – 13:00', cat: 'protein' },
  { key: 'dinner', title: 'Bữa tối', time: '18:00 – 19:30', cat: 'vegetables' },
  { key: 'snack', title: 'Bữa phụ', time: '15:30 – 16:00', cat: 'fruits' },
];

function todayStr(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

export function NutritionDashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const today = todayStr();

  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<HealthProfile | null>(null);
  const [plan, setPlan] = useState<DailyMealPlan | null>(null);
  const [diary, setDiary] = useState<Record<MealType, MealDiaryEntry> | null>(null);

  useEffect(() => {
    if (!user) return;
    let active = true;
    (async () => {
      setLoading(true);
      try {
        const hp = await healthProfileApi.getByUser(user.id).catch(() => null);
        if (active) setProfile(hp);
      } finally {
        if (active) {
          setPlan(mealPlanStorage.getByDate(user.id, today));
          setDiary(foodDiaryStorage.getByDate(user.id, today));
          setLoading(false);
        }
      }
    })();
    return () => {
      active = false;
    };
  }, [user, today]);

  if (!user) return null;
  const prefs = localPrefsAdapter.get(user.id);
  const targetKcal = estimateReferenceDailyKcal(profile, prefs.nutrition_goal);

  const mealValues = plan ? Object.values(plan.meals).filter(Boolean) : [];
  const plannedKcal = plan && mealValues.length > 0
    ? Math.round(mealValues.reduce((s, m) => s + (m?.total_energy_kcal ?? 0), 0))
    : null;
  const plannedCarb = plan && mealValues.length > 0
    ? Number(mealValues.reduce((s, m) => s + (m?.total_carbohydrate_g ?? 0), 0).toFixed(1))
    : null;
  const plannedProtein = plan && mealValues.length > 0
    ? Number(mealValues.reduce((s, m) => s + (m?.total_protein_g ?? 0), 0).toFixed(1))
    : null;
  const plannedFat = plan && mealValues.length > 0
    ? Number(mealValues.reduce((s, m) => s + (m?.total_fat_g ?? 0), 0).toFixed(1))
    : null;
  const plannedFiber = plan && mealValues.length > 0
    ? Number(mealValues.reduce((s, m) => s + (m?.total_fiber_g ?? 0), 0).toFixed(1))
    : null;
  const plannedSodium = plan && mealValues.length > 0
    ? mealValues.reduce((s, m) => s + (m ? sumMealSodium(m.items) : 0), 0)
    : null;

  const diaryEntries = diary ? Object.values(diary) : [];
  const hasActual = diaryEntries.some((d) => d.status !== 'planned');
  const actualKcal = hasActual
    ? Math.round(diaryEntries.reduce((s, d) => s + d.actual_energy_kcal, 0))
    : null;

  return (
    <AppLayout
      breadcrumbs={[
        { label: 'Diabetes Care', to: '/dashboard' },
        { label: 'Dinh dưỡng' },
      ]}
    >
      <PageHeader
        title="Tổng quan dinh dưỡng"
        subtitle={`Hôm nay: ${today} · Quản lý thực đơn và nhật ký ăn uống hằng ngày`}
        actions={
          <PrimaryButton
            icon={<Sparkles size={16} />}
            onClick={() => navigate('/nutrition/generate')}
          >
            Tạo thực đơn
          </PrimaryButton>
        }
      />

      {loading ? (
        <LoadingSkeleton rows={4} />
      ) : (
        <>
          {!profile && (
            <WarningCard
              level="warning"
              title="Hồ sơ dinh dưỡng chưa đầy đủ"
              action={
                <SecondaryButton size="sm" onClick={() => navigate('/nutrition/profile')}>
                  Cập nhật hồ sơ ngay
                </SecondaryButton>
              }
            >
              Bạn chưa khai báo chiều cao, cân nặng và mức vận động. Hệ thống chưa thể ước tính
              nhu cầu năng lượng mục tiêu cá nhân hóa.
            </WarningCard>
          )}

          {/* B. Daily Nutrition Overview */}
          <section className="dc-grid-3">
            <StatCard
              label="Mục tiêu năng lượng (Target)"
              value={targetKcal !== null ? targetKcal : 'Chưa đủ dữ liệu'}
              unit={targetKcal !== null ? 'kcal/ngày' : undefined}
              subtitle={
                prefs.nutrition_goal === 'weight_loss'
                  ? 'Ước tính giảm cân an toàn (Mifflin-St Jeor)'
                  : 'Ước tính duy trì cân nặng'
              }
              icon={<Flame size={18} />}
              tone="secondary"
            />
            <StatCard
              label="Kế hoạch thực đơn (Planned)"
              value={plannedKcal !== null ? plannedKcal : 'Chưa tạo'}
              unit={plannedKcal !== null ? 'kcal' : undefined}
              subtitle={plan ? `Thực đơn ngày ${plan.date}` : 'Chưa có thực đơn cho hôm nay'}
              icon={<CalendarDays size={18} />}
              tone="primary"
            />
            <StatCard
              label="Thực tế đã ăn (Actual)"
              value={actualKcal !== null ? actualKcal : 'Chưa ghi nhận'}
              unit={actualKcal !== null ? 'kcal' : undefined}
              subtitle="Tổng hợp từ Nhật ký ăn uống hôm nay"
              icon={<Activity size={18} />}
              tone="warning"
            />
          </section>

          <NutritionProgressCard
            title="Tiến độ năng lượng trong ngày (Phân biệt Mục tiêu / Kế hoạch / Thực tế)"
            target={targetKcal}
            planned={plannedKcal}
            actual={actualKcal}
          />

          {/* C. Macronutrients */}
          <section>
            <h2 style={{ fontSize: 17, marginBottom: 12 }}>Thành phần dinh dưỡng kế hoạch hôm nay</h2>
            <div className="dc-grid-5">
              <StatCard label="Carbohydrate" value={plannedCarb ?? '—'} unit={plannedCarb !== null ? 'g' : ''} />
              <StatCard label="Protein (Đạm)" value={plannedProtein ?? '—'} unit={plannedProtein !== null ? 'g' : ''} />
              <StatCard label="Fat (Chất béo)" value={plannedFat ?? '—'} unit={plannedFat !== null ? 'g' : ''} />
              <StatCard label="Fiber (Chất xơ)" value={plannedFiber ?? '—'} unit={plannedFiber !== null ? 'g' : ''} />
              <StatCard
                label="Sodium (Natri)"
                value={plannedSodium !== null ? plannedSodium : '—'}
                unit={plannedSodium !== null ? 'mg' : ''}
                tone={plannedSodium && plannedSodium > 2000 ? 'warning' : 'primary'}
              />
            </div>
          </section>

          {/* D. Today's Meals */}
          <section>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h2 style={{ fontSize: 17 }}>Các bữa ăn hôm nay</h2>
              <SecondaryButton size="sm" onClick={() => navigate('/nutrition/daily')}>
                Xem chi tiết thực đơn
              </SecondaryButton>
            </div>
            <div className="dc-grid-2">
              {MEAL_META.map((m) => {
                const mealPlan = plan?.meals[m.key];
                const logEntry = diary?.[m.key];
                const statusLabel = logEntry
                  ? logEntry.status === 'eaten_full'
                    ? 'Đã ăn hết'
                    : logEntry.status === 'eaten_partial'
                      ? 'Ăn một phần'
                      : logEntry.status === 'skipped'
                        ? 'Đã bỏ bữa'
                        : logEntry.status === 'eaten_other'
                          ? 'Ăn món khác'
                          : 'Theo kế hoạch'
                  : mealPlan
                    ? 'Chưa ghi nhận'
                    : 'Chưa có thực đơn';

                const tone =
                  logEntry?.status === 'eaten_full'
                    ? 'success'
                    : logEntry?.status === 'skipped'
                      ? 'warning'
                      : mealPlan
                        ? 'info'
                        : 'neutral';

                return (
                  <MealCard
                    key={m.key}
                    title={m.title}
                    timeRange={m.time}
                    totalKcal={mealPlan?.total_energy_kcal ?? 0}
                    statusLabel={statusLabel}
                    statusTone={tone}
                    categoryHint={m.cat}
                    footer={
                      <>
                        <span style={{ fontSize: 13, color: 'var(--dc-text-secondary)' }}>
                          {mealPlan
                            ? `${mealPlan.items.length} món · Carb ${mealPlan.total_carbohydrate_g}g`
                            : 'Chưa tạo món cho bữa này'}
                        </span>
                        <SecondaryButton
                          size="sm"
                          onClick={() => navigate(mealPlan ? '/nutrition/daily' : '/nutrition/generate')}
                        >
                          {mealPlan ? 'Mở bữa ăn' : 'Tạo ngay'}
                        </SecondaryButton>
                      </>
                    }
                  />
                );
              })}
            </div>
          </section>

          {/* E. Quick Actions */}
          <section className="dc-card">
            <h2 style={{ fontSize: 17, marginBottom: 12 }}>Thao tác nhanh</h2>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
              <PrimaryButton icon={<Utensils size={16} />} onClick={() => navigate('/nutrition/daily')}>
                Xem thực đơn
              </PrimaryButton>
              <SecondaryButton variant="blue" icon={<Sparkles size={16} />} onClick={() => navigate('/nutrition/generate')}>
                Tạo thực đơn mới
              </SecondaryButton>
              <SecondaryButton icon={<BookOpen size={16} />} onClick={() => navigate('/nutrition/diary')}>
                Mở nhật ký ăn uống
              </SecondaryButton>
              <SecondaryButton icon={<UserCheck size={16} />} onClick={() => navigate('/nutrition/profile')}>
                Cập nhật hồ sơ
              </SecondaryButton>
            </div>
          </section>
        </>
      )}
    </AppLayout>
  );
}
