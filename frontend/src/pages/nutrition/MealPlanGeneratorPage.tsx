import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, Sparkles } from 'lucide-react';
import { AppLayout } from '../../components/layout/AppLayout';
import { useAuth } from '../../context/AuthContext';
import { PrimaryButton, SecondaryButton } from '../../components/ui/Buttons';
import { WarningCard } from '../../components/ui/Cards';
import { FormField } from '../../components/ui/FormControls';
import { StatusBadge } from '../../components/ui/Badges';
import { PageHeader } from '../../components/ui/NavigationUI';
import {
  healthProfileApi,
  nutritionBackendApi,
} from '../../services/nutritionApi';
import type {
  HealthProfile,
  HealthProfileCompleteness,
  MealType,
  NutritionGoalType,
} from '../../types/nutrition';

const MEAL_OPTIONS: Array<{ value: MealType; label: string }> = [
  { value: 'breakfast', label: 'Bữa sáng' },
  { value: 'lunch', label: 'Bữa trưa' },
  { value: 'dinner', label: 'Bữa tối' },
  { value: 'snack', label: 'Bữa phụ' },
];

const MISSING_FIELD_LABELS: Record<string, string> = {
  date_of_birth: 'Ngày sinh',
  sex: 'Giới tính',
  height_cm: 'Chiều cao',
  weight_kg: 'Cân nặng',
  activity_level: 'Mức vận động',
};

function todayStr(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

export function MealPlanGeneratorPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [profile, setProfile] = useState<HealthProfile | null>(null);
  const [completeness, setCompleteness] = useState<HealthProfileCompleteness | null>(null);
  const [date, setDate] = useState(todayStr());
  const [diet, setDiet] = useState('normal');
  const [goal, setGoal] = useState<NutritionGoalType>('maintenance');
  const [extraExcluded, setExtraExcluded] = useState('');
  const [selectedMeals, setSelectedMeals] = useState<MealType[]>(['breakfast', 'lunch', 'dinner', 'snack']);

  const [generating, setGenerating] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [abstentionError, setAbstentionError] = useState<{
    reasonCode?: string | null;
    message: string;
    notes?: string[];
    isCritical?: boolean;
  } | null>(null);

  useEffect(() => {
    if (!user) return;
    let active = true;
    Promise.all([
      healthProfileApi.getMe().catch(() => null),
      healthProfileApi.getCompleteness().catch(() => null),
    ]).then(([hp, comp]) => {
      if (!active) return;
      setProfile(hp);
      setCompleteness(comp);
      if (hp?.dietary_preference) setDiet(hp.dietary_preference);
      if (hp?.nutrition_goal) setGoal(hp.nutrition_goal);
    });
    return () => {
      active = false;
    };
  }, [user]);

  if (!user) return null;

  const profileAllergies = profile?.allergies ?? [];
  const profileComorbidities = profile?.comorbidities ?? [];
  const hasCKD = profileComorbidities.some(
    (c) => c.toLowerCase().includes('ckd') || c.toLowerCase().includes('bệnh thận')
  );
  const missingFields = (completeness?.missing_fields ?? []).map(
    (f) => MISSING_FIELD_LABELS[f] ?? f
  );

  const toggleMeal = (m: MealType) => {
    setSelectedMeals((prev) =>
      prev.includes(m) ? prev.filter((x) => x !== m) : [...prev, m]
    );
  };

  const handleGenerate = async (e: FormEvent) => {
    e.preventDefault();
    setAbstentionError(null);
    setStatusMsg(null);

    if (selectedMeals.length === 0) {
      setAbstentionError({
        message: 'Vui lòng chọn ít nhất 1 bữa ăn để tạo thực đơn.',
      });
      return;
    }

    setGenerating(true);
    setStatusMsg('Đang kiểm tra ràng buộc an toàn và gọi Nutrition Recommendation Engine trên máy chủ...');

    try {
      const extraKeywords = extraExcluded
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);

      const hasHypertension = profileComorbidities.some(
        (c) => c.toLowerCase().includes('hypertension') || c.toLowerCase().includes('tăng huyết áp')
      );
      const activePref =
        diet !== 'normal' ? diet : hasHypertension ? 'low_sodium' : null;

      for (const mtype of selectedMeals) {
        const res = await nutritionBackendApi.recommendMeal({
          user_id: user.id,
          meal_type: mtype,
          dietary_preference: activePref,
          excluded_allergens: profileAllergies.length > 0 ? profileAllergies : null,
          excluded_keywords: extraKeywords.length > 0 ? extraKeywords : null,
        });

        // Xử lý trực tiếp từ chối có chủ đích (HTTP 200 status="abstained") từ Backend Safety Guard
        if (res.status === 'abstained') {
          setAbstentionError({
            reasonCode: res.reason_code,
            message: res.meal_balance_evaluation,
            notes: res.safety_notes,
            isCritical: res.reason_code === 'CKD_SPECIALIST_REQUIRED',
          });
          return;
        }
      }

      navigate(`/nutrition/daily?date=${encodeURIComponent(date)}`);
    } catch (err) {
      setAbstentionError({
        message:
          err instanceof Error
            ? err.message
            : 'Không thể tạo thực đơn đáp ứng các ràng buộc hiện tại.',
      });
    } finally {
      setGenerating(false);
      setStatusMsg(null);
    }
  };

  return (
    <AppLayout
      breadcrumbs={[
        { label: 'Diabetes Care', to: '/dashboard' },
        { label: 'Dinh dưỡng', to: '/nutrition' },
        { label: 'Tạo thực đơn AI' },
      ]}
    >
      <PageHeader
        title="Tạo thực đơn bằng AI"
        subtitle="Thiết lập thông số bữa ăn và gửi tới Nutrition Recommendation Engine trên máy chủ"
      />

      {abstentionError && (
        <WarningCard
          level={abstentionError.isCritical ? 'critical' : 'error'}
          title={
            abstentionError.reasonCode
              ? `Engine tạm dừng tạo thực đơn (${abstentionError.reasonCode})`
              : 'Engine tạm dừng / từ chối tạo thực đơn'
          }
          action={
            <div style={{ display: 'flex', gap: 8 }}>
              <SecondaryButton size="sm" onClick={() => navigate('/nutrition/safety')}>
                Xem chi tiết cảnh báo an toàn
              </SecondaryButton>
              <SecondaryButton size="sm" onClick={() => navigate('/nutrition/profile')}>
                Kiểm tra hồ sơ
              </SecondaryButton>
            </div>
          }
        >
          <p>{abstentionError.message}</p>
          {abstentionError.notes && abstentionError.notes.length > 0 && (
            <ul style={{ margin: '8px 0 0', paddingLeft: 18 }}>
              {abstentionError.notes.map((n, idx) => (
                <li key={idx}>{n}</li>
              ))}
            </ul>
          )}
        </WarningCard>
      )}

      <div className="dc-split-main">
        <form onSubmit={handleGenerate} className="dc-card" style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <FormField label="Bước 1: Chọn ngày áp dụng thực đơn" required>
            <input
              type="date"
              className="dc-input"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              disabled={generating}
            />
          </FormField>

          <FormField label="Bước 2: Chọn chế độ ăn">
            <select
              className="dc-select"
              value={diet}
              onChange={(e) => setDiet(e.target.value)}
              disabled={generating}
            >
              <option value="normal">Bình thường (Cân bằng theo Plate Method)</option>
              <option value="vegetarian">Ăn chay (Vegetarian)</option>
              <option value="vegan">Thuần chay (Vegan)</option>
              <option value="low_carb">Giảm tinh bột (Low Carb)</option>
              <option value="low_sodium">Ít muối (Low Sodium)</option>
            </select>
          </FormField>

          <FormField label="Bước 3: Chọn mục tiêu dinh dưỡng">
            <select
              className="dc-select"
              value={goal}
              onChange={(e) => setGoal(e.target.value as NutritionGoalType)}
              disabled={generating}
            >
              <option value="maintenance">Ổn định đường huyết & duy trì cân nặng</option>
              <option value="weight_loss">Kiểm soát cân nặng / giảm cân an toàn</option>
            </select>
          </FormField>

          <FormField
            label="Bước 4: Nguyên liệu muốn tránh thêm (ngoài dị ứng trong hồ sơ)"
            hint="Ngăn cách bằng dấu phẩy, ví dụ: tôm, đậu phộng, hành"
          >
            <input
              className="dc-input"
              value={extraExcluded}
              onChange={(e) => setExtraExcluded(e.target.value)}
              placeholder="Ví dụ: cá hồi, đậu phụ..."
              disabled={generating}
            />
          </FormField>

          <FormField label="Bước 5: Chọn các bữa ăn cần tạo">
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
              {MEAL_OPTIONS.map((opt) => {
                const active = selectedMeals.includes(opt.value);
                return (
                  <label
                    key={opt.value}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 8,
                      padding: '8px 14px',
                      borderRadius: 10,
                      border: `1px solid ${active ? 'var(--dc-primary)' : 'var(--dc-border)'}`,
                      background: active ? 'var(--dc-primary-soft)' : 'var(--dc-surface)',
                      cursor: 'pointer',
                      fontWeight: 500,
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={active}
                      onChange={() => toggleMeal(opt.value)}
                      disabled={generating}
                    />
                    <span>{opt.label}</span>
                  </label>
                );
              })}
            </div>
          </FormField>

          {statusMsg && (
            <WarningCard level="info" title="Đang xử lý">
              {statusMsg}
            </WarningCard>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, paddingTop: 6 }}>
            <PrimaryButton type="submit" loading={generating} icon={<Sparkles size={16} />}>
              Tạo thực đơn
            </PrimaryButton>
          </div>
        </form>

        {/* Profile Summary Card */}
        <aside className="dc-card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h2 style={{ fontSize: 16 }}>Tóm tắt hồ sơ áp dụng</h2>
            <StatusBadge tone={completeness?.is_complete ? 'success' : 'warning'}>
              {completeness?.is_complete ? 'Đủ thông tin' : `Thiếu ${missingFields.length} trường`}
            </StatusBadge>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 13.5 }}>
            <div>Ngày sinh: <strong>{profile?.date_of_birth || 'Chưa có'}</strong></div>
            <div>Giới tính: <strong>{profile?.sex || 'Chưa có'}</strong></div>
            <div>Chiều cao: <strong>{profile?.height_cm != null ? `${profile.height_cm} cm` : 'Chưa có'}</strong></div>
            <div>Cân nặng: <strong>{profile?.weight_kg != null ? `${profile.weight_kg} kg` : 'Chưa có'}</strong></div>
            <div>Mức vận động: <strong>{profile?.activity_level || 'Chưa có'}</strong></div>
            <div>
              Mục tiêu năng lượng:{' '}
              <strong>
                {profile?.target_energy_kcal != null
                  ? `${Math.round(profile.target_energy_kcal)} kcal/ngày`
                  : 'Chưa tính được'}
              </strong>
            </div>
            <div>Mục tiêu: <strong>{goal === 'weight_loss' ? 'Giảm cân' : 'Duy trì'}</strong></div>
            <div>Chế độ ăn: <strong>{diet}</strong></div>
            <div>
              Dị ứng:{' '}
              <strong>{profileAllergies.length > 0 ? profileAllergies.join(', ') : 'Không'}</strong>
            </div>
            <div>
              Bệnh lý:{' '}
              <strong>{profileComorbidities.length > 0 ? profileComorbidities.join(', ') : 'Đái tháo đường Type 2'}</strong>
            </div>
          </div>

          {hasCKD && (
            <WarningCard level="critical" title="Giới hạn bệnh thận (CKD)">
              Hồ sơ ghi nhận CKD — Backend Safety Guard sẽ tạm dừng tự động sinh thực đơn để đảm bảo an toàn chuyên khoa.
            </WarningCard>
          )}

          <SecondaryButton
            size="sm"
            icon={<ShieldAlert size={15} />}
            onClick={() => navigate('/nutrition/profile')}
          >
            Chỉnh sửa hồ sơ
          </SecondaryButton>
        </aside>
      </div>
    </AppLayout>
  );
}
