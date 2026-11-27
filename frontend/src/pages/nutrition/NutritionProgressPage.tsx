import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Plus, Scale, TrendingUp } from 'lucide-react';
import { AppLayout } from '../../components/layout/AppLayout';
import { useAuth } from '../../context/AuthContext';
import { PrimaryButton, SecondaryButton } from '../../components/ui/Buttons';
import { StatCard, WarningCard } from '../../components/ui/Cards';
import { EmptyState, LoadingSkeleton } from '../../components/ui/Feedback';
import { PageHeader } from '../../components/ui/NavigationUI';
import {
  nutritionBackendApi,
  progressApi,
} from '../../services/nutritionApi';
import type {
  MealRecommendationResponse,
  NutritionProgressResponse,
  WeightRecord,
} from '../../types/nutrition';

type TimeRange = 7 | 30 | 90;

function formatDate(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

export function NutritionProgressPage() {
  const { user } = useAuth();
  const [range, setRange] = useState<TimeRange>(30);
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState<NutritionProgressResponse | null>(null);
  const [history, setHistory] = useState<Array<{
    id: string;
    meal_type: string;
    algorithm_version: string;
    generated_at: string;
    result: MealRecommendationResponse;
  }>>([]);
  const [hoverPoint, setHoverPoint] = useState<WeightRecord | null>(null);

  // Weight quick-log form
  const [weightInput, setWeightInput] = useState('');
  const [weightDate, setWeightDate] = useState(() => formatDate(new Date()));
  const [savingWeight, setSavingWeight] = useState(false);
  const [weightFeedback, setWeightFeedback] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);

  const loadProgress = useCallback(async (userId: string, days: TimeRange) => {
    setLoading(true);
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - (days - 1));

    try {
      const [progRes, recs] = await Promise.all([
        progressApi
          .getProgress({ date_from: formatDate(start), date_to: formatDate(end) })
          .catch(() => null),
        nutritionBackendApi.getHistory(userId, 30).catch(() => []),
      ]);
      setProgress(progRes);
      setHistory(recs);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!user) return;
    void loadProgress(user.id, range);
  }, [user, range, loadProgress]);

  if (!user) return null;

  const handleLogWeight = async (e: FormEvent) => {
    e.preventDefault();
    setWeightFeedback(null);
    const kg = Number(weightInput);
    if (!weightInput || Number.isNaN(kg) || kg <= 20 || kg > 300) {
      setWeightFeedback({ type: 'error', msg: 'Vui lòng nhập cân nặng hợp lệ (20 – 300 kg).' });
      return;
    }

    setSavingWeight(true);
    try {
      await progressApi.logWeight({ weight_kg: kg, recorded_at: weightDate });
      setWeightInput('');
      setWeightFeedback({
        type: 'success',
        msg: `Đã lưu cân nặng ${kg} kg cho ngày ${weightDate} và đồng bộ hồ sơ sức khỏe.`,
      });
      await loadProgress(user.id, range);
    } catch (err) {
      setWeightFeedback({
        type: 'error',
        msg: err instanceof Error ? err.message : 'Không thể lưu cân nặng. Vui lòng thử lại.',
      });
    } finally {
      setSavingWeight(false);
    }
  };

  const weightRecords = progress?.weight.records ?? [];
  const latestWeight = progress?.weight.latest_kg ?? null;
  const previousWeight = progress?.weight.previous_kg ?? null;
  const weightDelta =
    latestWeight !== null && previousWeight !== null
      ? Number((latestWeight - previousWeight).toFixed(1))
      : null;

  const summary = progress?.summary;
  const loggedMeals = summary?.total_meals_logged ?? 0;
  const skippedMeals = summary?.total_meals_skipped ?? 0;
  const totalTracked = loggedMeals + skippedMeals;
  const compliancePct = Math.round((summary?.meal_logging_rate ?? 0) * 100);

  const trends = progress?.nutrition_trends ?? [];
  const totalPlannedKcal = Math.round(
    trends.reduce((s, t) => s + t.planned_calories_kcal, 0)
  );
  const totalActualKcal = Math.round(
    trends.reduce((s, t) => s + t.actual_calories_kcal, 0)
  );
  const totalPlannedCarb = Number(
    trends.reduce((s, t) => s + t.planned_carbs_g, 0).toFixed(1)
  );
  const totalActualCarb = Number(
    trends.reduce((s, t) => s + t.actual_carbs_g, 0).toFixed(1)
  );

  // SVG chart coordinates
  const chartW = 560;
  const chartH = 170;
  const minW =
    weightRecords.length > 0
      ? Math.min(...weightRecords.map((w) => w.weight_kg)) - 2
      : 40;
  const maxW =
    weightRecords.length > 0
      ? Math.max(...weightRecords.map((w) => w.weight_kg)) + 2
      : 90;
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
        subtitle="Tổng hợp xu hướng cân nặng, tuân thủ nhật ký ăn uống (Planned vs Actual) từ PostgreSQL"
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
          {/* B. Weight Tracking & Quick Upsert Form */}
          <section className="dc-card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
              <div>
                <h2 style={{ fontSize: 17 }}>Biểu đồ theo dõi cân nặng (kg)</h2>
                <span style={{ fontSize: 13, color: 'var(--dc-text-secondary)' }}>
                  Đơn vị: kg · Khoảng thời gian: {progress?.period.date_from} → {progress?.period.date_to}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 16, fontSize: 14 }}>
                <span>Gần nhất: <strong>{latestWeight !== null ? `${latestWeight} kg` : 'Chưa có'}</strong></span>
                <span>
                  So với lần trước:{' '}
                  <strong>
                    {weightDelta !== null ? `${weightDelta > 0 ? '+' : ''}${weightDelta} kg` : 'Chưa đủ dữ liệu'}
                  </strong>
                </span>
              </div>
            </div>

            <form
              onSubmit={handleLogWeight}
              style={{ display: 'flex', flexWrap: 'wrap', gap: 10, alignItems: 'center' }}
            >
              <input
                type="date"
                className="dc-input"
                style={{ width: 170 }}
                value={weightDate}
                onChange={(e) => setWeightDate(e.target.value)}
                disabled={savingWeight}
              />
              <input
                type="number"
                step="0.1"
                className="dc-input"
                style={{ width: 180 }}
                placeholder="Nhập cân nặng (kg)..."
                value={weightInput}
                onChange={(e) => setWeightInput(e.target.value)}
                disabled={savingWeight}
              />
              <PrimaryButton type="submit" size="sm" loading={savingWeight} icon={<Plus size={15} />}>
                Lưu cân nặng
              </PrimaryButton>
            </form>

            {weightFeedback && (
              <WarningCard
                level={weightFeedback.type === 'success' ? 'success' : 'error'}
                title={weightFeedback.type === 'success' ? 'Đã ghi nhận cân nặng' : 'Lỗi ghi nhận'}
              >
                {weightFeedback.msg}
              </WarningCard>
            )}

            {weightRecords.length === 0 ? (
              <EmptyState
                icon={<Scale size={24} />}
                title="Chưa có dữ liệu cân nặng trong giai đoạn này"
                description="Hãy nhập cân nặng ở biểu mẫu phía trên để bắt đầu theo dõi xu hướng trên máy chủ."
              />
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <svg viewBox={`0 0 ${chartW} ${chartH}`} style={{ width: '100%', maxWidth: 680, height: 190 }}>
                  <line x1={40} y1={15} x2={40} y2={chartH - 30} stroke="#CBD5E1" />
                  <line x1={40} y1={chartH - 30} x2={chartW - 20} y2={chartH - 30} stroke="#CBD5E1" />
                  <text x={6} y={24} fontSize={11} fill="#64748B">{maxW.toFixed(0)}kg</text>
                  <text x={6} y={chartH - 32} fontSize={11} fill="#64748B">{minW.toFixed(0)}kg</text>

                  {weightRecords.length > 1 && (
                    <polyline
                      fill="none"
                      stroke="#16865A"
                      strokeWidth={2.5}
                      points={weightRecords
                        .map((pt, i) => {
                          const x = 55 + (i / Math.max(1, weightRecords.length - 1)) * (chartW - 95);
                          const y = chartH - 35 - ((pt.weight_kg - minW) / spanW) * (chartH - 55);
                          return `${x},${y}`;
                        })
                        .join(' ')}
                    />
                  )}

                  {weightRecords.map((pt, i) => {
                    const x =
                      weightRecords.length === 1
                        ? chartW / 2
                        : 55 + (i / Math.max(1, weightRecords.length - 1)) * (chartW - 95);
                    const y = chartH - 35 - ((pt.weight_kg - minW) / spanW) * (chartH - 55);
                    return (
                      <g
                        key={pt.id}
                        onMouseEnter={() => setHoverPoint(pt)}
                        onMouseLeave={() => setHoverPoint(null)}
                        style={{ cursor: 'pointer' }}
                      >
                        <circle cx={x} cy={y} r={5} fill="#16865A" stroke="#ffffff" strokeWidth={2} />
                        <text x={x - 22} y={chartH - 12} fontSize={10.5} fill="#64748B">
                          {pt.recorded_at.slice(5)}
                        </text>
                      </g>
                    );
                  })}
                </svg>
                {hoverPoint && (
                  <div style={{ fontSize: 13, color: 'var(--dc-primary)', fontWeight: 600 }}>
                    Chi tiết: Ngày {hoverPoint.recorded_at} — {hoverPoint.weight_kg} kg
                  </div>
                )}
              </div>
            )}
          </section>

          {/* C & D. Nutrition Tracking & Meal Compliance */}
          <section className="dc-grid-4">
            <StatCard
              label="Thực tế / Kế hoạch (Kcal)"
              value={`${totalActualKcal} / ${totalPlannedKcal}`}
              unit="kcal"
              subtitle={`Trong ${trends.length} ngày có dữ liệu`}
              icon={<TrendingUp size={18} />}
            />
            <StatCard
              label="Carb thực tế / Kế hoạch"
              value={`${totalActualCarb}g / ${totalPlannedCarb}g`}
              subtitle="Tổng hợp theo kỳ đã chọn"
              tone="secondary"
            />
            <StatCard
              label="Số bữa đã ăn / Bỏ qua"
              value={`${loggedMeals} / ${skippedMeals}`}
              subtitle="Ghi nhận thực tế trong meal_logs"
            />
            <StatCard
              label="Tỷ lệ hoàn thành nhật ký"
              value={`${compliancePct}%`}
              subtitle={totalTracked > 0 ? `${loggedMeals}/${totalTracked} bữa` : 'Chưa có dữ liệu'}
              tone="primary"
            />
          </section>

          {/* D2. Daily Planned vs Actual Trends */}
          <section className="dc-card">
            <h2 style={{ fontSize: 17, marginBottom: 14 }}>
              Đối chiếu Kế hoạch vs Thực tế theo ngày
            </h2>
            {trends.length === 0 ? (
              <p style={{ fontSize: 14, color: 'var(--dc-text-secondary)' }}>
                Chưa có dữ liệu thực đơn hoặc nhật ký ăn uống trong khoảng thời gian đã chọn.
              </p>
            ) : (
              <div className="dc-table-wrap">
                <table className="dc-table">
                  <thead>
                    <tr>
                      <th>Ngày</th>
                      <th>Kế hoạch (Kcal)</th>
                      <th>Thực tế (Kcal)</th>
                      <th>Kế hoạch (Carb)</th>
                      <th>Thực tế (Carb)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trends.map((t) => (
                      <tr key={t.date}>
                        <td>{t.date}</td>
                        <td>{Math.round(t.planned_calories_kcal)} kcal</td>
                        <td><strong>{Math.round(t.actual_calories_kcal)} kcal</strong></td>
                        <td>{t.planned_carbs_g} g</td>
                        <td><strong>{t.actual_carbs_g} g</strong></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
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
