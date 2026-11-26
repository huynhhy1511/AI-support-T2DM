import { useState, type FormEvent } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { Activity, AlertCircle, CheckCircle2, Lock, Mail } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { ApiError, isValidEmail } from '../services/api';

interface LocationState {
  registeredMessage?: string;
  from?: { pathname?: string };
}

export function LoginPage() {
  const { login, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const state = (location.state as LocationState | null) ?? null;

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (!isLoading && isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!email.trim() || !password) {
      setError('Vui lòng nhập đầy đủ email và mật khẩu.');
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

    setSubmitting(true);
    try {
      await login({
        email: email.trim(),
        password,
      });
      const target = state?.from?.pathname || '/dashboard';
      navigate(target, { replace: true });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Đăng nhập thất bại. Vui lòng thử lại.');
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

        <h2 className="auth-heading">Đăng nhập</h2>
        <p className="auth-subheading">
          Chào mừng bạn quay trở lại. Đăng nhập để xem bảng điều khiển sức khỏe.
        </p>

        {state?.registeredMessage && !error && (
          <div className="alert alert-success" role="status">
            <CheckCircle2 size={18} style={{ flexShrink: 0, marginTop: 2 }} />
            <span>{state.registeredMessage}</span>
          </div>
        )}

        {error && (
          <div className="alert alert-error" role="alert">
            <AlertCircle size={18} style={{ flexShrink: 0, marginTop: 2 }} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label className="form-label" htmlFor="login_email">
              Email
            </label>
            <div className="input-wrapper">
              <Mail size={17} className="input-icon" />
              <input
                id="login_email"
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
            <label className="form-label" htmlFor="login_password">
              Mật khẩu
            </label>
            <div className="input-wrapper">
              <Lock size={17} className="input-icon" />
              <input
                id="login_password"
                type="password"
                className="form-input"
                placeholder="Nhập mật khẩu của bạn"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>
          </div>

          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Đang đăng nhập...' : 'Đăng nhập'}
          </button>
        </form>

        <div className="auth-footer">
          Chưa có tài khoản? <Link to="/register">Đăng ký ngay</Link>
        </div>
      </div>
    </div>
  );
}
