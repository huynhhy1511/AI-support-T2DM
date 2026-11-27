import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppLayout } from '../../components/layout/AppLayout';
import { useAuth } from '../../context/AuthContext';
import { PrimaryButton, SecondaryButton } from '../../components/ui/Buttons';
import { WarningCard } from '../../components/ui/Cards';
import { StatusBadge } from '../../components/ui/Badges';
import { PageHeader } from '../../components/ui/NavigationUI';
import {
  estimateReferenceDailyKcal,
  healthProfileApi,
  localPrefsAdapter,
} from '../../services/nutritionApi';
import type { HealthProfile, SafetyAlertItem } from '../../types/nutrition';

const SAMPLE_SCENARIOS: SafetyAlertItem[] = [
  {
    id: 's1',
    level: 'warning',
    code: 'missing_profile',
    title: '1. Hồ sơ dinh dưỡng chưa đầy đủ thông tin',
    cause: 'Thiếu một hoặc nhiều chỉ số: ngày sinh, giới tính, chiều cao, cân nặng, mức vận động.',
    details: ['Không thể áp dụng công thức Mifflin-St Jeor nếu thiếu dữ liệu nhân trắc học.'],
    action_guidance: 'Vui lòng bổ sung đầy đủ thông tin trong Hồ sơ dinh dưỡng để nhận gợi ý phù hợp.',
    action_label: 'Cập nhật hồ sơ ngay',
    action_route: '/nutrition/profile',
  },
  {
    id: 's2',
    level: 'critical',
    code: 'ckd_restriction',
    title: '2. Phát hiện bệnh thận mạn (CKD) — Giới hạn phạm vi tự động',
    cause: 'Người mắc đái tháo đường kèm bệnh thận mạn cần kiểm soát nghiêm ngặt protein, kali, photpho và natri.',
    details: [
      'Hệ thống không tự thiết lập ngưỡng protein, kali hay natri cho bệnh nhân CKD khi chưa có phác đồ chuyên khoa.',
    ],
    action_guidance: 'Cần tham khảo trực tiếp bác sĩ chuyên khoa thận hoặc chuyên gia dinh dưỡng lâm sàng.',
    action_label: 'Xem lại khai báo bệnh lý',
    action_route: '/nutrition/profile',
  },
  {
    id: 's3',
    level: 'error',
    code: 'allergy_conflict',
    title: '3. Xung đột dị ứng thực phẩm',
    cause: 'Món ăn hoặc thành phần được chọn trùng với danh sách dị ứng của người dùng.',
    details: ['Hệ thống chặn xác nhận thực đơn có chứa dị nguyên (tỷ lệ vi phạm cho phép = 0%).'],
    action_guidance: 'Sử dụng chức năng Thay món tương đương hoặc cập nhật lại danh sách nguyên liệu tránh.',
    action_label: 'Mở trang Tạo thực đơn',
    action_route: '/nutrition/generate',
  },
  {
    id: 's4',
    level: 'info',
    code: 'no_valid_plan',
    title: '4. Không tìm được tổ hợp thực đơn đáp ứng đồng thời mọi ràng buộc',
    cause: 'Kho thực phẩm hiện tại không còn món thỏa mãn cùng lúc toàn bộ điều kiện dị ứng và chế độ ăn.',
    details: ['Hệ thống thông báo rõ thay vì tự động trả về thực đơn không phù hợp.'],
    action_guidance: 'Kiểm tra lại danh sách từ khóa loại trừ hoặc liên hệ chuyên gia dinh dưỡng.',
    action_label: 'Điều chỉnh ràng buộc',
    action_route: '/nutrition/generate',
  },
  {
    id: 's5',
    level: 'warning',
    code: 'energy_out_of_range',
    title: '5. Mức năng lượng hoặc chỉ số BMI nằm ngoài ngưỡng tham khảo an toàn',
    cause: 'BMI < 18.5 (thiếu cân) hoặc >= 30, hoặc mục tiêu calo thấp hơn ngưỡng sàn (1.200 kcal nữ / 1.400 kcal nam).',
    details: ['Không áp dụng chế độ thâm hụt năng lượng giảm cân đối với người thiếu cân.'],
    action_guidance: 'Điều chỉnh mục tiêu sang Duy trì cân nặng và trao đổi với chuyên gia dinh dưỡng.',
    action_label: 'Điều chỉnh mục tiêu',
    action_route: '/nutrition/profile',
  },
];

export function SafetyAlertPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState<HealthProfile | null>(null);

  useEffect(() => {
    if (!user) return;
    healthProfileApi.getByUser(user.id).then(setProfile).catch(() => setProfile(null));
  }, [user]);

  if (!user) return null;
  const prefs = localPrefsAdapter.get(user.id);
  const hasCKD = prefs.comorbidities.some((c) => c.toLowerCase().includes('ckd'));
  const estKcal = estimateReferenceDailyKcal(profile, prefs.nutrition_goal);
  const bmi = profile?.bmi ?? null;

  const activeAlerts: SafetyAlertItem[] = [];
  if (!profile || estKcal === null) {
    activeAlerts.push(SAMPLE_SCENARIOS[0]);
  }
  if (hasCKD) {
    activeAlerts.push(SAMPLE_SCENARIOS[1]);
  }
  if (bmi !== null && (bmi < 18.5 || bmi >= 30)) {
    activeAlerts.push(SAMPLE_SCENARIOS[4]);
  }

  return (
    <AppLayout
      breadcrumbs={[
        { label: 'Diabetes Care', to: '/dashboard' },
        { label: 'Dinh dưỡng', to: '/nutrition' },
        { label: 'Cảnh báo an toàn' },
      ]}
    >
      <PageHeader
        title="Cảnh báo an toàn dinh dưỡng"
        subtitle="Kiểm soát các điều kiện từ chối (Abstention), giới hạn bệnh lý và xung đột dị ứng — Không thay thế chẩn đoán y khoa"
      />

      <section className="dc-card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
          <h2 style={{ fontSize: 17 }}>Trạng thái an toàn trên hồ sơ hiện tại của bạn</h2>
          <StatusBadge tone={activeAlerts.length === 0 ? 'success' : 'warning'}>
            {activeAlerts.length === 0 ? 'Không có cảnh báo đang kích hoạt' : `${activeAlerts.length} lưu ý cần xem xét`}
          </StatusBadge>
        </div>

        {activeAlerts.length === 0 ? (
          <WarningCard level="success" title="Hồ sơ hiện tại đủ điều kiện tham khảo thực đơn">
            Không ghi nhận bệnh thận mạn (CKD) hoặc thiếu dữ liệu nhân trắc học. Luôn kiểm tra kỹ dị ứng trước khi xác nhận bữa ăn.
          </WarningCard>
        ) : (
          activeAlerts.map((al) => (
            <WarningCard
              key={al.id}
              level={al.level}
              title={al.title}
              action={
                <PrimaryButton size="sm" onClick={() => navigate(al.action_route)}>
                  {al.action_label}
                </PrimaryButton>
              }
            >
              <p><strong>Nguyên nhân:</strong> {al.cause}</p>
              <p style={{ marginTop: 4 }}><strong>Hướng xử lý:</strong> {al.action_guidance}</p>
            </WarningCard>
          ))
        )}
      </section>

      <section className="dc-card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <h2 style={{ fontSize: 17 }}>5 trạng thái bảo vệ an toàn chuẩn của hệ thống</h2>
        <p style={{ fontSize: 13.5, color: 'var(--dc-text-secondary)' }}>
          Phân biệt rõ mức độ Thông tin (Info), Cảnh báo (Warning), Lỗi ràng buộc (Error) và Giới hạn chuyên môn (Critical) — không dùng màu đỏ cho mọi tình huống.
        </p>

        {SAMPLE_SCENARIOS.map((sc) => (
          <WarningCard
            key={sc.id}
            level={sc.level}
            title={sc.title}
            action={
              <SecondaryButton size="sm" onClick={() => navigate(sc.action_route)}>
                {sc.action_label}
              </SecondaryButton>
            }
          >
            <div><strong>Nguyên nhân:</strong> {sc.cause}</div>
            <div style={{ marginTop: 4 }}><strong>Chi tiết:</strong> {sc.details.join(' ')}</div>
            <div style={{ marginTop: 4 }}><strong>Hướng xử lý:</strong> {sc.action_guidance}</div>
          </WarningCard>
        ))}
      </section>
    </AppLayout>
  );
}
