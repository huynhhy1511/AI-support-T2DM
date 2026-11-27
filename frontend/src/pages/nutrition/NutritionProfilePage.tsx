import { useEffect, useState, type FormEvent } from 'react';
import { Plus, Save, X } from 'lucide-react';
import { AppLayout } from '../../components/layout/AppLayout';
import { useAuth } from '../../context/AuthContext';
import { PrimaryButton, SecondaryButton } from '../../components/ui/Buttons';
import { StatCard, WarningCard } from '../../components/ui/Cards';
import { FormField } from '../../components/ui/FormControls';
import { LoadingSkeleton } from '../../components/ui/Feedback';
import { PageHeader } from '../../components/ui/NavigationUI';
import { StatusBadge } from '../../components/ui/Badges';
import { healthProfileApi } from '../../services/nutritionApi';
import type {
  ActivityLevelType,
  HealthProfile,
  NutritionGoalType,
  SexType,
} from '../../types/nutrition';

const COMORBIDITY_OPTIONS = [
  { id: 'type2_diabetes', label: 'Đái tháo đường Type 2' },
  { id: 'hypertension', label: 'Tăng huyết áp' },
  { id: 'ckd', label: 'Bệnh thận mạn (CKD)' },
  { id: 'dyslipidemia', label: 'Rối loạn mỡ máu' },
];

const STANDARD_ALLERGENS = [
  { code: 'shellfish', label: 'Hải sản có vỏ (Tôm, cua, mực)' },
  { code: 'fish', label: 'Cá' },
  { code: 'seafood', label: 'Hải sản chung' },
  { code: 'egg', label: 'Trứng' },
  { code: 'dairy', label: 'Sữa & chế phẩm sữa' },
  { code: 'soy', label: 'Đậu nành' },
  { code: 'peanut', label: 'Đậu phộng (lạc)' },
  { code: 'tree_nut', label: 'Hạt cây' },
  { code: 'gluten', label: 'Gluten' },
  { code: 'sesame', label: 'Mè (vừng)' },
];

const DIET_OPTIONS = [
  { value: 'normal', label: 'Bình thường (Cân bằng ĐTĐ)' },
  { value: 'vegetarian', label: 'Ăn chay (Có trứng/sữa)' },
  { value: 'vegan', label: 'Thuần chay (Không đạm động vật)' },
  { value: 'low_carb', label: 'Giảm tinh bột (Low Carb)' },
  { value: 'low_sodium', label: 'Ít muối (Low Sodium)' },
];

function normalizeComorbidityId(raw: string): string {
  const lower = raw.toLowerCase().trim();
  if (lower.includes('ckd') || lower.includes('bệnh thận')) return 'ckd';
  if (lower.includes('hypertension') || lower.includes('tăng huyết áp')) return 'hypertension';
  if (lower.includes('dyslipidemia') || lower.includes('mỡ máu')) return 'dyslipidemia';
  if (lower.includes('diabetes') || lower.includes('đái tháo đường')) return 'type2_diabetes';
  return lower;
}

export function NutritionProfilePage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [dob, setDob] = useState('');
  const [sex, setSex] = useState<SexType | ''>('');
  const [heightCm, setHeightCm] = useState('');
  const [weightKg, setWeightKg] = useState('');
  const [activityLevel, setActivityLevel] = useState<ActivityLevelType | ''>('');
  const [dietaryPreference, setDietaryPreference] = useState('normal');
  const [nutritionGoal, setNutritionGoal] = useState<NutritionGoalType>('maintenance');
  const [comorbidities, setComorbidities] = useState<string[]>(['type2_diabetes']);
  const [allergies, setAllergies] = useState<string[]>([]);
  const [newAllergy, setNewAllergy] = useState('');
  const [weightUpdatedAt, setWeightUpdatedAt] = useState<string>('');
  const [savedProfile, setSavedProfile] = useState<HealthProfile | null>(null);

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);

  useEffect(() => {
    if (!user) return;
    let active = true;
    (async () => {
      setLoading(true);
      try {
        const hp: HealthProfile = await healthProfileApi.getMe();
        if (!active) return;
        setSavedProfile(hp);
        setDob(hp.date_of_birth || '');
        setSex(hp.sex || '');
        setHeightCm(hp.height_cm != null ? String(hp.height_cm) : '');
        setWeightKg(hp.weight_kg != null ? String(hp.weight_kg) : '');
        setActivityLevel(hp.activity_level || '');
        setDietaryPreference(hp.dietary_preference || 'normal');
        setNutritionGoal(hp.nutrition_goal || 'maintenance');
        const normalizedComorb = (hp.comorbidities || []).map(normalizeComorbidityId);
        setComorbidities(normalizedComorb.length > 0 ? normalizedComorb : ['type2_diabetes']);
        setAllergies(hp.allergies || []);
        setWeightUpdatedAt(hp.updated_at ? hp.updated_at.slice(0, 10) : '');
      } catch {
        if (active) setSavedProfile(null);
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [user]);

  if (!user) return null;

  const hNum = Number(heightCm);
  const wNum = Number(weightKg);
  const computedBmi =
    hNum > 0 && wNum > 0 ? Number((wNum / ((hNum / 100) ** 2)).toFixed(2)) : null;

  const toggleComorbidity = (id: string) => {
    setComorbidities((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const toggleAllergy = (codeOrName: string) => {
    const lower = codeOrName.toLowerCase();
    setAllergies((prev) =>
      prev.some((a) => a.toLowerCase() === lower)
        ? prev.filter((a) => a.toLowerCase() !== lower)
        : [...prev, codeOrName]
    );
  };

  const addAllergy = () => {
    const clean = newAllergy.trim();
    if (!clean) return;
    if (!allergies.some((a) => a.toLowerCase() === clean.toLowerCase())) {
      setAllergies((prev) => [...prev, clean]);
    }
    setNewAllergy('');
  };

  const validate = (): boolean => {
    const nextErr: Record<string, string> = {};
    if (!dob) nextErr.dob = 'Vui lòng chọn ngày sinh.';
    if (!sex) nextErr.sex = 'Vui lòng chọn giới tính.';
    if (!heightCm || hNum <= 50 || hNum > 260) nextErr.heightCm = 'Chiều cao hợp lệ từ 50 đến 260 cm.';
    if (!weightKg || wNum <= 20 || wNum > 300) nextErr.weightKg = 'Cân nặng hợp lệ từ 20 đến 300 kg.';
    if (!activityLevel) nextErr.activityLevel = 'Vui lòng chọn mức độ vận động.';
    setErrors(nextErr);
    return Object.keys(nextErr).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setFeedback(null);
    if (!validate()) return;

    setSaving(true);
    try {
      const updated = await healthProfileApi.upsertMe({
        date_of_birth: dob || null,
        sex: (sex || null) as SexType | null,
        height_cm: hNum,
        weight_kg: wNum,
        diabetes_type: 'type2',
        activity_level: (activityLevel || null) as ActivityLevelType | null,
        dietary_preference: dietaryPreference === 'normal' ? null : dietaryPreference,
        nutrition_goal: nutritionGoal,
        comorbidities,
        allergies,
      });

      setSavedProfile(updated);
      setWeightUpdatedAt(updated.updated_at ? updated.updated_at.slice(0, 10) : '');
      setFeedback({
        type: 'success',
        msg: 'Đã lưu hồ sơ dinh dưỡng lên máy chủ và cập nhật mục tiêu năng lượng (Mifflin-St Jeor).',
      });
    } catch (err) {
      setFeedback({
        type: 'error',
        msg: err instanceof Error ? err.message : 'Không thể lưu hồ sơ. Vui lòng thử lại.',
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppLayout
      breadcrumbs={[
        { label: 'Diabetes Care', to: '/dashboard' },
        { label: 'Dinh dưỡng', to: '/nutrition' },
        { label: 'Hồ sơ dinh dưỡng' },
      ]}
    >
      <PageHeader
        title="Hồ sơ dinh dưỡng cá nhân"
        subtitle="Thông tin chuẩn hóa lưu trên PostgreSQL phục vụ tính nhu cầu năng lượng (Mifflin-St Jeor) và lọc an toàn thực phẩm"
      />

      {loading ? (
        <LoadingSkeleton rows={5} />
      ) : (
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {feedback && (
            <WarningCard
              level={feedback.type === 'success' ? 'success' : 'error'}
              title={feedback.type === 'success' ? 'Lưu thành công' : 'Có lỗi xảy ra'}
            >
              {feedback.msg}
            </WarningCard>
          )}

          {/* A. Thông tin cá nhân */}
          <section className="dc-card">
            <h2 style={{ fontSize: 17, marginBottom: 16 }}>A. Thông tin cá nhân</h2>
            <div className="dc-grid-3">
              <FormField label="Họ và tên">
                <input className="dc-input" value={user.full_name || ''} disabled />
              </FormField>
              <FormField label="Ngày sinh" required error={errors.dob}>
                <input
                  type="date"
                  className={`dc-input ${errors.dob ? 'error' : ''}`}
                  value={dob}
                  onChange={(e) => setDob(e.target.value)}
                />
              </FormField>
              <FormField label="Giới tính" required error={errors.sex}>
                <select
                  className={`dc-select ${errors.sex ? 'error' : ''}`}
                  value={sex}
                  onChange={(e) => setSex(e.target.value as SexType)}
                >
                  <option value="">-- Chọn giới tính --</option>
                  <option value="male">Nam</option>
                  <option value="female">Nữ</option>
                  <option value="other">Khác</option>
                </select>
              </FormField>
            </div>
          </section>

          {/* B. Thể trạng & Chỉ số năng lượng từ Backend */}
          <section className="dc-card">
            <h2 style={{ fontSize: 17, marginBottom: 16 }}>B. Thể trạng, BMI & Nhu cầu năng lượng</h2>
            <div className="dc-grid-4">
              <FormField label="Chiều cao (cm)" required error={errors.heightCm}>
                <input
                  type="number"
                  step="0.1"
                  className={`dc-input ${errors.heightCm ? 'error' : ''}`}
                  value={heightCm}
                  onChange={(e) => setHeightCm(e.target.value)}
                  placeholder="Ví dụ: 165"
                />
              </FormField>
              <FormField label="Cân nặng (kg)" required error={errors.weightKg}>
                <input
                  type="number"
                  step="0.1"
                  className={`dc-input ${errors.weightKg ? 'error' : ''}`}
                  value={weightKg}
                  onChange={(e) => setWeightKg(e.target.value)}
                  placeholder="Ví dụ: 62"
                />
              </FormField>
              <FormField label="BMI tính từ hồ sơ" hint="kg / m²">
                <div className="dc-input" style={{ display: 'flex', alignItems: 'center', background: 'var(--dc-bg)' }}>
                  <strong>{savedProfile?.bmi ?? computedBmi ?? 'Chưa đủ dữ liệu'}</strong>
                </div>
              </FormField>
              <FormField label="Ngày cập nhật hồ sơ">
                <div className="dc-input" style={{ display: 'flex', alignItems: 'center', background: 'var(--dc-bg)' }}>
                  {weightUpdatedAt || 'Chưa cập nhật'}
                </div>
              </FormField>
            </div>

            {savedProfile && (
              <div className="dc-grid-3" style={{ marginTop: 16 }}>
                <StatCard
                  label="BMR (Chuyển hóa cơ bản)"
                  value={savedProfile.bmr_kcal != null ? Math.round(savedProfile.bmr_kcal) : 'Chưa đủ dữ liệu'}
                  unit={savedProfile.bmr_kcal != null ? 'kcal/ngày' : undefined}
                  subtitle="Tính theo công thức Mifflin-St Jeor"
                />
                <StatCard
                  label="TDEE (Tổng tiêu hao)"
                  value={savedProfile.tdee_kcal != null ? Math.round(savedProfile.tdee_kcal) : 'Chưa đủ dữ liệu'}
                  unit={savedProfile.tdee_kcal != null ? 'kcal/ngày' : undefined}
                  subtitle="Đã nhân hệ số vận động"
                  tone="secondary"
                />
                <StatCard
                  label="Mục tiêu năng lượng (Target)"
                  value={
                    savedProfile.target_energy_kcal != null
                      ? Math.round(savedProfile.target_energy_kcal)
                      : 'Chưa đủ dữ liệu'
                  }
                  unit={savedProfile.target_energy_kcal != null ? 'kcal/ngày' : undefined}
                  subtitle={
                    savedProfile.nutrition_goal === 'weight_loss'
                      ? 'Mục tiêu giảm cân an toàn'
                      : 'Mục tiêu duy trì cân nặng'
                  }
                  tone="primary"
                />
              </div>
            )}
          </section>

          {/* C & D. Mức độ vận động & Mục tiêu */}
          <div className="dc-grid-2">
            <section className="dc-card">
              <h2 style={{ fontSize: 17, marginBottom: 14 }}>C. Mức độ vận động</h2>
              <FormField label="Cường độ sinh hoạt hằng ngày" required error={errors.activityLevel}>
                <select
                  className={`dc-select ${errors.activityLevel ? 'error' : ''}`}
                  value={activityLevel}
                  onChange={(e) => setActivityLevel(e.target.value as ActivityLevelType)}
                >
                  <option value="">-- Chọn mức vận động --</option>
                  <option value="sedentary">Ít vận động (Sedentary - làm việc văn phòng)</option>
                  <option value="light">Vận động nhẹ (Light - đi bộ 1–3 ngày/tuần)</option>
                  <option value="moderate">Vận động vừa (Moderate - tập 3–5 ngày/tuần)</option>
                  <option value="active">Vận động nhiều (Active - tập 6–7 ngày/tuần)</option>
                  <option value="very_active">Vận động rất nhiều (Very Active)</option>
                </select>
              </FormField>
            </section>

            <section className="dc-card">
              <h2 style={{ fontSize: 17, marginBottom: 14 }}>D. Mục tiêu dinh dưỡng</h2>
              <FormField
                label="Mục tiêu chính"
                hint="Lưu trên Backend để tự động tính target_energy_kcal"
              >
                <select
                  className="dc-select"
                  value={nutritionGoal}
                  onChange={(e) => setNutritionGoal(e.target.value as NutritionGoalType)}
                >
                  <option value="maintenance">Duy trì cân nặng & ổn định đường huyết</option>
                  <option value="weight_loss">Giảm cân an toàn (Weight loss)</option>
                </select>
              </FormField>
            </section>
          </div>

          {/* E. Bệnh lý */}
          <section className="dc-card">
            <h2 style={{ fontSize: 17, marginBottom: 8 }}>E. Bệnh lý & Bệnh đồng mắc</h2>
            <p style={{ fontSize: 13.5, color: 'var(--dc-text-secondary)', marginBottom: 14 }}>
              Hệ thống kiểm tra bệnh đồng mắc trên máy chủ để cảnh báo kiểm soát natri (tăng huyết áp) hoặc tạm dừng tạo thực đơn tự động (bệnh thận mạn CKD).
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
              {COMORBIDITY_OPTIONS.map((c) => {
                const checked = comorbidities.includes(c.id);
                return (
                  <label
                    key={c.id}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 8,
                      padding: '10px 14px',
                      borderRadius: 10,
                      border: `1px solid ${checked ? 'var(--dc-primary)' : 'var(--dc-border)'}`,
                      background: checked ? 'var(--dc-primary-soft)' : 'var(--dc-surface)',
                      cursor: 'pointer',
                      fontWeight: 500,
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleComorbidity(c.id)}
                    />
                    <span>{c.label}</span>
                  </label>
                );
              })}
            </div>
          </section>

          {/* F & G. Dị ứng & Chế độ ăn */}
          <div className="dc-grid-2">
            <section className="dc-card">
              <h2 style={{ fontSize: 17, marginBottom: 10 }}>F. Dị ứng thực phẩm</h2>
              <p style={{ fontSize: 12.5, color: 'var(--dc-text-secondary)', marginBottom: 12 }}>
                Chọn nhanh nhóm dị nguyên chuẩn hóa hoặc nhập thêm từ khóa riêng:
              </p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 12 }}>
                {STANDARD_ALLERGENS.map((item) => {
                  const selected = allergies.some((a) => a.toLowerCase() === item.code);
                  return (
                    <button
                      key={item.code}
                      type="button"
                      onClick={() => toggleAllergy(item.code)}
                      style={{
                        padding: '5px 10px',
                        borderRadius: 999,
                        fontSize: 12.5,
                        cursor: 'pointer',
                        border: `1px solid ${selected ? 'var(--dc-danger)' : 'var(--dc-border)'}`,
                        background: selected ? '#FEF2F2' : 'var(--dc-surface)',
                        color: selected ? 'var(--dc-danger)' : 'var(--dc-text-secondary)',
                        fontWeight: selected ? 600 : 400,
                      }}
                    >
                      {item.label}
                    </button>
                  );
                })}
              </div>

              <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                <input
                  className="dc-input"
                  value={newAllergy}
                  onChange={(e) => setNewAllergy(e.target.value)}
                  placeholder="Thêm dị ứng khác (vd: hành, nấm)..."
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      addAllergy();
                    }
                  }}
                />
                <SecondaryButton icon={<Plus size={16} />} onClick={addAllergy}>
                  Thêm
                </SecondaryButton>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {allergies.length === 0 ? (
                  <span style={{ fontSize: 13.5, color: 'var(--dc-text-secondary)' }}>
                    Chưa khai báo dị ứng thực phẩm nào.
                  </span>
                ) : (
                  allergies.map((a) => (
                    <StatusBadge key={a} tone="danger">
                      <span>{a}</span>
                      <button
                        type="button"
                        onClick={() => setAllergies((prev) => prev.filter((x) => x !== a))}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: 'inherit',
                          cursor: 'pointer',
                          padding: 0,
                          display: 'inline-flex',
                        }}
                        aria-label={`Xóa ${a}`}
                      >
                        <X size={13} />
                      </button>
                    </StatusBadge>
                  ))
                )}
              </div>
            </section>

            <section className="dc-card">
              <h2 style={{ fontSize: 17, marginBottom: 14 }}>G. Chế độ ăn ưu tiên</h2>
              <FormField label="Chọn chế độ ăn được Backend hỗ trợ">
                <select
                  className="dc-select"
                  value={dietaryPreference}
                  onChange={(e) => setDietaryPreference(e.target.value)}
                >
                  {DIET_OPTIONS.map((d) => (
                    <option key={d.value} value={d.value}>
                      {d.label}
                    </option>
                  ))}
                </select>
              </FormField>
            </section>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
            <SecondaryButton onClick={() => window.history.back()}>Hủy</SecondaryButton>
            <PrimaryButton type="submit" loading={saving} icon={<Save size={16} />}>
              Lưu hồ sơ
            </PrimaryButton>
          </div>
        </form>
      )}
    </AppLayout>
  );
}
