# Backend - AI-support-T2DM

Nền tảng backend cho ứng dụng AI hỗ trợ tự quản lý đái tháo đường type 2.

## 1. Công nghệ sử dụng
- Python 3.13+
- FastAPI
- SQLAlchemy 2.x
- PostgreSQL (driver `psycopg` v3)
- Alembic
- Pydantic v2 & `pydantic-settings`
- Uvicorn
- Pytest

---

## 2. Hướng dẫn thiết lập & chạy Backend

### 1. Kích hoạt Virtual Environment (Windows PowerShell)
Từ thư mục `backend`:
```powershell
.venv\Scripts\activate
```

*(Nếu chưa có virtual environment, khởi tạo bằng lệnh: `python -m venv .venv`)*

### 2. Cài đặt Dependency
```powershell
python -m pip install -r requirements.txt
```

### 3. Tạo Database PostgreSQL
Đảm bảo dịch vụ PostgreSQL đang chạy, kết nối bằng `psql` hoặc pgAdmin và tạo database:
```sql
CREATE DATABASE diabetes_ai_dev;
```

### 4. Cấu hình biến môi trường (.env)
Sao chép file `.env.example` thành `.env`:
```powershell
Copy-Item .env.example .env
```
Mở file `.env` và cập nhật thông tin tài khoản PostgreSQL thực tế:
```env
APP_NAME=AI-support-T2DM
APP_ENV=development
DATABASE_URL=postgresql+psycopg://postgres:YOUR_ACTUAL_PASSWORD@localhost:5432/diabetes_ai_dev
SECRET_KEY=change-me
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

> **Lưu ý:** Tuyệt đối không commit file `.env` lên Git repository.

### 5. Chạy Alembic Migrations
- Kiểm tra migration hiện tại:
  ```powershell
  alembic current
  ```
- Kiểm tra tính đồng bộ schema:
  ```powershell
  alembic check
  ```
- Nâng cấp database lên revision mới nhất:
  ```powershell
  alembic upgrade head
  ```

### 6. Khởi chạy Server
Chạy máy chủ phát triển với Uvicorn:
```powershell
uvicorn app.main:app --reload
```

Server sẽ lắng nghe tại: `http://127.0.0.1:8000`

### 7. Truy cập Swagger UI & API
- **Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check Endpoint**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
  - Khi database kết nối thành công:
    ```json
    {
      "status": "ok",
      "service": "AI-support-T2DM",
      "database": "connected"
    }
    ```
  - Khi database chưa kết nối được (server không crash):
    ```json
    {
      "status": "ok",
      "service": "AI-support-T2DM",
      "database": "disconnected"
    }
    ```

### 8. Chạy Kiểm thử (Pytest)
```powershell
pytest -v
```

---

## 3. Cấu trúc thư mục Backend

```text
backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py           # Gom router API v1
│   │       └── health.py             # Endpoint GET /api/v1/health (có check DB)
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py                 # Cấu hình Settings bằng pydantic-settings
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py                   # SQLAlchemy 2.x DeclarativeBase
│   │   └── session.py                # Engine, SessionLocal, get_db dependency
│   ├── models/
│   │   └── __init__.py               # Nơi đăng ký các ORM models
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── health.py                 # Pydantic schema cho HealthCheckResponse
│   ├── services/
│   │   ├── __init__.py
│   │   └── database.py               # Utility kiểm tra kết nối DB (SELECT 1)
│   └── main.py                       # Khởi tạo FastAPI app, lifespan, error handlers
├── tests/
│   ├── __init__.py
│   └── test_health.py                # Test endpoint GET /api/v1/health và root
├── alembic/
│   ├── versions/
│   │   └── .gitkeep
│   ├── env.py                        # Liên kết Base.metadata & Settings.database_url
│   └── script.py.mako                # Template migration của Alembic
├── alembic.ini                       # Cấu hình Alembic CLI
├── requirements.txt                  # Danh sách dependencies
├── .env                              # Biến môi trường local (chứa placeholder, gitignored)
├── .env.example                      # Biến môi trường mẫu
├── .gitignore                        # Quy tắc bỏ qua file tạm, venv, cache
└── README.md                         # Hướng dẫn chi tiết thiết lập & chạy backend
```
