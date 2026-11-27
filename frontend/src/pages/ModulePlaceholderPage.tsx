import { useNavigate } from 'react-router-dom';
import { Wrench } from 'lucide-react';
import { AppLayout } from '../components/layout/AppLayout';
import { EmptyState } from '../components/ui/Feedback';
import { PageHeader } from '../components/ui/NavigationUI';

export function ModulePlaceholderPage({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  const navigate = useNavigate();

  return (
    <AppLayout breadcrumbs={[{ label: 'Diabetes Care', to: '/dashboard' }, { label: title }]}>
      <PageHeader title={title} subtitle={description} />
      <EmptyState
        icon={<Wrench size={24} />}
        title={`Phân hệ "${title}" đang được tích hợp`}
        description="Hiện tại giao diện đầy đủ đã hoàn thiện cho phân hệ Dinh dưỡng (9 trang). Bạn có thể chuyển sang phân hệ Dinh dưỡng để trải nghiệm."
        actionLabel="Mở phân hệ Dinh dưỡng"
        onAction={() => navigate('/nutrition')}
      />
    </AppLayout>
  );
}
