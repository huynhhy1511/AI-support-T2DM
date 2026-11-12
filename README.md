# AI-support-T2DM

Ứng dụng AI hỗ trợ tự quản lý đái tháo đường type 2 thông qua:
- Tư vấn tri thức
- Gợi ý dinh dưỡng
- Giám sát tư thế tập luyện

Thư mục:
- Docs
- backend
- frontend
- ai
- computer-vision
- database
- dataset
- tests

| Nội dung | Kết quả kiểm tra thực tế | Bằng chứng mã nguồn / Ghi chú |
| --- | --- | --- |
| Tên project | `AI-support-T2DM` | Khai báo trong config.py và main.py |
| Backend framework | FastAPI `0.142.2` | Khai báo trong requirements.txt |
| Ngôn ngữ lập trình | Python `3.13.1` (64-bit Windows) | Môi trường `.venv` tại `backend/.venv` |
| Database | PostgreSQL 18 (Cơ sở dữ liệu `diabetes_ai_dev`) | Cấu hình qua biến `DATABASE_URL` trong config.py |
| ORM | SQLAlchemy `2.1.3` (Cú pháp SQLAlchemy 2.x `Mapped`, `mapped_column`) | Khai báo trong base.py và session.py |
| Database Driver | `psycopg` (v3 binary) | Khai báo `psycopg[binary]>=3.2.0` trong requirements.txt |
| Migration tool | Alembic `1.20.0` | Thư mục backend/alembic và file alembic.ini |
| Authentication | Chưa triển khai (NOT IMPLEMENTED) | Không tìm thấy module JWT, OAuth2 hay session trong mã nguồn. Có trường `secret_key` trong config.py nhưng chưa dùng. |
| API style | RESTful JSON API (FastAPI Router, OpenAPI 3.1) | Gom router tại backend/app/api/v1/__init__.py |
| Kiến trúc Backend | Phân tầng chuẩn (Layered Architecture): API →\\rightarrow→ Schemas →\\rightarrow→ Services/Engines →\\rightarrow→ Models →\\rightarrow→ DB | Tách biệt logic theo thư mục `api/`, `schemas/`, `services/`, `models/`, `db/` |
| Các thư viện quan trọng | `pydantic` (2.13.5), `pydantic-settings` (2.15.0), `uvicorn` (0.54.0), `pytest` (9.1.1), `httpx` (0.28.1) | requirements.txt |
| Trạng thái tổng thể | Core Backend & Module Dinh dưỡng (Giai đoạn 1 & 2) đã hoàn thiện và hoạt động ổn định; RAG và Computer Vision chưa triển khai | Toàn bộ 25 unit/API tests đang chạy đạt 100% PASSED |

backend/
├── alembic/                          # Cấu hình và lịch sử migrations của Alembic
│   ├── env.py                        # Cấu hình môi trường migration, liên kết Base.metadata
│   ├── script.py.mako                # Template sinh mã migration
│   └── versions/                     # Thư mục chứa các file migration
│       ├── 001_core_models.py        # Migration tạo bảng users, health_profiles, glucose_records
│       └── 002_nutrition_models.py   # Migration tạo bảng foods, meal_recommendations, meal_recommendation_items
├── app/                              # Toàn bộ mã nguồn ứng dụng chính
│   ├── main.py                       # Khởi tạo FastAPI app, lifespan, global exception handlers, endpoint "/"
│   ├── api/                          # Tầng điều phối API routes
│   │   ├── __init__.py
│   │   └── v1/                       # API phiên bản 1
│   │       ├── __init__.py           # Gom các router v1 (health, users, profiles, glucose, foods, nutrition)
│   │       ├── foods.py              # Endpoints CRUD dữ liệu thực phẩm & seed dữ liệu mẫu
│   │       ├── glucose_records.py    # Endpoints ghi nhận, xem lịch sử và thống kê đường huyết
│   │       ├── health.py             # Endpoint GET /api/v1/health (kiểm tra trạng thái app & database)
│   │       ├── health_profiles.py    # Endpoints quản lý hồ sơ sức khỏe bệnh nhân
│   │       ├── nutrition.py          # Endpoints gợi ý bữa ăn và tra cứu lịch sử gợi ý
│   │       └── users.py              # Endpoints quản lý tài khoản người dùng
│   ├── core/                         # Cấu hình toàn cục hệ thống
│   │   ├── __init__.py
│   │   └── config.py                 # Pydantic Settings đọc biến môi trường từ .env
│   ├── db/                           # Tầng kết nối Database
│   │   ├── __init__.py
│   │   ├── base.py                   # Khởi tạo SQLAlchemy DeclarativeBase
│   │   └── session.py                # Engine, SessionLocal, get_db dependency
│   ├── models/                       # Tầng thực thể ORM (SQLAlchemy 2.x Models)
│   │   ├── __init__.py               # Xuất các model
│   │   ├── food.py                   # Model bảng foods (thành phần dinh dưỡng, GI, GL)
│   │   ├── glucose_record.py         # Model bảng glucose_records (chỉ số đường huyết)
│   │   ├── health_profile.py         # Model bảng health_profiles (thông tin sức khỏe 1:1 với User)
│   │   ├── meal_recommendation.py    # Model bảng meal_recommendations (lưu snapshot gợi ý)
│   │   ├── meal_recommendation_item.py # Model bảng meal_recommendation_items (món ăn trong bữa gợi ý)
│   │   └── user.py                   # Model bảng users (tài khoản người dùng)
│   ├── schemas/                      # Tầng DTO / Validation Schemas (Pydantic v2)
│   │   ├── __init__.py
│   │   ├── food.py                   # Schemas FoodBase, FoodCreate, FoodUpdate, FoodResponse
│   │   ├── glucose_record.py         # Schemas GlucoseRecordCreate, Response, StatsResponse
│   │   ├── health.py                 # Schema HealthCheckResponse
│   │   ├── health_profile.py         # Schemas HealthProfileCreate, Update, Response (tính BMI)
│   │   ├── nutrition.py              # Schemas MealRecommendationRequest, Response, Plate items
│   │   └── user.py                   # Schemas UserCreate, UserUpdate, UserResponse
│   └── services/                     # Tầng nghiệp vụ xử lý logic (Business Logic Layer)
│       ├── __init__.py
│       ├── database.py               # Hàm kiểm tra kết nối DB (SELECT 1)
│       ├── food_service.py           # Nghiệp vụ thực phẩm, dataset mẫu chuẩn hóa khẩu phần
│       ├── glucose_service.py        # Nghiệp vụ ghi đo đường huyết, lọc và tính min/max/avg
│       ├── health_profile_service.py # Nghiệp vụ tạo và cập nhật hồ sơ sức khỏe
│       ├── nutrition_engine.py       # ConstraintEngine, ScoringEngine (GI, GL, xơ), MealComposer
│       ├── nutrition_service.py      # Điều phối gợi ý món ăn và lưu lịch sử snapshot
│       └── user_service.py           # Nghiệp vụ người dùng và đồng thuận y tế
├── tests/                            # Bộ kiểm thử tự động (Pytest)
│   ├── __init__.py
│   ├── test_foods_api.py             # Test API thực phẩm, seed data, validation lỗi
│   ├── test_glucose_records_api.py   # Test API đường huyết, lọc fasting, thống kê stats
│   ├── test_health.py                # Test endpoint health check và root endpoint
│   ├── test_health_profiles_api.py   # Test API hồ sơ sức khỏe, tự tính BMI, conflict 409
│   ├── test_models.py                # Test ORM relationship in-memory và persistence database
│   ├── test_nutrition_api.py         # Test API gợi ý món ăn, ăn chay, lưu lịch sử snapshot
│   ├── test_nutrition_engine.py      # Unit test độc lập cho ConstraintEngine & ScoringEngine
│   └── test_users_api.py             # Test API CRUD người dùng, duplicate email 409, phân trang
├── .env                              # Biến môi trường local (chứa thông tin kết nối DB)
├── .env.example                      # Biến môi trường mẫu
├── .gitignore                        # Quy tắc bỏ qua git (venv, cache, .env)
├── alembic.ini                       # Cấu hình kết nối cho Alembic CLI
├── README.md                         # Hướng dẫn thiết lập và chạy Backend
└── requirements.txt                  # Danh mục dependencies của dự án

| STT | Table Name | Các trường chính | Primary Key | Foreign Keys | Trạng thái thực tế trong DB |
| --- | --- | --- | --- | --- | --- |
| 1 | `alembic_version` | `version_num (VARCHAR(32))` | `version_num` | Không có | Đang áp dụng head: `002_nutrition_models` |
| 2 | `users` | `id (UUID)`, `email (VARCHAR(255))`, `display_name (VARCHAR(255))`, `consent_accepted_at (TIMESTAMPTZ)`, `created_at (TIMESTAMPTZ)` | `id` | Không có | Đã kích hoạt (Index Unique trên `email`) |
| 3 | `health_profiles` | `id (UUID)`, `user_id (UUID)`, `date_of_birth (DATE)`, `sex (VARCHAR(50))`, `height_cm (NUMERIC(5,2))`, `weight_kg (NUMERIC(5,2))`, `diabetes_type (VARCHAR(50))`, `diagnosis_year (INT)`, `activity_level (VARCHAR(100))`, `dietary_preference (VARCHAR(100))`, `updated_at (TIMESTAMPTZ)` | `id` | `user_id` →\\rightarrow→ `users(id)` (ON DELETE CASCADE) | Đã kích hoạt (Unique Constraint trên `user_id` đảm bảo quan hệ 1:1) |
| 4 | `glucose_records` | `id (UUID)`, `user_id (UUID)`, `measured_at (TIMESTAMPTZ)`, `glucose_value (NUMERIC(6,2))`, `unit (VARCHAR(20))`, `measurement_context (VARCHAR(50))`, `note (TEXT)`, `created_at (TIMESTAMPTZ)` | `id` | `user_id` →\\rightarrow→ `users(id)` (ON DELETE CASCADE) | Đã kích hoạt (Index trên `user_id`, 3 Check Constraints kiểm soát dữ liệu) |
| 5 | `foods` | `id (UUID)`, `name (VARCHAR(255))`, `category (VARCHAR(100))`, `serving_size_g (NUMERIC(7,2))`, `energy_kcal (NUMERIC(7,2))`, `carbohydrate_g (NUMERIC(7,2))`, `protein_g (NUMERIC(7,2))`, `fat_g (NUMERIC(7,2))`, `fiber_g (NUMERIC(7,2))`, `sugar_g (NUMERIC(7,2))`, `glycemic_index (NUMERIC(5,2))`, `glycemic_load (NUMERIC(5,2))`, `is_test_data (BOOLEAN)`, `source_name (VARCHAR(255))`, `source_url (VARCHAR(500))`, `created_at (TIMESTAMPTZ)`, `updated_at (TIMESTAMPTZ)` | `id` | Không có | Đã kích hoạt (Index trên `name`, `category`, 9 Check Constraints bảo đảm số liệu ≥0\\ge 0≥0) |
| 6 | `meal_recommendations` | `id (UUID)`, `user_id (UUID)`, `meal_type (VARCHAR(50))`, `algorithm_version (VARCHAR(50))`, `input_snapshot (JSONB)`, `recommendation_result (JSONB)`, `generated_at (TIMESTAMPTZ)`, `created_at (TIMESTAMPTZ)` | `id` | `user_id` →\\rightarrow→ `users(id)` (ON DELETE CASCADE) | Đã kích hoạt (Index trên `user_id`) |
| 7 | `meal_recommendation_items` | `id (UUID)`, `recommendation_id (UUID)`, `food_id (UUID)`, `serving_multiplier (NUMERIC(4,2))`, `calculated_energy_kcal (NUMERIC(7,2))`, `calculated_carbohydrate_g (NUMERIC(7,2))`, `calculated_protein_g (NUMERIC(7,2))`, `calculated_fat_g (NUMERIC(7,2))`, `calculated_fiber_g (NUMERIC(7,2))`, `score (NUMERIC(5,2))`, `reason (TEXT)` | `id` | - `recommendation_id` →\\rightarrow→ `meal_recommendations(id)` (ON DELETE CASCADE)<br>- `food_id` →\\rightarrow→ `foods(id)` (ON DELETE RESTRICT) | Đã kích hoạt (Index trên `recommendation_id` và `food_id`) |

| Nội dung | Kết quả kiểm tra thực tế |
| --- | --- |
| Database connection | Hoạt động tốt (`connected`). Đã kiểm chứng qua API `/api/v1/health` và SQLAlchemy pool. |
| ORM models | 6 models được định nghĩa chuẩn xác bằng SQLAlchemy 2.x trong thư mục app/models. |
| Migration scripts | 2 migration files hợp lệ: `001_core_models.py` và `002_nutrition_models.py`. Đồng bộ hoàn toàn với database head. |
| Foreign key constraints | Đầy đủ khóa ngoại; có cấu hình `ON DELETE CASCADE` cho thực thể con theo người dùng, và `ON DELETE RESTRICT` bảo vệ dữ liệu thực phẩm khi đang được dùng trong gợi ý. |
| Indexes | Đã đánh chỉ mục (Index) trên các cột thường xuyên tìm kiếm và join: `users.email` (unique), `glucose_records.user_id`, `foods.name`, `foods.category`, `meal_recommendations.user_id`, `meal_recommendation_items.recommendation_id`, `meal_recommendation_items.food_id`. |
| Check constraints | Ràng buộc chặt chẽ tại PostgreSQL: `glucose_value > 0`, `unit IN ('mmol/L', 'mg/dL')`, `context IN (...)`, `serving_size_g > 0`, `0 <= GI <= 150`, dinh dưỡng ≥0\\ge 0≥0. |
| Seed data / Sample data | Có sẵn bộ dữ liệu mẫu gồm 14 thực phẩm phổ biến cho bệnh nhân tiểu đường trong food_service.py được gắn nhãn `is_test_data: True`. |
| Database initialization | Khởi tạo bảng tự động thông qua lệnh chuẩn: `alembic upgrade head`. |

| STT | Method | Endpoint | Nhóm API | Chức năng | Request Schema | Response Schema | Trạng thái kiểm thử | File định nghĩa / Service |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `GET` | `/` | Root | Xem thông tin phiên bản backend | Không | `dict` | PASSED | main.py |
| 2 | `GET` | `/api/v1/health` | Health | Kiểm tra kết nối API & PostgreSQL | Không | `HealthCheckResponse` | PASSED | health.py / database.py |
| 3 | `POST` | `/api/v1/users` | Users | Đăng ký người dùng mới | `UserCreate` | `UserResponse` (201201201) | PASSED | users.py / user_service.py |
| 4 | `GET` | `/api/v1/users` | Users | Lấy danh sách người dùng phân trang | Query (`skip`, `limit`) | `List[UserResponse]` | PASSED | users.py / user_service.py |
| 5 | `GET` | `/api/v1/users/{user_id}` | Users | Xem thông tin chi tiết một người dùng | Path (`user_id`) | `UserResponse` | PASSED | users.py / user_service.py |
| 6 | `PUT` | `/api/v1/users/{user_id}` | Users | Cập nhật tên hiển thị, trạng thái consent | `UserUpdate` | `UserResponse` | PASSED | users.py / user_service.py |
| 7 | `DELETE` | `/api/v1/users/{user_id}` | Users | Xóa người dùng (cascade dữ liệu con) | Path (`user_id`) | `dict` (200200200) | PASSED | users.py / user_service.py |
| 8 | `POST` | `/api/v1/health-profiles` | Profiles | Tạo hồ sơ sức khỏe bệnh nhân | `HealthProfileCreate` | `HealthProfileResponse` (201201201) | PASSED | health_profiles.py / health_profile_service.py |
| 9 | `GET` | `/api/v1/health-profiles/user/{user_id}` | Profiles | Lấy hồ sơ sức khỏe và BMI tự động | Path (`user_id`) | `HealthProfileResponse` | PASSED | health_profiles.py / health_profile_service.py |
| 10 | `PUT` | `/api/v1/health-profiles/user/{user_id}` | Profiles | Cập nhật chỉ số (chiều cao, cân nặng...) | `HealthProfileUpdate` | `HealthProfileResponse` | PASSED | health_profiles.py / health_profile_service.py |
| 11 | `DELETE` | `/api/v1/health-profiles/user/{user_id}` | Profiles | Xóa hồ sơ sức khỏe | Path (`user_id`) | `dict` (200200200) | PASSED | health_profiles.py / health_profile_service.py |
| 12 | `POST` | `/api/v1/glucose-records` | Glucose | Thêm một bản ghi đo đường huyết | `GlucoseRecordCreate` | `GlucoseRecordResponse` (201201201) | PASSED | glucose_records.py / glucose_service.py |
| 13 | `GET` | `/api/v1/glucose-records/user/{user_id}` | Glucose | Danh sách lịch sử đo đường huyết (có filter) | Query (`start_time`, `context`...) | `List[GlucoseRecordResponse]` | PASSED | glucose_records.py / glucose_service.py |
| 14 | `GET` | `/api/v1/glucose-records/user/{user_id}/stats` | Glucose | Thống kê đường huyết (trung bình, min, max) | Query (`unit`) | `GlucoseStatsResponse` | PASSED | glucose_records.py / glucose_service.py |
| 15 | `GET` | `/api/v1/glucose-records/{record_id}` | Glucose | Xem chi tiết 1 lần đo đường huyết | Path (`record_id`) | `GlucoseRecordResponse` | PASSED | glucose_records.py / glucose_service.py |
| 16 | `PUT` | `/api/v1/glucose-records/{record_id}` | Glucose | Sửa giá trị/ngữ cảnh/ghi chú đo | `GlucoseRecordUpdate` | `GlucoseRecordResponse` | PASSED | glucose_records.py / glucose_service.py |
| 17 | `DELETE` | `/api/v1/glucose-records/{record_id}` | Glucose | Xóa 1 lần đo đường huyết | Path (`record_id`) | `dict` (200200200) | PASSED | glucose_records.py / glucose_service.py |
| 18 | `GET` | `/api/v1/foods` | Foods | Tra cứu từ điển thực phẩm (lọc/search) | Query (`category`, `search`...) | `List[FoodResponse]` | PASSED | foods.py / food_service.py |
| 19 | `POST` | `/api/v1/foods` | Foods | Thêm món ăn mới vào database | `FoodCreate` | `FoodResponse` (201201201) | PASSED | foods.py / food_service.py |
| 20 | `POST` | `/api/v1/nutrition/recommend` | Nutrition | Tạo thực đơn gợi ý theo Plate Method | `MealRecommendationRequest` | `MealRecommendationResponse` | PASSED | nutrition.py / nutrition_service.py |

| Nội dung kiểm tra | Trạng thái | File liên quan | Bằng chứng mã nguồn & Ghi chú |
| --- | --- | --- | --- |
| Food Model | ĐÃ CÓ | food.py | Đã map bảng `foods` bằng SQLAlchemy 2.x Mapped columns. |
| Food Categories | ĐÃ CÓ | food.py | 8 nhóm chuẩn: `staple`, `vegetables`, `protein`, `fruits`, `dairy`, `fat_oil`, `snack`, `beverage`. |
| Calories | ĐÃ CÓ | `energy_kcal` | Kiểu `Numeric(7,2)`, tính trên khẩu phần chuẩn `serving_size_g`. |
| Carbohydrates | ĐÃ CÓ | `carbohydrate_g` | Kiểm soát chặt chẽ làm đầu vào cho tính Glycemic Load. |
| Protein | ĐÃ CÓ | `protein_g` | Đánh giá đạm nạc trong thuật toán chấm điểm. |
| Fat | ĐÃ CÓ | `fat_g` | Đánh giá tổng chất béo trong mỗi khẩu phần. |
| Fiber (Chất xơ) | ĐÃ CÓ | `fiber_g` | Trường quan trọng cho tiểu đường (làm chậm hấp thu đường). |
| Sodium (Natri) | CHƯA CÓ | - | Bảng `foods` hiện chưa có cột natri (muối). Cần bổ sung nếu phát triển tính năng cho bệnh nhân tăng huyết áp kèm theo. |
| Saturated Fat (Chất béo bão hòa) | CHƯA CÓ | - | Hiện chỉ lưu tổng `fat_g`, chưa tách riêng chất béo bão hòa và không bão hòa. |
| Food Allergens (Dị ứng) | MỘT PHẦN | nutrition_engine.py | Chưa có cột dị ứng trong bảng thực phẩm; hiện lọc qua mảng từ khóa `excluded_keywords` người dùng gửi lên. |
| Data Sources | ĐÃ CÓ | `source_name`, `source_url` | Lưu rõ nguồn gốc trích dẫn (ví dụ: Viện Dinh Dưỡng, USDA). |
| Data Versioning | MỘT PHẦN | `created_at`, `updated_at` | Có dấu thời gian cập nhật bản ghi, chưa có hệ thống versioning snapshot riêng cho từng phiên bản dataset thực phẩm. |

1. Đã có Food Database chưa? \rightarrow ĐÃ CÓ
- Trạng thái: Bảng vật lý foods đã được tạo và kích hoạt trong PostgreSQL (diabetes_ai_dev) qua migration 002_nutrition_models.py.
- Mã nguồn: Model ORM food.py.
- Cấu trúc trường dữ liệu:
  - Định danh & phân loại: id (UUID), name (tên thực phẩm), category (8 nhóm: staple, vegetables, protein, fruits, dairy, fat_oil, snack, beverage).
  - Khẩu phần: serving_size_g (trọng lượng tính bằng gram của 1 khẩu phần chuẩn).
  - Nguồn gốc: source_name, source_url, cờ is_test_data (để phân định dữ liệu test và dữ liệu chính thức).
- API quản trị: Đã có đầy đủ API CRUD tại foods.py (GET /api/v1/foods, POST /api/v1/foods, GET /foods/{id}, PUT /foods/{id}, DELETE /foods/{id}).
2. Đã có dữ liệu dinh dưỡng chưa? \rightarrow ĐÃ CÓ (DỮ LIỆU TEST MẪU)
- Những gì đã có:
  - Đã có cấu trúc lưu trữ toàn diện: Calo (energy_kcal), Carbohydrate (carbohydrate_g), Đạm (protein_g), Chất béo (fat_g), Chất xơ (fiber_g), Đường đơn (sugar_g), Chỉ số đường huyết (glycemic_index - GI) và Tải lượng đường huyết (glycemic_load - GL).
  - Đã nạp sẵn bộ dữ liệu test mẫu gồm 14 thực phẩm phổ biến cho người tiểu đường trong food_service.py (Gạo lứt, Yến mạch, Khoai lang, Cơm trắng, Ức gà, Cá hồi, Đậu phụ, Trứng gà, Bông cải xanh, Rau muống, Dưa chuột, Táo, Sữa chua Hy Lạp, Hạnh nhân) gắn nhãn is_test_data: True.
- Những gì còn thiếu:
  - Chưa có bộ dataset lớn chính thức: Dự án cần TV1 cung cấp file dữ liệu đầy đủ từ Bảng thành phần thực phẩm Việt Nam (Viện Dinh Dưỡng) hoặc USDA FoodData Central để nạp chính thức.
  - Chưa lưu vi chất Natri (sodium) và Chất béo bão hòa (saturated_fat).
3. Đã có Recipe (Công thức nấu ăn) chưa? \rightarrow CHƯA CÓ
- Hiện trạng thực tế: Hoàn toàn chưa triển khai.
- Giải thích:
  - Hiện tại hệ thống chỉ quản lý ở cấp độ thực phẩm đơn lẻ (Food), ví dụ: 150g Gạo lứt luộc, 100g Ức gà áp chảo, 150g Bông cải xanh luộc.
  - Chưa có bảng recipes (lưu tên món phức hợp như "Canh chua cá hồi", "Phở bò gạo lứt"), chưa có bảng ingredients (định lượng từng nguyên liệu cấu thành món) và chưa có trường lưu các bước hướng dẫn nấu nướng.
4. Đã có Nutrition Calculator (Bộ tính toán dinh dưỡng) chưa? \rightarrow ĐÃ CÓ
Đã xây dựng và hoạt động trong các service:
1. Tính tổng dinh dưỡng bữa ăn (nutrition_engine.py): Tính toán tổng Calo, Carb, Protein, Fat, Xơ dựa trên hệ số khẩu phần (serving_multiplier).
2. Tính tải lượng đường huyết (GL): Tính tự động dựa trên công thức: \text{GL} = \frac{\text{GI} \times \text{Carbohydrate (g)}}{100}
3. Tính chỉ số khối cơ thể (BMI): Tự động tính toán từ chiều cao và cân nặng trong health_profile.py: \text{BMI} = \frac{\text{Weight (kg)}}{(\text{Height (m)})^2}
4. Tính toán thống kê đường huyết: Tính giá trị trung bình (Average), nhỏ nhất (Min), lớn nhất (Max) theo đơn vị đo trong glucose_service.py.
5. Đã có thuật toán gợi ý thực đơn chưa? \rightarrow ĐÃ CÓ (HOÀN THIỆN)
- Mã nguồn: Class ConstraintEngine, NutritionScoringEngine và MealComposer trong nutrition_engine.py.
- Quy trình hoạt động:
  1. Lọc quy tắc (Constraint Engine): Loại bỏ món có trong danh sách kiêng excluded_food_ids, loại bỏ món chứa từ khóa dị ứng excluded_keywords (ví dụ: "tôm", "hải sản"), lọc theo chế độ ăn chay vegetarian (tự động loại bỏ thịt gà, bò, heo, cá), loại bỏ món có lượng đường đơn quá cao (> 15\text{g}).
  2. Chấm điểm & Xếp hạng (Scoring & Ranking): Chấm điểm 0 - 100 dựa trên các tiêu chí y khoa: thưởng điểm cho thực phẩm giàu chất xơ (làm chậm hấp thu glucose), thưởng điểm cho thực phẩm có GI thấp (\le 55), trừ điểm nặng cho thực phẩm có GI cao (\ge 70), thưởng điểm đạm nạc, trừ điểm nếu nhiều đường hoặc nhiều mỡ xấu.
  3. Cơ cấu đĩa ăn (Plate Method của ADA / Bộ Y tế): Bữa trưa/tối tự động kết hợp: 1/4 Tinh bột tốt (GI thấp) + 1/4 Đạm nạc + 1/2 Rau củ giàu chất xơ.
  4. Cảnh báo an toàn y khoa: Nếu tổng lượng carbohydrate bữa ăn vượt quá ngưỡng an toàn (> 55\text{g}), hệ thống tự sinh cảnh báo lưu ý bệnh nhân; luôn kèm lời miễn trừ trách nhiệm y tế lâm sàng.
  5. Lưu vết: Lưu toàn bộ lịch sử gợi ý dạng JSONB snapshot vào bảng meal_recommendations và các món cụ thể vào bảng meal_recommendation_items.
- API sẵn sàng gọi: POST /api/v1/nutrition/recommend (đã test thực tế PASSED 100%).