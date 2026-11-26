import { useState, type FormEvent } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Lock,
  Mail,
  User as UserIcon,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { ApiError, isValidEmail } from '../services/api';

export function RegisterPage() {
  const { register, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [consentAccepted, setConsentAccepted] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (!isLoading && isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSuccessMessage(null);

    if (!fullName.trim()) {
      setError('Vui lòng nhập họ và tên.');
      return;
    }

    if (!isValidEmail(email)) {
      setError('Email không đúng định dạng (ví dụ: ten@gmail.com).');
      return;
    }

    if (password.length < 8) {
      setError('Mật khẩu cần có ít nhất 8 ký tự.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Mật khẩu xác nhận không khớp. Vui lòng kiểm tra lại.');
      return;
    }

    if (!consentAccepted) {
      setError('Bạn cần đồng ý điều khoản lưu trữ dữ liệu sức khỏe để đăng ký.');
      return;
    }

    setSubmitting(true);
    try {
      await register({
        full_name: fullName.trim(),
        email: email.trim(),
        password,
        consent_accepted: true,
      });

      const msg = 'Đăng ký tài khoản thành công! Đang chuyển sang trang đăng nhập...';
      setSuccessMessage(msg);
      setTimeout(() => {
        navigate('/login', {
          replace: true,
          state: { registeredMessage: 'Đăng ký thành công! Vui lòng đăng nhập để tiếp tục.' },
        });
      }, 900);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Đã xảy ra lỗi không mong muốn. Vui lòng thử lại.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="brand-header">
          <div className="brand-icon">
            <Activity size={24} />
          </div>
          <div>
            <h1 className="brand-title">DiaCare AI</h1>
            <p className="brand-subtitle">Hỗ trợ tự quản lý Đái tháo đường Type 2</p>
          </div>
        </div>

        <h2 className="auth-heading">Tạo tài khoản mới</h2>
        <p className="auth-subheading">
          Theo dõi đường huyết và nhận gợi ý dinh dưỡng cá nhân hóa an toàn.
        </p>

        {error && (
          <div className="alert alert-error" role="alert">
            <AlertCircle size={18} style={{ flexShrink: 0, marginTop: 2 }} />
            <span>{error}</span>
          </div>
        )}

        {successMessage && (
          <div className="alert alert-success" role="status">
            <CheckCircle2 size={18} style={{ flexShrink: 0, marginTop: 2 }} />
            <span>{successMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label className="form-label" htmlFor="full_name">
              Họ và tên
            </label>
            <div className="input-wrapper">
              <UserIcon size={17} className="input-icon" />
              <input
                id="full_name"
                type="text"
                className="form-input"
                placeholder="Nguyễn Văn An"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                autoComplete="name"
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="email">
              Email
            </label>
            <div className="input-wrapper">
              <Mail size={17} className="input-icon" />
              <input
                id="email"
                type="email"
                className="form-input"
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">
              Mật khẩu
            </label>
            <div className="input-wrapper">
              <Lock size={17} className="input-icon" />
              <input
                id="password"
                type="password"
                className="form-input"
                placeholder="Tối thiểu 8 ký tự"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={8}
                required
                autoComplete="new-password"
              />
            </div>
            <p className="form-hint">Mật khẩu cần có ít nhất 8 ký tự.</p>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="confirm_password">
              Xác nhận mật khẩu
            </label>
            <div className="input-wrapper">
              <Lock size={17} className="input-icon" />
              <input
                id="confirm_password"
                type="password"
                className="form-input"
                placeholder="Nhập lại mật khẩu"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                minLength={8}
                required
                autoComplete="new-password"
              />
            </div>
          </div>

          <label className="consent-box">
            <input
              type="checkbox"
              checked={consentAccepted}
              onChange={(e) => setConsentAccepted(e.target.checked)}
            />
            <span className="consent-text">
              Tôi đồng ý cho phép hệ thống lưu trữ và xử lý dữ liệu sức khỏe cá nhân
              (chỉ số đường huyết, dị ứng, chế độ ăn) nhằm phục vụ việc hỗ trợ tự
              quản lý bệnh Đái tháo đường Type 2.
            </span>
          </label>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={!consentAccepted || submitting}
          >
            {submitting ? 'Đang xử lý...' : 'Đăng ký tài khoản'}
          </button>
        </form>

        <div className="auth-footer">
          Đã có tài khoản? <Link to="/login">Đăng nhập ngay</Link>
        </div>
      </div>
    </div>
  );
}
