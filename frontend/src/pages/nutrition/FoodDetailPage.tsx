import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, BookOpen, ExternalLink } from 'lucide-react';
import { AppLayout } from '../../components/layout/AppLayout';
import { PrimaryButton, SecondaryButton } from '../../components/ui/Buttons';
import { FoodVisual, StatCard, WarningCard } from '../../components/ui/Cards';
import { LoadingSkeleton } from '../../components/ui/Feedback';
import { PageHeader } from '../../components/ui/NavigationUI';
import { StatusBadge } from '../../components/ui/Badges';
import { foodsApi } from '../../services/nutritionApi';
import type { FoodItem, PreparationStateType } from '../../types/nutrition';

const PREP_STATE_LABELS: Record<PreparationStateType, string> = {
  cooked: 'Đã nấu chín (Cooked)',
  raw: 'Tươi sống (Raw)',
  ready_to_eat: 'Ăn liền / Chế biến sẵn (Ready-to-eat)',
};

export function FoodDetailPage() {
  const { foodId } = useParams<{ foodId: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [food, setFood] = useState<FoodItem | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!foodId) return;
    let active = true;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await foodsApi.getById(foodId);
        if (active) setFood(data);
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : 'Không tìm thấy món ăn.');
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [foodId]);

  const formatOrEmpty = (val: number | null | undefined, unit = '') => {
    if (val === null || val === undefined) return 'Chưa có dữ liệu';
    return `${val}${unit}`;
  };

  return (
    <AppLayout
      breadcrumbs={[
        { label: 'Diabetes Care', to: '/dashboard' },
        { label: 'Dinh dưỡng', to: '/nutrition' },
        { label: 'Thực đơn hằng ngày', to: '/nutrition/daily' },
        { label: food?.name || 'Chi tiết món ăn' },
      ]}
    >
      <PageHeader
        title="Chi tiết món ăn"
        subtitle="Thông tin dinh dưỡng chuẩn hóa theo khẩu phần phục vụ tự quản lý đái tháo đường type 2"
        actions={
          <SecondaryButton icon={<ArrowLeft size={16} />} onClick={() => navigate('/nutrition/daily')}>
            Quay lại thực đơn
          </SecondaryButton>
        }
      />

      {loading ? (
        <LoadingSkeleton rows={4} />
      ) : error || !food ? (
        <WarningCard level="error" title="Không tải được thông tin món ăn">
          {error || 'Món ăn không tồn tại trong cơ sở dữ liệu.'}
        </WarningCard>
      ) : (
        <>
          <div className="dc-card dc-grid-2" style={{ alignItems: 'center' }}>
            <FoodVisual category={food.category} size="lg" />

            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                <StatusBadge tone="info">{food.category}</StatusBadge>
                <StatusBadge tone="neutral">
                  {PREP_STATE_LABELS[food.preparation_state] ?? food.preparation_state}
                </StatusBadge>
                {food.is_test_data && <StatusBadge tone="warning">Dữ liệu thử nghiệm</StatusBadge>}
              </div>

              <h2 style={{ fontSize: 22 }}>{food.name}</h2>
              <p style={{ fontSize: 14.5, color: 'var(--dc-text-secondary)' }}>
                Khẩu phần tiêu chuẩn: <strong>{food.serving_size_g}g</strong>
              </p>

              <div className="dc-grid-3">
                <StatCard label="Calories" value={food.energy_kcal} unit="kcal" />
                <StatCard label="Carbohydrate" value={food.carbohydrate_g} unit="g" tone="secondary" />
                <StatCard label="Protein" value={food.protein_g} unit="g" />
              </div>

              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', paddingTop: 6 }}>
                <PrimaryButton icon={<BookOpen size={16} />} onClick={() => navigate('/nutrition/diary')}>
                  Ghi nhận món ăn
                </PrimaryButton>
                <SecondaryButton onClick={() => navigate('/nutrition/daily')}>
                  Quay lại thực đơn
                </SecondaryButton>
              </div>
            </div>
          </div>

          <section className="dc-card">
            <h3 style={{ fontSize: 17, marginBottom: 14 }}>Bảng thành phần dinh dưỡng chi tiết</h3>
            <div className="dc-grid-4">
              <StatCard label="Chất béo (Fat)" value={food.fat_g} unit="g" />
              <StatCard label="Chất béo bão hòa" value={formatOrEmpty(food.saturated_fat_g, 'g')} />
              <StatCard label="Chất xơ (Fiber)" value={formatOrEmpty(food.fiber_g, 'g')} />
              <StatCard label="Natri (Sodium)" value={formatOrEmpty(food.sodium_mg, 'mg')} />
              <StatCard
                label="Đường đơn (Sugar)"
                value={formatOrEmpty(food.sugar_g, 'g')}
                subtitle="Giữ nguyên trạng thái trống nếu chưa có tách đường đơn xác thực"
              />
              <StatCard label="Chỉ số đường huyết (GI)" value={formatOrEmpty(food.glycemic_index)} />
              <StatCard label="Tải lượng đường huyết (GL)" value={formatOrEmpty(food.glycemic_load)} />
            </div>
          </section>

          <div className="dc-grid-2">
            <section className="dc-card" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <h3 style={{ fontSize: 16 }}>Thành phần, chế biến & Lưu ý ĐTĐ Type 2</h3>
              <p style={{ fontSize: 14, color: 'var(--dc-text-secondary)' }}>
                <strong>Trạng thái chế biến:</strong>{' '}
                {PREP_STATE_LABELS[food.preparation_state] ?? food.preparation_state}
              </p>
              <p style={{ fontSize: 14, color: 'var(--dc-text-secondary)' }}>
                <strong>Cách chế biến & khẩu phần:</strong> Ưu tiên luộc, hấp, áp chảo ít dầu; hạn chế nêm muối, nước mắm và đường tinh luyện.
              </p>
              <p style={{ fontSize: 14, color: 'var(--dc-text-secondary)' }}>
                <strong>Lưu ý người mắc ĐTĐ:</strong> Kết hợp rau xanh giàu chất xơ trong bữa ăn để làm chậm hấp thu đường sau ăn; kiểm soát tổng carbohydrate theo khuyến nghị.
              </p>
            </section>

            <section className="dc-card" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <h3 style={{ fontSize: 16 }}>Dị nguyên & Nguồn dữ liệu chuẩn hóa</h3>
              <div>
                <strong style={{ fontSize: 14, color: 'var(--dc-text-secondary)' }}>
                  Dị nguyên chuẩn hóa (Allergens):
                </strong>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
                  {food.allergens && food.allergens.length > 0 ? (
                    food.allergens.map((al) => (
                      <StatusBadge key={al.id} tone="danger">
                        {al.name_vi} ({al.code})
                      </StatusBadge>
                    ))
                  ) : (
                    <StatusBadge tone="success">Không ghi nhận dị nguyên phổ biến</StatusBadge>
                  )}
                </div>
              </div>

              <p style={{ fontSize: 14, color: 'var(--dc-text-secondary)', marginTop: 4 }}>
                <strong>Mã nguồn chuẩn hóa:</strong> {food.data_source} · <strong>Phiên bản:</strong>{' '}
                {food.data_version}
              </p>
              <p style={{ fontSize: 14, color: 'var(--dc-text-secondary)' }}>
                <strong>Tài liệu tham chiếu:</strong> {food.source_name || 'Chưa có dữ liệu nguồn'}
              </p>
              {food.source_url && (
                <a
                  href={food.source_url}
                  target="_blank"
                  rel="noreferrer"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 14 }}
                >
                  <span>Xem tài liệu nguồn</span>
                  <ExternalLink size={14} />
                </a>
              )}
            </section>
          </div>
        </>
      )}
    </AppLayout>
  );
}
