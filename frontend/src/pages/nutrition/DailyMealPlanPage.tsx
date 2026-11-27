import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Bot,
  CalendarDays,
  CheckCircle2,
  Eye,
  RefreshCw,
  Sparkles,
} from 'lucide-react';
import { AppLayout } from '../../components/layout/AppLayout';
import { useAuth } from '../../context/AuthContext';
import { PrimaryButton, SecondaryButton } from '../../components/ui/Buttons';
import {
  FoodCard,
  MealCard,
  StatCard,
  WarningCard,
} from '../../components/ui/Cards';
import { EmptyState, LoadingSkeleton } from '../../components/ui/Feedback';
import { DateSelector } from '../../components/ui/FormControls';
import { PageHeader } from '../../components/ui/NavigationUI';
import { StatusBadge } from '../../components/ui/Badges';
import {
  foodDiaryStorage,
  foodsApi,
  nutritionBackendApi,
  sumMealSodium,
} from '../../services/nutritionApi';
import type {
  DailyRecommendationsResponse,
  FoodAlternativeItem,
  MealDiaryEntry,
  MealRecommendationResponse,
  MealType,
  RecommendedFoodItem,
} from '../../types/nutrition';

const MEALS_ORDER: Array<{ key: MealType; title: string; time: string }> = [
  { key: 'breakfast', title: 'Bữa sáng', time: '06:30 – 08:00' },
  { key: 'lunch', title: 'Bữa trưa', time: '11:30 – 13:00' },
  { key: 'dinner', title: 'Bữa tối', time: '18:00 – 19:30' },
  { key: 'snack', title: 'Bữa phụ', time: '15:30 – 16:00' },
];

function todayStr(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

export function DailyMealPlanPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const initialDate = searchParams.get('date') || todayStr();
  const [selectedDate, setSelectedDate] = useState(initialDate);
  const [loading, setLoading] = useState(true);
  const [dailyData, setDailyData] = useState<DailyRecommendationsResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  // Swap food modal state
  const [swapTarget, setSwapTarget] = useState<{
    recommendationId: string;
    mealType: MealType;
    item: RecommendedFoodItem;
  } | null>(null);
  const [swapLoading, setSwapLoading] = useState(false);
  const [swapSubmitting, setSwapSubmitting] = useState(false);
  const [swapCandidates, setSwapCandidates] = useState<FoodAlternativeItem[]>([]);
  const [swapError, setSwapError] = useState<string | null>(null);

  const loadDailyPlan = useCallback(async (targetDate: string) => {
    setLoading(true);
    setLoadError(null);
    try {
      const res = await nutritionBackendApi.getToday(targetDate);
      setDailyData(res);
    } catch (err) {
      setLoadError(
        err instanceof Error ? err.message : 'Không thể tải thực đơn trong ngày từ máy chủ.'
      );
      setDailyData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!user) return;
    void loadDailyPlan(selectedDate);
  }, [user, selectedDate, loadDailyPlan]);

  if (!user) return null;

  const mealsByType: Partial<Record<MealType, MealRecommendationResponse>> = {};
  if (dailyData) {
    for (const m of dailyData.meals) {
      mealsByType[m.meal_type] = m;
    }
  }

  const mealList = dailyData?.meals ?? [];
  const summary = dailyData?.daily_summary;
  const totalKcal = Math.round(summary?.total_energy_kcal ?? 0);
  const totalCarb = Number((summary?.total_carbohydrate_g ?? 0).toFixed(1));
  const totalProtein = Number((summary?.total_protein_g ?? 0).toFixed(1));
  const totalFat = Number((summary?.total_fat_g ?? 0).toFixed(1));
  const totalFiber = Number((summary?.total_fiber_g ?? 0).toFixed(1));
  const totalSodium = Math.round(summary?.total_sodium_mg ?? 0);

  const openSwapModal = async (
    recommendationId: string,
    mealType: MealType,
    item: RecommendedFoodItem
  ) => {
    setSwapTarget({ recommendationId, mealType, item });
    setSwapLoading(true);
    setSwapError(null);
    setSwapCandidates([]);

    try {
      const alternatives = await foodsApi.getAlternatives(item.food_id, { limit: 8 });
      setSwapCandidates(alternatives);
      if (alternatives.length === 0) {
        setSwapError(
          'Không tìm thấy món tương đương cùng nhóm thỏa mãn ràng buộc dị ứng và chế độ ăn hiện tại.'
        );
      }
    } catch (err) {
      setSwapError(
        err instanceof Error
          ? err.message
          : 'Không thể tải danh sách món thay thế từ máy chủ.'
      );
    } finally {
      setSwapLoading(false);
    }
  };

  const applySwap = async (replacement: FoodAlternativeItem) => {
    if (!swapTarget) return;
    setSwapSubmitting(true);
    setSwapError(null);

    try {
      await nutritionBackendApi.substituteFood(swapTarget.recommendationId, {
        original_food_id: swapTarget.item.food_id,
        replacement_food_id: replacement.id,
      });
      await loadDailyPlan(selectedDate);
      setSwapTarget(null);
      setToast(`Đã thay thế sang "${replacement.name}" và cập nhật tổng dinh dưỡng trên máy chủ.`);
    } catch (err) {
      setSwapError(
        err instanceof Error
          ? err.message
          : 'Không thể áp dụng thay thế món. Thực đơn gốc được giữ nguyên.'
      );
    } finally {
      setSwapSubmitting(false);
    }
  };

  const handleLogMealAsEaten = (mealType: MealType) => {
    const meal = mealsByType[mealType];
    if (!meal) return;

    const existing =
      foodDiaryStorage.getByDate(user.id, selectedDate) ||
      ({} as Record<MealType, MealDiaryEntry>);
    existing[mealType] = {
      id: `${selectedDate}-${mealType}`,
      date: selectedDate,
      meal_type: mealType,
      status: 'eaten_full',
      portion_ratio: 1.0,
      logged_at: new Date().toISOString(),
      actual_energy_kcal: meal.total_energy_kcal,
      actual_carbohydrate_g: meal.total_carbohydrate_g,
      actual_protein_g: meal.total_protein_g,
      actual_fat_g: meal.total_fat_g,
      actual_fiber_g: meal.total_fiber_g,
      actual_sodium_mg: meal.total_sodium_mg ?? sumMealSodium(meal.items),
    };
    foodDiaryStorage.saveByDate(user.id, selectedDate, existing);
    setToast(`Đã ghi nhận bữa ${mealType} vào Nhật ký ăn uống (kế hoạch gốc vẫn được giữ nguyên).`);
  };

  return (
    <AppLayout
      breadcrumbs={[
        { label: 'Diabetes Care', to: '/dashboard' },
        { label: 'Dinh dưỡng', to: '/nutrition' },
        { label: 'Thực đơn hằng ngày' },
      ]}
    >
      <PageHeader
        title="Thực đơn hằng ngày"
        subtitle="Chi tiết các bữa ăn từ máy chủ theo Đĩa ăn Đái tháo đường (Plate Method)"
        actions={
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <DateSelector value={selectedDate} onChange={setSelectedDate} />
            <StatusBadge tone={mealList.length > 0 ? 'success' : 'neutral'}>
              {mealList.length > 0 ? `Đang áp dụng (${mealList.length} bữa)` : 'Chưa có thực đơn'}
            </StatusBadge>
          </div>
        }
      />

      {toast && (
        <WarningCard level="success" title="Cập nhật thành công">
          {toast}
        </WarningCard>
      )}

      {loadError && (
        <WarningCard level="error" title="Không tải được thực đơn">
          {loadError}
        </WarningCard>
      )}

      {loading ? (
        <LoadingSkeleton rows={4} />
      ) : mealList.length === 0 ? (
        <EmptyState
          icon={<CalendarDays size={26} />}
          title={`Chưa có thực đơn cho ngày ${selectedDate}`}
          description="Hãy tạo thực đơn cá nhân hóa bằng AI dựa trên hồ sơ sức khỏe và sở thích ăn uống của bạn."
          actionLabel="Tạo thực đơn ngay"
          onAction={() => navigate('/nutrition/generate')}
        />
      ) : (
        <>
          {/* B. Nutrition Summary */}
          <section className="dc-grid-3">
            <StatCard label="Tổng năng lượng (Calories)" value={totalKcal} unit="kcal" tone="primary" />
            <StatCard label="Carbohydrate / Chất xơ" value={`${totalCarb}g`} subtitle={`Chất xơ: ${totalFiber}g`} tone="secondary" />
            <StatCard label="Đạm / Béo / Natri" value={`${totalProtein}g / ${totalFat}g`} subtitle={`Natri: ${totalSodium} mg`} />
          </section>

          {/* C. 4 Meal Sections */}
          <section style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
            {MEALS_ORDER.map((mMeta) => {
              const meal = mealsByType[mMeta.key];
              if (!meal) return null;
              return (
                <MealCard
                  key={mMeta.key}
                  title={mMeta.title}
                  timeRange={mMeta.time}
                  totalKcal={meal.total_energy_kcal}
                  statusLabel={`${meal.items.length} món`}
                  statusTone="info"
                  categoryHint={mMeta.key === 'snack' ? 'fruits' : 'vegetables'}
                  footer={
                    <>
                      <span style={{ fontSize: 13, color: 'var(--dc-text-secondary)' }}>
                        Carb: <strong>{meal.total_carbohydrate_g}g</strong> · Đạm: <strong>{meal.total_protein_g}g</strong> · Béo: <strong>{meal.total_fat_g}g</strong> · Xơ: <strong>{meal.total_fiber_g}g</strong>
                      </span>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <PrimaryButton
                          size="sm"
                          icon={<CheckCircle2 size={15} />}
                          onClick={() => handleLogMealAsEaten(mMeta.key)}
                        >
                          Ghi nhận đã ăn
                        </PrimaryButton>
                      </div>
                    </>
                  }
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {meal.items.map((item) => (
                      <FoodCard
                        key={item.food_id}
                        item={item}
                        actions={
                          <>
                            <SecondaryButton
                              size="sm"
                              icon={<Eye size={14} />}
                              onClick={() => navigate(`/nutrition/food/${item.food_id}`)}
                            >
                              Xem món ăn
                            </SecondaryButton>
                            <SecondaryButton
                              size="sm"
                              variant="blue"
                              icon={<RefreshCw size={14} />}
                              onClick={() => openSwapModal(meal.recommendation_id, mMeta.key, item)}
                            >
                              Thay món tương đương
                            </SecondaryButton>
                          </>
                        }
                      />
                    ))}
                  </div>
                </MealCard>
              );
            })}
          </section>

          {/* E. Footer */}
          <section className="dc-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
            <div>
              <h3 style={{ fontSize: 16 }}>Tổng dinh dưỡng cả ngày: {totalKcal} kcal</h3>
              <p style={{ fontSize: 13.5, color: 'var(--dc-text-secondary)', marginTop: 4 }}>
                {mealList[0]?.clinical_safety_disclaimer}
              </p>
            </div>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              <SecondaryButton icon={<Sparkles size={15} />} onClick={() => navigate('/nutrition/diary')}>
                Ghi nhận kế hoạch vào nhật ký
              </SecondaryButton>
              <PrimaryButton icon={<Bot size={15} />} onClick={() => navigate('/nutrition/explanation')}>
                Xem lý do AI đề xuất
              </PrimaryButton>
            </div>
          </section>
        </>
      )}

      {/* Modal thay món tương đương */}
      {swapTarget && (
        <div className="dc-modal-backdrop" role="dialog" aria-modal="true">
          <div className="dc-modal" style={{ maxWidth: 640 }}>
            <h3 style={{ fontSize: 18, marginBottom: 6 }}>
              Thay món tương đương cho "{swapTarget.item.food_name}"
            </h3>
            <p style={{ fontSize: 13.5, color: 'var(--dc-text-secondary)', marginBottom: 16 }}>
              Nhóm thực phẩm: <strong>{swapTarget.item.category}</strong> · Đã lọc dị ứng và chế độ ăn qua Backend Constraint Engine
            </p>

            {swapLoading && (
              <WarningCard level="info" title="Đang kiểm tra ràng buộc">
                Hệ thống đang truy vấn món thay thế an toàn từ máy chủ...
              </WarningCard>
            )}

            {swapError && (
              <WarningCard level="warning" title="Lưu ý thay thế món">
                {swapError}
              </WarningCard>
            )}

            {!swapLoading && swapCandidates.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxHeight: 360, overflowY: 'auto' }}>
                {swapCandidates.map((cand) => (
                  <div
                    key={cand.id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: 12,
                      borderRadius: 10,
                      border: '1px solid var(--dc-border)',
                      gap: 10,
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 14.5 }}>{cand.name}</div>
                      <div style={{ fontSize: 12.5, color: 'var(--dc-text-secondary)' }}>
                        {cand.serving_size_g}g · {cand.energy_kcal} kcal · Carb {cand.carbohydrate_g}g · GI: {cand.glycemic_index ?? 'Chưa có'}
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--dc-primary)', marginTop: 3 }}>
                        {cand.similarity_reason}
                      </div>
                      {cand.allergens && cand.allergens.length > 0 && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 4 }}>
                          {cand.allergens.map((al) => (
                            <StatusBadge key={al.id} tone="warning">
                              {al.name_vi}
                            </StatusBadge>
                          ))}
                        </div>
                      )}
                    </div>
                    <PrimaryButton
                      size="sm"
                      loading={swapSubmitting}
                      onClick={() => applySwap(cand)}
                    >
                      Chọn món này
                    </PrimaryButton>
                  </div>
                ))}
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
              <SecondaryButton onClick={() => setSwapTarget(null)} disabled={swapSubmitting}>
                Đóng
              </SecondaryButton>
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
