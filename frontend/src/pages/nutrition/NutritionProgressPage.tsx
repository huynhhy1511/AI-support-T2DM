import { useEffect, useState } from 'react';
import { Scale, TrendingUp } from 'lucide-react';
import { AppLayout } from '../../components/layout/AppLayout';
import { useAuth } from '../../context/AuthContext';
import { SecondaryButton } from '../../components/ui/Buttons';
import { StatCard, WarningCard } from '../../components/ui/Cards';
import { EmptyState, LoadingSkeleton } from '../../components/ui/Feedback';
import { PageHeader } from '../../components/ui/NavigationUI';
import {
  foodDiaryStorage,
  mealPlanStorage,
  nutritionBackendApi,
  weightHistoryStorage,
} from '../../services/nutritionApi';
import type { MealRecommendationResponse, WeightLogEntry } from '../../types/nutrition';

type TimeRange = 7 | 30 | 90;

export function NutritionProgressPage() {
  const { user } = useAuth();
  const [range, setRange] = useState<TimeRange>(7);
  const [loading, setLoading] = useState(true);
  const [weights, setWeights] = useState<WeightLogEntry[]>([]);
  const [history, setHistory] = useState<Array<{
    id: string;
    meal_type: string;
    algorithm_version: string;
    generated_at: string;
    result: MealRecommendationResponse;
  }>>([]);
  const [hoverPoint, setHoverPoint] = useState<WeightLogEntry | null>(null);

  useEffect(() => {
    if (!user) return;
    let active = true;
    (async () => {
      setLoading(true);
      try {
        const recs = await nutritionBackendApi.getHistory(user.id, 30).catch(() => []);
        if (active) setHistory(recs);
      } finally {
        if (active) {
          setWeights(weightHistoryStorage.getAll(user.id));
          setLoading(false);
        }
      }
    })();
    return () => {
      active = false;
    };
  }, [user]);

  if (!user) return null;

  // Filter weight history by range
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - range);
  const cutoffStr = cutoff.toISOString().slice(0, 10);
  const filteredWeights = weights.filter((w) => w.date >= cutoffStr);

  const latestWeight = filteredWeights.length > 0 ? filteredWeights[filteredWeights.length - 1].weight_kg : null;
  const firstWeight = filteredWeights.length > 0 ? filteredWeights[0].weight_kg : null;
  const weightDelta =
    latestWeight !== null && firstWeight !== null
      ? Number((latestWeight - firstWeight).toFixed(1))
      : null;

  // Aggregate diary & planned meals
  const diaryDates = foodDiaryStorage.listDates(user.id).filter((d) => d >= cutoffStr);
  let loggedMeals = 0;
  let skippedMeals = 0;
  let totalPlannedKcal = 0;
  let totalActualKcal = 0;
  let totalActualCarb = 0;
  let totalActualProtein = 0;
  let totalActualFat = 0;

  for (const d of diaryDates) {
    const plan = mealPlanStorage.getByDate(user.id, d);
    if (plan) {
      totalPlannedKcal += Object.values(plan.meals).reduce(
        (s, m) => s + (m?.total_energy_kcal ?? 0),
        0
      );
    }
    const entries = foodDiaryStorage.getByDate(user.id, d);
    if (entries) {
      for (const e of Object.values(entries)) {
        if (e.status === 'skipped') skippedMeals += 1;
        else if (e.status !== 'planned') {
          loggedMeals += 1;
          totalActualKcal += e.actual_energy_kcal;
          totalActualCarb += e.actual_carbohydrate_g;
          totalActualProtein += e.actual_protein_g;
          totalActualFat += e.actual_fat_g;
        }
      }
    }
  }
  const totalTracked = loggedMeals + skippedMeals;
  const compliancePct = totalTracked > 0 ? Math.round((loggedMeals / totalTracked) * 100) : 0;

  // SVG chart coordinates
  const chartW = 560;
  const chartH = 170;
  const minW = filteredWeights.length > 0 ? Math.min(...filteredWeights.map((w) => w.weight_kg)) - 2 : 40;
  const maxW = filteredWeights.length > 0 ? Math.max(...filteredWeights.map((w) => w.weight_kg)) + 2 : 90;
  const spanW = Math.max(1, maxW - minW);

  return (
    <AppLayout
      breadcrumbs={[
        { label: 'Diabetes Care', to: '/dashboard' },
        { label: 'Dinh dưỡng', to: '/nutrition' },
        { label: 'Theo dõi tiến triển' },
      ]}
    >
      <PageHeader
        title="Theo dõi tiến triển dinh dưỡng"
        subtitle="Tổng hợp xu hướng cân nặng, tuân thủ nhật ký ăn uống và lịch sử thực đơn"
        actions={
          <div style={{ display: 'flex', gap: 8 }}>
            {([7, 30, 90] as TimeRange[]).map((r) => (
              <SecondaryButton
                key={r}
                size="sm"
                variant={range === r ? 'blue' : 'default'}
                onClick={() => setRange(r)}
              >
                {r === 7 ? '7 ngày' : r === 30 ? '30 ngày' : '3 tháng'}
              </SecondaryButton>
            ))}
          </div>
        }
      />

      <WarningCard level="info" title="Giới hạn diễn giải lâm sàng">
        Các số liệu tiến triển phản ánh mức độ ghi nhận nhật ký và thay đổi cân nặng theo thời gian;
        không dùng để tự đánh giá hiệu quả điều trị hay mức kiểm soát đường huyết thay cho xét nghiệm HbA1c và bác sĩ.
      </WarningCard>

      {loading ? (
        <LoadingSkeleton rows={4} />
      ) : (
        <>
          {/* B. Weight Tracking */}
          <section className="dc-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
              <div>
                <h2 style={{ fontSize: 17 }}>Biểu đồ theo dõi cân nặng (kg)</h2>
                <span style={{ fontSize: 13, color: 'var(--dc-text-secondary)' }}>
                  Đơn vị: kg · Khoảng thời gian: {range} ngày gần nhất
                </span>
              </div>
              <div style={{ display: 'flex', gap: 16, fontSize: 14 }}>
                <span>Gần nhất: <strong>{latestWeight !== null ? `${latestWeight} kg` : 'Chưa có'}</strong></span>
                <span>
                  Thay đổi:{' '}
                  <strong>
                    {weightDelta !== null ? `${weightDelta > 0 ? '+' : ''}${weightDelta} kg` : 'Chưa đủ dữ liệu'}
                  </strong>
                </span>
              </div>
            </div>

            {filteredWeights.length === 0 ? (
              <EmptyState
                icon={<Scale size={24} />}
                title="Chưa có dữ liệu cân nặng"
                description="Hãy lưu cân nặng tại trang Hồ sơ dinh dưỡng để bắt đầu theo dõi xu hướng."
              />
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <svg viewBox={`0 0 ${chartW} ${chartH}`} style={{ width: '100%', maxWidth: 680, height: 190 }}>
                  <line x1={40} y1={15} x2={40} y2={chartH - 30} stroke="#CBD5E1" />
                  <line x1={40} y1={chartH - 30} x2={chartW - 20} y2={chartH - 30} stroke="#CBD5E1" />
                  <text x={6} y={24} fontSize={11} fill="#64748B">{maxW.toFixed(0)}kg</text>
                  <text x={6} y={chartH - 32} fontSize={11} fill="#64748B">{minW.toFixed(0)}kg</text>

                  {filteredWeights.length > 1 && (
                    <polyline
                      fill="none"
                      stroke="#16865A"
                      strokeWidth={2.5}
                      points={filteredWeights
                        .map((pt, i) => {
                          const x = 55 + (i / Math.max(1, filteredWeights.length - 1)) * (chartW - 95);
                          const y = chartH - 35 - ((pt.weight_kg - minW) / spanW) * (chartH - 55);
                          return `${x},${y}`;
                        })
                        .join(' ')}
                    />
                  )}

                  {filteredWeights.map((pt, i) => {
                    const x =
                      filteredWeights.length === 1
                        ? chartW / 2
                        : 55 + (i / Math.max(1, filteredWeights.length - 1)) * (chartW - 95);
                    const y = chartH - 35 - ((pt.weight_kg - minW) / spanW) * (chartH - 55);
                    return (
                      <g
                        key={pt.date}
                        onMouseEnter={() => setHoverPoint(pt)}
                        onMouseLeave={() => setHoverPoint(null)}
                        style={{ cursor: 'pointer' }}
                      >
                        <circle cx={x} cy={y} r={5} fill="#16865A" stroke="#ffffff" strokeWidth={2} />
                        <text x={x - 22} y={chartH - 12} fontSize={10.5} fill="#64748B">
                          {pt.date.slice(5)}
                        </text>
                      </g>
                    );
                  })}
                </svg>
                {hoverPoint && (
                  <div style={{ fontSize: 13, color: 'var(--dc-primary)', fontWeight: 600 }}>
                    Chi tiết: Ngày {hoverPoint.date} — {hoverPoint.weight_kg} kg
                  </div>
                )}
              </div>
            )}
          </section>

          {/* C & D. Nutrition Tracking & Meal Compliance */}
          <section className="dc-grid-4">
            <StatCard
              label="Kế hoạch vs Thực tế (Kcal)"
              value={`${Math.round(totalActualKcal)} / ${Math.round(totalPlannedKcal)}`}
              unit="kcal"
              subtitle={`Trong ${diaryDates.length} ngày có ghi nhận`}
              icon={<TrendingUp size={18} />}
            />
            <StatCard
              label="Macro thực tế (Carb / Đạm / Béo)"
              value={`${Math.round(totalActualCarb)}g / ${Math.round(totalActualProtein)}g`}
              subtitle={`Chất béo: ${Math.round(totalActualFat)}g`}
              tone="secondary"
            />
            <StatCard
              label="Số bữa đã ghi nhận / Bỏ qua"
              value={`${loggedMeals} / ${skippedMeals}`}
              subtitle="Ghi nhận thực tế trong nhật ký"
            />
            <StatCard
              label="Tỷ lệ hoàn thành nhật ký"
              value={`${compliancePct}%`}
              subtitle={totalTracked > 0 ? `${loggedMeals}/${totalTracked} bữa` : 'Chưa có dữ liệu'}
              tone="primary"
            />
          </section>

          {/* E. History */}
          <section className="dc-card">
            <h2 style={{ fontSize: 17, marginBottom: 14 }}>Lịch sử thực đơn đã tạo (từ Backend PostgreSQL)</h2>
            {history.length === 0 ? (
              <p style={{ fontSize: 14, color: 'var(--dc-text-secondary)' }}>
                Chưa có bản ghi thực đơn nào được lưu trên máy chủ.
              </p>
            ) : (
              <div className="dc-table-wrap">
                <table className="dc-table">
                  <thead>
                    <tr>
                      <th>Thời gian tạo</th>
                      <th>Bữa ăn</th>
                      <th>Tổng Calories</th>
                      <th>Carb / Đạm / Xơ</th>
                      <th>Phiên bản</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((h) => (
                      <tr key={h.id}>
                        <td>{new Date(h.generated_at).toLocaleString('vi-VN')}</td>
                        <td>{h.meal_type}</td>
                        <td><strong>{h.result.total_energy_kcal} kcal</strong></td>
                        <td>
                          {h.result.total_carbohydrate_g}g / {h.result.total_protein_g}g / {h.result.total_fiber_g}g
                        </td>
                        <td>{h.algorithm_version}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </AppLayout>
  );
}
