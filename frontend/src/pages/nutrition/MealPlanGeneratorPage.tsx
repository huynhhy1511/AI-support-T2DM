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
  localPrefsAdapter,
  mealPlanStorage,
  nutritionBackendApi,
} from '../../services/nutritionApi';
import type { DailyMealPlan, HealthProfile, MealType } from '../../types/nutrition';

const MEAL_OPTIONS: Array<{ value: MealType; label: string }> = [
  { value: 'breakfast', label: 'Bữa sáng' },
  { value: 'lunch', label: 'Bữa trưa' },
  { value: 'dinner', label: 'Bữa tối' },
  { value: 'snack', label: 'Bữa phụ' },
];

function todayStr(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

export function MealPlanGeneratorPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [profile, setProfile] = useState<HealthProfile | null>(null);
  const [date, setDate] = useState(todayStr());
  const [diet, setDiet] = useState('normal');
  const [goal, setGoal] = useState<'weight_loss' | 'maintenance'>('maintenance');
  const [extraExcluded, setExtraExcluded] = useState('');
  const [selectedMeals, setSelectedMeals] = useState<MealType[]>(['breakfast', 'lunch', 'dinner', 'snack']);

  const [generating, setGenerating] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [abstentionError, setAbstentionError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    const prefs = localPrefsAdapter.get(user.id);
    setGoal(prefs.nutrition_goal);
    healthProfileApi
      .getByUser(user.id)
      .then((hp) => {
        setProfile(hp);
        if (hp.dietary_preference) setDiet(hp.dietary_preference);
      })
      .catch(() => setProfile(null));
  }, [user]);

  if (!user) return null;
  const prefs = localPrefsAdapter.get(user.id);
  const hasCKD = prefs.comorbidities.some((c) => c.toLowerCase().includes('ckd'));
  const missingFields: string[] = [];
  if (!profile?.date_of_birth) missingFields.push('Ngày sinh');
  if (!profile?.sex) missingFields.push('Giới tính');
  if (!profile?.height_cm) missingFields.push('Chiều cao');
  if (!profile?.weight_kg) missingFields.push('Cân nặng');
  if (!profile?.activity_level) missingFields.push('Mức vận động');

  const toggleMeal = (m: MealType) => {
    setSelectedMeals((prev) =>
      prev.includes(m) ? prev.filter((x) => x !== m) : [...prev, m]
    );
  };

  const handleGenerate = async (e: FormEvent) => {
    e.preventDefault();
    setAbstentionError(null);
    setStatusMsg(null);

    // Kiểm tra an toàn CKD: không tự ý tạo thực đơn khi có bệnh thận mạn
    if (hasCKD) {
      setAbstentionError(
        'Hồ sơ có ghi nhận bệnh thận mạn (CKD). Hệ thống không tự động tạo thực đơn vì cần kiểm soát chặt chẽ protein, kali, photpho và natri bởi bác sĩ chuyên khoa thận/dinh dưỡng.'
      );
      return;
    }

    if (selectedMeals.length === 0) {
      setAbstentionError('Vui lòng chọn ít nhất 1 bữa ăn để tạo thực đơn.');
      return;
    }

    setGenerating(true);
    setStatusMsg('Đang kiểm tra ràng buộc và gọi Nutrition Recommendation Engine...');

    try {
      const excludedKeywords = [
        ...prefs.allergies,
        ...extraExcluded
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
      ];

      const mealsResult: DailyMealPlan['meals'] = {};
      const activePref =
        diet !== 'normal'
          ? diet
          : prefs.comorbidities.some((c) => c.toLowerCase().includes('hypertension'))
            ? 'low_sodium'
            : null;

      for (const mtype of selectedMeals) {
        const res = await nutritionBackendApi.recommendMeal({
          user_id: user.id,
          meal_type: mtype,
          dietary_preference: activePref,
          excluded_keywords: excludedKeywords.length > 0 ? excludedKeywords : null,
        });
        mealsResult[mtype] = res;
      }

      const plan: DailyMealPlan = {
        date,
        generated_at: new Date().toISOString(),
        meals: mealsResult,
        status: 'active',
        applied_preference: activePref || 'Cân bằng ĐTĐ',
        applied_goal: goal,
        missing_fields: missingFields,
      };
      mealPlanStorage.save(user.id, plan);
      navigate('/nutrition/daily');
    } catch (err) {
      setAbstentionError(
        err instanceof Error
          ? err.message
          : 'Không thể tạo thực đơn đáp ứng các ràng buộc hiện tại.'
      );
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
          level={hasCKD ? 'critical' : 'error'}
          title="Engine tạm dừng / từ chối tạo thực đơn"
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
          {abstentionError}
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
              onChange={(e) => setGoal(e.target.value as 'weight_loss' | 'maintenance')}
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
            <StatusBadge tone={missingFields.length === 0 ? 'success' : 'warning'}>
              {missingFields.length === 0 ? 'Đủ thông tin' : `Thiếu ${missingFields.length} trường`}
            </StatusBadge>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 13.5 }}>
            <div>Ngày sinh: <strong>{profile?.date_of_birth || 'Chưa có'}</strong></div>
            <div>Giới tính: <strong>{profile?.sex || 'Chưa có'}</strong></div>
            <div>Chiều cao: <strong>{profile?.height_cm ? `${profile.height_cm} cm` : 'Chưa có'}</strong></div>
            <div>Cân nặng: <strong>{profile?.weight_kg ? `${profile.weight_kg} kg` : 'Chưa có'}</strong></div>
            <div>Mức vận động: <strong>{profile?.activity_level || 'Chưa có'}</strong></div>
            <div>Mục tiêu: <strong>{goal === 'weight_loss' ? 'Giảm cân' : 'Duy trì'}</strong></div>
            <div>Chế độ ăn: <strong>{diet}</strong></div>
            <div>
              Dị ứng:{' '}
              <strong>{prefs.allergies.length > 0 ? prefs.allergies.join(', ') : 'Không'}</strong>
            </div>
            <div>
              Bệnh lý:{' '}
              <strong>{prefs.comorbidities.join(', ')}</strong>
            </div>
          </div>

          {hasCKD && (
            <WarningCard level="critical" title="Giới hạn bệnh thận (CKD)">
              Không thể tạo thực đơn tự động khi có CKD.
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
