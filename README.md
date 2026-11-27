# AI-support-T2DM (Diabetes Care)

Ứng dụng AI hỗ trợ tự quản lý đái tháo đường type 2 thông qua:
- **AI Knowledge Consultation:** Tư vấn tri thức y khoa dựa trên RAG + FAISS + Gemini API.
- **Nutrition Recommendation:** Gợi ý thực đơn cá nhân hóa theo Đĩa ăn Đái tháo đường (Plate Method), kiểm soát dị ứng và natri.
- **Exercise Pose Monitoring:** Giám sát tư thế tập luyện bằng AI Computer Vision (MediaPipe Pose).

## 1. Cấu trúc thư mục

- `backend/` — FastAPI RESTful API, SQLAlchemy 2.x, Alembic migrations, JWT Auth, Nutrition Engine & Pytest.
- `frontend/` — React 19 + Vite 6 + TypeScript, Unified Healthcare Design System (`Diabetes Care`) gồm Auth và 9 màn hình phân hệ Dinh dưỡng.
- `Docs/`, `ai/`, `computer-vision/`, `database/`, `dataset/`, `tests/` — Dữ liệu và các phân hệ nghiên cứu.
- `PROGRESS_OVERVIEW.md` — Tài liệu theo dõi tiến độ tổng thể của đề tài.

---

## 2. Hướng dẫn cài đặt và chạy dự án (Windows / PowerShell)

### Bước 1: Chuẩn bị Database PostgreSQL
1. Đảm bảo PostgreSQL Server đang chạy (mặc định cổng `5432`) và đã tạo database `diabetes_ai_dev`.
2. Tạo file cấu hình môi trường cho Backend:
   ```powershell
   Copy-Item backend\.env.example backend\.env
   ```
   Mở `backend\.env` và sửa `YOUR_PASSWORD` thành mật khẩu PostgreSQL của bạn (ví dụ: `1511`):
   ```env
   DATABASE_URL=postgresql+psycopg://postgres:1511@localhost:5432/diabetes_ai_dev
   ```

### Bước 2: Chạy Backend (FastAPI)
Mở Terminal 1 tại thư mục gốc `D:\NCKH-2026-2027`:
```powershell
# 1. Cài thư viện (nếu chưa cài)
.\.venv\Scripts\pip.exe install -r backend\requirements.txt

# 2. Chạy Alembic migration tạo bảng
cd backend
..\.venv\Scripts\alembic.exe upgrade head

# 3. Khởi động FastAPI server tại http://127.0.0.1:8000
..\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```
- Tài liệu API tự động (Swagger UI): `http://127.0.0.1:8000/docs`

### Bước 3: Chạy Frontend (React + Vite)
Mở Terminal 2 tại thư mục gốc `D:\NCKH-2026-2027`:
```powershell
cd frontend
npm install
Copy-Item .env.example .env -ErrorAction SilentlyContinue
npm run dev
```
- Truy cập ứng dụng web tại địa chỉ hiển thị trên terminal (mặc định `http://localhost:5173`).
- Đăng ký tài khoản mới hoặc đăng nhập, sau đó vào mục **Dinh dưỡng** trên Sidebar để sử dụng 9 trang của module Nutrition Recommendation.

### Bước 4: Chạy kiểm thử (Tests)
- **Kiểm tra Backend (`pytest`):**
  ```powershell
  cd backend
  ..\.venv\Scripts\pytest.exe
  ```
- **Kiểm tra Build Frontend (TypeScript + Vite):**
  ```powershell
  cd frontend
  npm run build
  ```

---

## 3. Lưu ý các nhánh Git hiện tại
- `main`: Chứa Backend FastAPI (JWT Auth, CORS, Nutrition Engine) + Frontend React (9 màn hình Nutrition Recommendation) + `PROGRESS_OVERVIEW.md`.
- `feature/ai-consultation`: Chứa toàn bộ phân hệ AI/RAG (`rag_chain.py`, `retriever.py`, `safety.py`, `nutrition_rag.py`), Knowledge Base `K001`–`K029`, Food DB 35 món, benchmark 30 hồ sơ giả lập và 29 scientific agent skills (`.agents/skills/`).
