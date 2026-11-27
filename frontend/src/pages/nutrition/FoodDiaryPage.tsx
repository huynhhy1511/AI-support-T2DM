import { useEffect, useState, type ChangeEvent } from 'react';
import { Camera, Check, MinusCircle, Utensils } from 'lucide-react';
import { AppLayout } from '../../components/layout/AppLayout';
import { useAuth } from '../../context/AuthContext';
import { PrimaryButton, SecondaryButton } from '../../components/ui/Buttons';
import { MealCard, StatCard, WarningCard } from '../../components/ui/Cards';
import { DateSelector } from '../../components/ui/FormControls';
import { PageHeader } from '../../components/ui/NavigationUI';
import {
  foodDiaryStorage,
  mealPlanStorage,
  sumMealSodium,
} from '../../services/nutritionApi';
import type {
  DailyMealPlan,
  DiaryLogStatus,
  MealDiaryEntry,
  MealType,
} from '../../types/nutrition';

const MEALS: Array<{ key: MealType; title: string; time: string }> = [
  { key: 'breakfast', title: 'Bữa sáng', time: '06:30 – 08:00' },
  { key: 'lunch', title: 'Bữa trưa', time: '11:30 – 13:00' },
  { key: 'dinner', title: 'Bữa tối', time: '18:00 – 19:30' },
  { key: 'snack', title: 'Bữa phụ', time: '15:30 – 16:00' },
];

function todayStr(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

export function FoodDiaryPage() {
  const { user } = useAuth();
  const [date, setDate] = useState(todayStr());
  const [plan, setPlan] = useState<DailyMealPlan | null>(null);
  const [diary, setDiary] = useState<Record<MealType, MealDiaryEntry>>({} as Record<MealType, MealDiaryEntry>);
  const [noteInputs, setNoteInputs] = useState<Record<string, string>>({});
  const [customFoodInputs, setCustomFoodInputs] = useState<Record<string, string>>({});
  const [savedNotice, setSavedNotice] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    setPlan(mealPlanStorage.getByDate(user.id, date));
    setDiary(foodDiaryStorage.getByDate(user.id, date) || ({} as Record<MealType, MealDiaryEntry>));
  }, [user, date]);

  if (!user) return null;

  const logAction = (
    mealType: MealType,
    status: DiaryLogStatus,
    portionRatio: number,
    customName?: string,
    photoUrl?: string
  ) => {
    const plannedMeal = plan?.meals[mealType];
    const baseKcal = plannedMeal?.total_energy_kcal ?? 0;
    const baseCarb = plannedMeal?.total_carbohydrate_g ?? 0;
    const baseProtein = plannedMeal?.total_protein_g ?? 0;
    const baseFat = plannedMeal?.total_fat_g ?? 0;
    const baseFiber = plannedMeal?.total_fiber_g ?? 0;
    const baseSodium = plannedMeal ? sumMealSodium(plannedMeal.items) : 0;

    const prev = diary[mealType];
    const entry: MealDiaryEntry = {
      id: `${date}-${mealType}`,
      date,
      meal_type: mealType,
      status,
      portion_ratio: portionRatio,
      logged_at: new Date().toISOString(),
      note: noteInputs[mealType] ?? prev?.note ?? '',
      custom_food_name: customName ?? prev?.custom_food_name,
      photo_preview_url: photoUrl ?? prev?.photo_preview_url,
      actual_energy_kcal: Number((baseKcal * portionRatio).toFixed(1)),
      actual_carbohydrate_g: Number((baseCarb * portionRatio).toFixed(1)),
      actual_protein_g: Number((baseProtein * portionRatio).toFixed(1)),
      actual_fat_g: Number((baseFat * portionRatio).toFixed(1)),
      actual_fiber_g: Number((baseFiber * portionRatio).toFixed(1)),
      actual_sodium_mg: Math.round(baseSodium * portionRatio),
    };

    const nextDiary = { ...diary, [mealType]: entry };
    setDiary(nextDiary);
    foodDiaryStorage.saveByDate(user.id, date, nextDiary);
    setSavedNotice(`Đã lưu nhật ký ${mealType} (dữ liệu thực tế tách biệt hoàn toàn với kế hoạch gốc).`);
  };

  const handlePhotoUpload = (mealType: MealType, e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const existing = diary[mealType];
      logAction(
        mealType,
        existing?.status || 'eaten_full',
        existing?.portion_ratio ?? 1.0,
        existing?.custom_food_name,
        String(reader.result)
      );
    };
    reader.readAsDataURL(file);
  };

  const plannedMeals = plan ? Object.values(plan.meals).filter(Boolean) : [];
  const plannedTotals = {
    kcal: Math.round(plannedMeals.reduce((s, m) => s + (m?.total_energy_kcal ?? 0), 0)),
    carb: Number(plannedMeals.reduce((s, m) => s + (m?.total_carbohydrate_g ?? 0), 0).toFixed(1)),
    protein: Number(plannedMeals.reduce((s, m) => s + (m?.total_protein_g ?? 0), 0).toFixed(1)),
    fat: Number(plannedMeals.reduce((s, m) => s + (m?.total_fat_g ?? 0), 0).toFixed(1)),
    sodium: plannedMeals.reduce((s, m) => s + (m ? sumMealSodium(m.items) : 0), 0),
  };

  const loggedList = Object.values(diary);
  const actualTotals = {
    kcal: Math.round(loggedList.reduce((s, d) => s + d.actual_energy_kcal, 0)),
    carb: Number(loggedList.reduce((s, d) => s + d.actual_carbohydrate_g, 0).toFixed(1)),
    protein: Number(loggedList.reduce((s, d) => s + d.actual_protein_g, 0).toFixed(1)),
    fat: Number(loggedList.reduce((s, d) => s + d.actual_fat_g, 0).toFixed(1)),
    sodium: loggedList.reduce((s, d) => s + d.actual_sodium_mg, 0),
  };

  return (
    <AppLayout
      breadcrumbs={[
        { label: 'Diabetes Care', to: '/dashboard' },
        { label: 'Dinh dưỡng', to: '/nutrition' },
        { label: 'Nhật ký ăn uống' },
      ]}
    >
      <PageHeader
        title="Nhật ký ăn uống"
        subtitle="Ghi nhận bữa ăn thực tế và so sánh với kế hoạch mà không ghi đè thực đơn gốc"
        actions={<DateSelector value={date} onChange={setDate} />}
      />

      {savedNotice && (
        <WarningCard level="success" title="Đã cập nhật nhật ký">
          {savedNotice}
        </WarningCard>
      )}

      {/* E. Nutrition Comparison: Planned vs Actual */}
      <section className="dc-card">
        <h2 style={{ fontSize: 17, marginBottom: 14 }}>
          So sánh Kế hoạch (Planned) vs Thực tế (Actual) — Ngày {date}
        </h2>
        <div className="dc-table-wrap">
          <table className="dc-table">
            <thead>
              <tr>
                <th>Chỉ tiêu dinh dưỡng</th>
                <th>Kế hoạch ban đầu (Planned)</th>
                <th>Thực tế đã ghi nhận (Actual)</th>
                <th>Chênh lệch</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Năng lượng (Calories)</td>
                <td>{plannedTotals.kcal} kcal</td>
                <td><strong>{actualTotals.kcal} kcal</strong></td>
                <td>{actualTotals.kcal - plannedTotals.kcal} kcal</td>
              </tr>
              <tr>
                <td>Carbohydrate</td>
                <td>{plannedTotals.carb} g</td>
                <td><strong>{actualTotals.carb} g</strong></td>
                <td>{Number((actualTotals.carb - plannedTotals.carb).toFixed(1))} g</td>
              </tr>
              <tr>
                <td>Protein (Đạm)</td>
                <td>{plannedTotals.protein} g</td>
                <td><strong>{actualTotals.protein} g</strong></td>
                <td>{Number((actualTotals.protein - plannedTotals.protein).toFixed(1))} g</td>
              </tr>
              <tr>
                <td>Fat (Chất béo)</td>
                <td>{plannedTotals.fat} g</td>
                <td><strong>{actualTotals.fat} g</strong></td>
                <td>{Number((actualTotals.fat - plannedTotals.fat).toFixed(1))} g</td>
              </tr>
              <tr>
                <td>Sodium (Natri)</td>
                <td>{plannedTotals.sodium} mg</td>
                <td><strong>{actualTotals.sodium} mg</strong></td>
                <td>{actualTotals.sodium - plannedTotals.sodium} mg</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* B & C & D. Meal Timeline */}
      <section style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {MEALS.map((m) => {
          const plannedMeal = plan?.meals[m.key];
          const log = diary[m.key];
          const statusLabel = !log
            ? 'Chưa ghi nhận'
            : log.status === 'eaten_full'
              ? 'Đã ăn hết (100%)'
              : log.status === 'eaten_partial'
                ? `Ăn một phần (${Math.round(log.portion_ratio * 100)}%)`
                : log.status === 'eaten_other'
                  ? 'Ăn món khác'
                  : 'Đã bỏ bữa';

          const tone = !log
            ? 'neutral'
            : log.status === 'eaten_full'
              ? 'success'
              : log.status === 'skipped'
                ? 'warning'
                : 'info';

          return (
            <MealCard
              key={m.key}
              title={m.title}
              timeRange={m.time}
              totalKcal={log ? log.actual_energy_kcal : plannedMeal?.total_energy_kcal ?? 0}
              statusLabel={statusLabel}
              statusTone={tone}
              categoryHint={m.key === 'snack' ? 'fruits' : 'vegetables'}
            >
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div style={{ fontSize: 13.5, color: 'var(--dc-text-secondary)' }}>
                  <strong>Món theo kế hoạch:</strong>{' '}
                  {plannedMeal
                    ? plannedMeal.items.map((it) => it.food_name).join(', ')
                    : 'Chưa có thực đơn kế hoạch cho bữa này'}
                </div>

                {log?.custom_food_name && (
                  <div style={{ fontSize: 13.5 }}>
                    <strong>Món thực tế đã ăn:</strong> {log.custom_food_name}
                  </div>
                )}

                {log?.photo_preview_url && (
                  <img
                    src={log.photo_preview_url}
                    alt={`Ảnh ${m.title}`}
                    style={{ width: 160, height: 110, objectFit: 'cover', borderRadius: 10, border: '1px solid var(--dc-border)' }}
                  />
                )}

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  <PrimaryButton
                    size="sm"
                    icon={<Check size={14} />}
                    onClick={() => logAction(m.key, 'eaten_full', 1.0)}
                  >
                    Ăn hết khẩu phần
                  </PrimaryButton>
                  <SecondaryButton
                    size="sm"
                    variant="blue"
                    onClick={() => logAction(m.key, 'eaten_partial', 0.5)}
                  >
                    Ăn một phần (50%)
                  </SecondaryButton>
                  <SecondaryButton
                    size="sm"
                    icon={<MinusCircle size={14} />}
                    onClick={() => logAction(m.key, 'skipped', 0)}
                  >
                    Bỏ bữa
                  </SecondaryButton>
                  <label className="dc-btn dc-btn-secondary dc-btn-sm" style={{ cursor: 'pointer' }}>
                    <Camera size={14} />
                    <span>Tải ảnh bữa ăn</span>
                    <input
                      type="file"
                      accept="image/*"
                      style={{ display: 'none' }}
                      onChange={(e) => handlePhotoUpload(m.key, e)}
                    />
                  </label>
                </div>

                <div className="dc-grid-2">
                  <div style={{ display: 'flex', gap: 8 }}>
                    <input
                      className="dc-input"
                      style={{ minHeight: 38, fontSize: 13.5 }}
                      placeholder="Nhập tên món khác nếu ăn ngoài kế hoạch..."
                      value={customFoodInputs[m.key] ?? ''}
                      onChange={(e) =>
                        setCustomFoodInputs((p) => ({ ...p, [m.key]: e.target.value }))
                      }
                    />
                    <SecondaryButton
                      size="sm"
                      icon={<Utensils size={14} />}
                      onClick={() =>
                        logAction(m.key, 'eaten_other', 1.0, customFoodInputs[m.key] || 'Món ngoài kế hoạch')
                      }
                    >
                      Ăn món khác
                    </SecondaryButton>
                  </div>

                  <div style={{ display: 'flex', gap: 8 }}>
                    <input
                      className="dc-input"
                      style={{ minHeight: 38, fontSize: 13.5 }}
                      placeholder="Thêm ghi chú (cảm giác no, đường huyết sau ăn)..."
                      value={noteInputs[m.key] ?? log?.note ?? ''}
                      onChange={(e) => setNoteInputs((p) => ({ ...p, [m.key]: e.target.value }))}
                    />
                    <SecondaryButton
                      size="sm"
                      onClick={() =>
                        logAction(
                          m.key,
                          log?.status || 'eaten_full',
                          log?.portion_ratio ?? 1.0,
                          log?.custom_food_name
                        )
                      }
                    >
                      Lưu ghi chú
                    </SecondaryButton>
                  </div>
                </div>
              </div>
            </MealCard>
          );
        })}
      </section>

      <StatCard
        label="Lưu ý dữ liệu nhật ký"
        value="Độc lập với Kế hoạch"
        subtitle="Mọi ghi nhận trong Nhật ký ăn uống được lưu riêng, không ghi đè thực đơn gốc do Recommendation Engine tạo."
      />
    </AppLayout>
  );
}
