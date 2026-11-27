import { useCallback, useEffect, useState } from 'react';
import { Check, MinusCircle, Trash2, Utensils } from 'lucide-react';
import { AppLayout } from '../../components/layout/AppLayout';
import { useAuth } from '../../context/AuthContext';
import { PrimaryButton, SecondaryButton } from '../../components/ui/Buttons';
import { MealCard, StatCard, WarningCard } from '../../components/ui/Cards';
import { LoadingSkeleton } from '../../components/ui/Feedback';
import { DateSelector } from '../../components/ui/FormControls';
import { PageHeader } from '../../components/ui/NavigationUI';
import {
  mealDiaryApi,
  nutritionBackendApi,
} from '../../services/nutritionApi';
import type {
  DailyRecommendationsResponse,
  MealLog,
  MealLogItemCreate,
  MealLogStatusType,
  MealRecommendationResponse,
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
  const [loading, setLoading] = useState(true);
  const [savingMeal, setSavingMeal] = useState<MealType | null>(null);
  const [dailyPlan, setDailyPlan] = useState<DailyRecommendationsResponse | null>(null);
  const [logs, setLogs] = useState<MealLog[]>([]);
  const [noteInputs, setNoteInputs] = useState<Record<string, string>>({});
  const [customFoodInputs, setCustomFoodInputs] = useState<Record<string, string>>({});
  const [savedNotice, setSavedNotice] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadData = useCallback(async (targetDate: string) => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const [planRes, logsRes] = await Promise.all([
        nutritionBackendApi.getToday(targetDate).catch(() => null),
        mealDiaryApi.listLogs({
          date_from: targetDate,
          date_to: targetDate,
          page: 1,
          page_size: 50,
        }),
      ]);
      setDailyPlan(planRes);
      setLogs(logsRes.items);
    } catch (err) {
      setErrorMsg(
        err instanceof Error ? err.message : 'Không thể tải dữ liệu nhật ký từ máy chủ.'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!user) return;
    void loadData(date);
  }, [user, date, loadData]);

  if (!user) return null;

  const plannedByType: Partial<Record<MealType, MealRecommendationResponse>> = {};
  if (dailyPlan) {
    for (const m of dailyPlan.meals) {
      plannedByType[m.meal_type] = m;
    }
  }

  const logByType: Partial<Record<MealType, MealLog>> = {};
  for (const l of logs) {
    if (!logByType[l.meal_type]) {
      logByType[l.meal_type] = l;
    }
  }

  const handleLogAction = async (
    mealType: MealType,
    status: MealLogStatusType,
    portionRatio: number,
    customName?: string
  ) => {
    setSavingMeal(mealType);
    setSavedNotice(null);
    setErrorMsg(null);

    const plannedMeal = plannedByType[mealType];
    const existingLog = logByType[mealType];
    const noteText = noteInputs[mealType] ?? existingLog?.notes ?? '';

    let items: MealLogItemCreate[] = [];
    if (status === 'skipped') {
      items = [];
    } else if (status === 'eaten_other') {
      const name = (customName ?? customFoodInputs[mealType] ?? '').trim() || 'Món ngoài kế hoạch';
      items = [
        {
          custom_food_name: name,
          serving_g: 200,
        },
      ];
    } else if (plannedMeal && plannedMeal.items.length > 0) {
      items = plannedMeal.items.map((it) => ({
        food_id: it.food_id,
        serving_g: Math.max(
          1,
          Number((it.serving_size_g * it.serving_multiplier * portionRatio).toFixed(1))
        ),
      }));
    } else if (existingLog && existingLog.items.length > 0) {
      items = existingLog.items.map((it) => ({
        food_id: it.food_id,
        custom_food_name: it.custom_food_name,
        serving_g: it.serving_g,
      }));
    }

    try {
      if (existingLog) {
        await mealDiaryApi.updateLog(existingLog.id, {
          status,
          notes: noteText || null,
          items,
        });
      } else {
        await mealDiaryApi.createLog({
          recommendation_id: plannedMeal?.recommendation_id ?? null,
          meal_date: date,
          meal_type: mealType,
          status,
          notes: noteText || null,
          items,
        });
      }
      await loadData(date);
      setSavedNotice(
        `Đã lưu nhật ký bữa ${mealType} lên PostgreSQL (kế hoạch thực đơn gốc không bị thay đổi).`
      );
    } catch (err) {
      setErrorMsg(
        err instanceof Error ? err.message : 'Không thể lưu nhật ký ăn uống. Vui lòng thử lại.'
      );
    } finally {
      setSavingMeal(null);
    }
  };

  const handleSaveNoteOnly = async (mealType: MealType) => {
    const existingLog = logByType[mealType];
    if (!existingLog) {
      await handleLogAction(mealType, 'eaten', 1.0);
      return;
    }
    setSavingMeal(mealType);
    setSavedNotice(null);
    setErrorMsg(null);
    try {
      await mealDiaryApi.updateLog(existingLog.id, {
        notes: noteInputs[mealType] ?? existingLog.notes ?? '',
      });
      await loadData(date);
      setSavedNotice(`Đã cập nhật ghi chú cho bữa ${mealType}.`);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Không thể lưu ghi chú.');
    } finally {
      setSavingMeal(null);
    }
  };

  const handleDeleteLog = async (mealType: MealType, logId: string) => {
    setSavingMeal(mealType);
    setSavedNotice(null);
    setErrorMsg(null);
    try {
      await mealDiaryApi.deleteLog(logId);
      await loadData(date);
      setSavedNotice(`Đã xóa nhật ký bữa ${mealType}.`);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Không thể xóa nhật ký.');
    } finally {
      setSavingMeal(null);
    }
  };

  const summary = dailyPlan?.daily_summary;
  const plannedTotals = {
    kcal: Math.round(summary?.total_energy_kcal ?? 0),
    carb: Number((summary?.total_carbohydrate_g ?? 0).toFixed(1)),
    protein: Number((summary?.total_protein_g ?? 0).toFixed(1)),
    fat: Number((summary?.total_fat_g ?? 0).toFixed(1)),
    sodium: Math.round(summary?.total_sodium_mg ?? 0),
  };

  const loggedList = Object.values(logByType).filter(Boolean) as MealLog[];
  const sodiumLogs = loggedList.filter((d) => d.actual_nutrition.sodium_mg !== null);
  const actualTotals = {
    kcal: Math.round(loggedList.reduce((s, d) => s + d.actual_nutrition.calories_kcal, 0)),
    carb: Number(loggedList.reduce((s, d) => s + d.actual_nutrition.carbs_g, 0).toFixed(1)),
    protein: Number(loggedList.reduce((s, d) => s + d.actual_nutrition.protein_g, 0).toFixed(1)),
    fat: Number(loggedList.reduce((s, d) => s + d.actual_nutrition.fat_g, 0).toFixed(1)),
    sodium:
      sodiumLogs.length > 0
        ? Math.round(sodiumLogs.reduce((s, d) => s + (d.actual_nutrition.sodium_mg ?? 0), 0))
        : null,
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
        subtitle="Ghi nhận bữa ăn thực tế trên máy chủ và so sánh với kế hoạch mà không ghi đè thực đơn gốc"
        actions={<DateSelector value={date} onChange={setDate} />}
      />

      {savedNotice && (
        <WarningCard level="success" title="Đã cập nhật nhật ký">
          {savedNotice}
        </WarningCard>
      )}

      {errorMsg && (
        <WarningCard level="error" title="Có lỗi xảy ra">
          {errorMsg}
        </WarningCard>
      )}

      {loading ? (
        <LoadingSkeleton rows={4} />
      ) : (
        <>
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
                    <td>
                      <strong>
                        {actualTotals.sodium !== null ? `${actualTotals.sodium} mg` : 'Chưa có dữ liệu'}
                      </strong>
                    </td>
                    <td>
                      {actualTotals.sodium !== null
                        ? `${actualTotals.sodium - plannedTotals.sodium} mg`
                        : '—'}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          {/* B & C & D. Meal Timeline */}
          <section style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {MEALS.map((m) => {
              const plannedMeal = plannedByType[m.key];
              const log = logByType[m.key];
              const isBusy = savingMeal === m.key;

              const statusLabel = !log
                ? 'Chưa ghi nhận'
                : log.status === 'eaten'
                  ? 'Đã ăn hết (100%)'
                  : log.status === 'partially_eaten'
                    ? 'Ăn một phần (50%)'
                    : log.status === 'eaten_other'
                      ? 'Ăn món khác'
                      : 'Đã bỏ bữa';

              const tone = !log
                ? 'neutral'
                : log.status === 'eaten'
                  ? 'success'
                  : log.status === 'skipped'
                    ? 'warning'
                    : 'info';

              const customItemNames = log?.items
                .filter((it) => it.custom_food_name)
                .map((it) => it.custom_food_name)
                .join(', ');

              return (
                <MealCard
                  key={m.key}
                  title={m.title}
                  timeRange={m.time}
                  totalKcal={
                    log
                      ? log.actual_nutrition.calories_kcal
                      : plannedMeal?.total_energy_kcal ?? 0
                  }
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

                    {log && (
                      <div style={{ fontSize: 13, color: 'var(--dc-text-secondary)' }}>
                        <strong>Dinh dưỡng thực tế (Backend tính):</strong>{' '}
                        {log.actual_nutrition.calories_kcal} kcal · Carb {log.actual_nutrition.carbs_g}g · Đạm{' '}
                        {log.actual_nutrition.protein_g}g · Béo {log.actual_nutrition.fat_g}g
                        {log.actual_nutrition.fiber_g !== null
                          ? ` · Xơ ${log.actual_nutrition.fiber_g}g`
                          : ''}
                        {log.actual_nutrition.sodium_mg !== null
                          ? ` · Natri ${Math.round(log.actual_nutrition.sodium_mg)}mg`
                          : ''}
                      </div>
                    )}

                    {customItemNames && (
                      <div style={{ fontSize: 13.5 }}>
                        <strong>Món thực tế ngoài kế hoạch:</strong> {customItemNames}
                      </div>
                    )}

                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                      <PrimaryButton
                        size="sm"
                        icon={<Check size={14} />}
                        loading={isBusy}
                        onClick={() => handleLogAction(m.key, 'eaten', 1.0)}
                      >
                        Ăn hết khẩu phần
                      </PrimaryButton>
                      <SecondaryButton
                        size="sm"
                        variant="blue"
                        disabled={isBusy}
                        onClick={() => handleLogAction(m.key, 'partially_eaten', 0.5)}
                      >
                        Ăn một phần (50%)
                      </SecondaryButton>
                      <SecondaryButton
                        size="sm"
                        icon={<MinusCircle size={14} />}
                        disabled={isBusy}
                        onClick={() => handleLogAction(m.key, 'skipped', 0)}
                      >
                        Bỏ bữa
                      </SecondaryButton>
                      {log && (
                        <SecondaryButton
                          size="sm"
                          icon={<Trash2 size={14} />}
                          disabled={isBusy}
                          onClick={() => handleDeleteLog(m.key, log.id)}
                        >
                          Xóa nhật ký
                        </SecondaryButton>
                      )}
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
                          disabled={isBusy}
                        />
                        <SecondaryButton
                          size="sm"
                          icon={<Utensils size={14} />}
                          disabled={isBusy}
                          onClick={() =>
                            handleLogAction(
                              m.key,
                              'eaten_other',
                              1.0,
                              customFoodInputs[m.key] || 'Món ngoài kế hoạch'
                            )
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
                          value={noteInputs[m.key] ?? log?.notes ?? ''}
                          onChange={(e) => setNoteInputs((p) => ({ ...p, [m.key]: e.target.value }))}
                          disabled={isBusy}
                        />
                        <SecondaryButton
                          size="sm"
                          disabled={isBusy}
                          onClick={() => handleSaveNoteOnly(m.key)}
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
            value="Lưu trữ độc lập trên PostgreSQL"
            subtitle="Mọi ghi nhận trong Nhật ký ăn uống được lưu riêng trong bảng meal_logs, không ghi đè thực đơn gốc do Recommendation Engine tạo."
          />
        </>
      )}
    </AppLayout>
  );
}
