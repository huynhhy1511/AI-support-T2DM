export interface User {
  id: string;
  email: string;
  full_name: string;
  consent_accepted_at?: string | null;
}

export interface RegisterPayload {
  full_name: string;
  email: string;
  password: string;
  consent_accepted: boolean;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export class ApiError extends Error {
  status: number;
  detail?: unknown;

  constructor(message: string, status: number, detail?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

const TOKEN_STORAGE_KEY = 'access_token';
const BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1'
).replace(/\/+$/, '');

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function isValidEmail(email: string): boolean {
  return EMAIL_REGEX.test(email.trim());
}

function translateHttpError(status: number, endpoint: string, detail?: unknown): string {
  const detailText =
    typeof detail === 'string'
      ? detail
      : Array.isArray(detail) && detail.length > 0 && typeof detail[0]?.msg === 'string'
        ? detail[0].msg
        : '';

  switch (status) {
    case 400:
      return detailText
        ? `Yêu cầu không hợp lệ: ${detailText}`
        : 'Dữ liệu gửi lên không hợp lệ. Vui lòng kiểm tra lại.';
    case 401:
      if (endpoint.includes('/auth/login')) {
        return 'Email hoặc mật khẩu không chính xác. Vui lòng thử lại.';
      }
      return 'Phiên đăng nhập đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại.';
    case 403:
      return 'Bạn không có quyền truy cập vào tài nguyên này.';
    case 409:
      return 'Email này đã được đăng ký. Vui lòng sử dụng email khác hoặc đăng nhập.';
    case 422: {
      const lowerDetail = `${detailText} ${JSON.stringify(detail ?? '')}`.toLowerCase();
      if (lowerDetail.includes('match pattern') || lowerDetail.includes('email')) {
        return 'Địa chỉ email không hợp lệ. Vui lòng kiểm tra lại.';
      }
      return detailText
        ? `Thông tin chưa đúng định dạng (${detailText}). Vui lòng kiểm tra lại.`
        : 'Thông tin nhập vào chưa đúng định dạng. Vui lòng kiểm tra lại các trường.';
    }
    default:
      if (status >= 500) {
        return 'Hệ thống đang gặp sự cố tạm thời. Vui lòng thử lại sau ít phút.';
      }
      return 'Đã có lỗi xảy ra khi kết nối máy chủ. Vui lòng thử lại.';
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getStoredToken();
  const headers = new Headers(options.headers);

  if (!headers.has('Content-Type') && options.body) {
    headers.set('Content-Type', 'application/json');
  }

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });
  } catch {
    throw new ApiError(
      'Không thể kết nối tới máy chủ. Vui lòng kiểm tra kết nối mạng hoặc trạng thái backend.',
      0
    );
  }

  const contentType = response.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');
  const data = isJson ? await response.json().catch(() => null) : null;

  if (!response.ok) {
    const message = translateHttpError(response.status, endpoint, data?.detail);
    throw new ApiError(message, response.status, data?.detail);
  }

  return data as T;
}

export const authApi = {
  register(payload: RegisterPayload): Promise<User> {
    return request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  login(payload: LoginPayload): Promise<TokenResponse> {
    return request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  me(): Promise<User> {
    return request<User>('/auth/me', {
      method: 'GET',
    });
  },
};
