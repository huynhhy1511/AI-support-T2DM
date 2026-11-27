import { useEffect, useState, type FormEvent } from 'react';
import { Plus, Save, X } from 'lucide-react';
import { AppLayout } from '../../components/layout/AppLayout';
import { useAuth } from '../../context/AuthContext';
import { PrimaryButton, SecondaryButton } from '../../components/ui/Buttons';
import { WarningCard } from '../../components/ui/Cards';
import { FormField } from '../../components/ui/FormControls';
import { LoadingSkeleton } from '../../components/ui/Feedback';
import { PageHeader } from '../../components/ui/NavigationUI';
import { StatusBadge } from '../../components/ui/Badges';
import {
  healthProfileApi,
  localPrefsAdapter,
  weightHistoryStorage,
} from '../../services/nutritionApi';
import type { ActivityLevelType, HealthProfile, SexType } from '../../types/nutrition';

const COMORBIDITY_OPTIONS = [
  { id: 'Type 2 Diabetes', label: 'Đái tháo đường Type 2' },
  { id: 'Hypertension', label: 'Tăng huyết áp' },
  { id: 'CKD', label: 'Bệnh thận mạn (CKD)' },
  { id: 'Dyslipidemia', label: 'Rối loạn mỡ máu' },
];

const DIET_OPTIONS = [
  { value: 'normal', label: 'Bình thường (Cân bằng ĐTĐ)' },
  { value: 'vegetarian', label: 'Ăn chay (Có trứng/sữa)' },
  { value: 'vegan', label: 'Thuần chay (Không đạm động vật)' },
  { value: 'low_carb', label: 'Giảm tinh bột (Low Carb)' },
  { value: 'low_sodium', label: 'Ít muối (Low Sodium)' },
];

export function NutritionProfilePage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasProfile, setHasProfile] = useState(false);

  const [dob, setDob] = useState('');
  const [sex, setSex] = useState<SexType | ''>('');
  const [heightCm, setHeightCm] = useState('');
  const [weightKg, setWeightKg] = useState('');
  const [activityLevel, setActivityLevel] = useState<ActivityLevelType | ''>('');
  const [dietaryPreference, setDietaryPreference] = useState('normal');
  const [nutritionGoal, setNutritionGoal] = useState<'weight_loss' | 'maintenance'>('maintenance');
  const [comorbidities, setComorbidities] = useState<string[]>(['Type 2 Diabetes']);
  const [allergies, setAllergies] = useState<string[]>([]);
  const [newAllergy, setNewAllergy] = useState('');
  const [weightUpdatedAt, setWeightUpdatedAt] = useState<string>('');

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; msg: string } | null>(null);

  useEffect(() => {
    if (!user) return;
    let active = true;
    (async () => {
      setLoading(true);
      try {
        const hp: HealthProfile = await healthProfileApi.getByUser(user.id);
        if (!active) return;
        setHasProfile(true);
        setDob(hp.date_of_birth || '');
        setSex(hp.sex || '');
        setHeightCm(hp.height_cm ? String(hp.height_cm) : '');
        setWeightKg(hp.weight_kg ? String(hp.weight_kg) : '');
        setActivityLevel(hp.activity_level || '');
        setDietaryPreference(hp.dietary_preference || 'normal');
        setWeightUpdatedAt(hp.updated_at ? hp.updated_at.slice(0, 10) : '');
      } catch {
        if (active) setHasProfile(false);
      } finally {
        if (active) {
          const prefs = localPrefsAdapter.get(user.id);
          setNutritionGoal(prefs.nutrition_goal);
          setComorbidities(prefs.comorbidities);
          setAllergies(prefs.allergies);
          if (prefs.weight_updated_at) setWeightUpdatedAt(prefs.weight_updated_at);
          setLoading(false);
        }
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
      const payload = {
        date_of_birth: dob || null,
        sex: (sex || null) as SexType | null,
        height_cm: hNum,
        weight_kg: wNum,
        diabetes_type: 'type2',
        activity_level: (activityLevel || null) as ActivityLevelType | null,
        dietary_preference: dietaryPreference === 'normal' ? null : dietaryPreference,
      };

      if (hasProfile) {
        await healthProfileApi.update(user.id, payload);
      } else {
        await healthProfileApi.create({ ...payload, user_id: user.id });
        setHasProfile(true);
      }

      const today = new Date().toISOString().slice(0, 10);
      localPrefsAdapter.save(user.id, {
        nutrition_goal: nutritionGoal,
        comorbidities,
        allergies,
        weight_updated_at: today,
      });
      weightHistoryStorage.addEntry(user.id, { date: today, weight_kg: wNum });
      setWeightUpdatedAt(today);
      setFeedback({ type: 'success', msg: 'Đã lưu hồ sơ dinh dưỡng cá nhân thành công.' });
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
        subtitle="Thông tin chuẩn hóa phục vụ tính nhu cầu năng lượng (Mifflin-St Jeor) và lọc an toàn thực phẩm"
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
                <input className="dc-input" value={user.full_name} disabled />
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

          {/* B. Thể trạng */}
          <section className="dc-card">
            <h2 style={{ fontSize: 17, marginBottom: 16 }}>B. Thể trạng & Chỉ số BMI</h2>
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
                  <strong>{computedBmi ?? 'Chưa đủ dữ liệu'}</strong>
                </div>
              </FormField>
              <FormField label="Ngày cập nhật cân nặng">
                <div className="dc-input" style={{ display: 'flex', alignItems: 'center', background: 'var(--dc-bg)' }}>
                  {weightUpdatedAt || 'Chưa cập nhật'}
                </div>
              </FormField>
            </div>
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
                </select>
              </FormField>
            </section>

            <section className="dc-card">
              <h2 style={{ fontSize: 17, marginBottom: 14 }}>D. Mục tiêu dinh dưỡng</h2>
              <FormField
                label="Mục tiêu chính"
                hint="Lưu cục bộ trên thiết bị để điều chỉnh ngưỡng năng lượng gợi ý"
              >
                <select
                  className="dc-select"
                  value={nutritionGoal}
                  onChange={(e) => setNutritionGoal(e.target.value as 'weight_loss' | 'maintenance')}
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
              Hệ thống kiểm tra bệnh đồng mắc để siết natri (tăng huyết áp) hoặc tạm dừng tạo thực đơn tự động (bệnh thận mạn CKD).
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
              <h2 style={{ fontSize: 17, marginBottom: 14 }}>F. Dị ứng thực phẩm</h2>
              <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                <input
                  className="dc-input"
                  value={newAllergy}
                  onChange={(e) => setNewAllergy(e.target.value)}
                  placeholder="Ví dụ: Hải sản, Đậu phộng, Trứng..."
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
