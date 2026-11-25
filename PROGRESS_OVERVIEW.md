# PROJECT PROGRESS OVERVIEW

**Đề tài:** Ứng dụng AI hỗ trợ tự quản lý đái tháo đường type 2 thông qua tư vấn tri thức, gợi ý dinh dưỡng và giám sát tư thế tập luyện.

**Thời gian:** Năm học 2026–2027  
**Nhóm:** 4 thành viên  
**Cập nhật:** 03/11/2026

## 1. Mục tiêu sản phẩm

Xây dựng nền tảng AI hỗ trợ người trưởng thành mắc đái tháo đường type 2 với 3 chức năng chính:

- **AI Assistant:** Hỏi đáp kiến thức y khoa dựa trên RAG và nguồn đáng tin cậy.
- **Nutrition Recommendation:** Gợi ý thực đơn dựa trên hồ sơ người dùng, dữ liệu thực phẩm và các ràng buộc dinh dưỡng.
- **Exercise Monitoring:** Sử dụng MediaPipe Pose để nhận diện chuyển động, đánh giá tư thế và phản hồi lỗi tập luyện.

Hệ thống chỉ hỗ trợ tự quản lý, không thay thế bác sĩ, không chẩn đoán và không kê đơn.

## 2. Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Frontend | React / Next.js (dự kiến) |
| Backend | FastAPI |
| AI / LLM | Gemini API |
| RAG | Sentence Transformers, FAISS |
| Embedding | paraphrase-multilingual-MiniLM-L12-v2 |
| Computer Vision | MediaPipe Pose, OpenCV |
| Database | PostgreSQL (dự kiến) |
| Thành phần | Công nghệ |
|---|---|
| Frontend | React / Next.js (dự kiến) |
| Backend | FastAPI 0.162, SQLAlchemy 2.0, Alembic 1.20 |
| AI / LLM | Gemini API / Mock LLM |
| RAG | Sentence Transformers, FAISS, Hybrid PostgreSQL |
| Embedding | paraphrase-multilingual-MiniLM-L12-v2 (384 dims) |
| Computer Vision | MediaPipe Pose, OpenCV (dự kiến P9.2) |
| Database | PostgreSQL 18 (`diabetes_ai_dev`) |
| Ngôn ngữ | Python 3.10 |

## 3. Tiến độ dự án

| Giai đoạn | Nội dung | Trạng thái |
|---|---|---|
| P1 | Môi trường và Codebase | Hoàn thành |
| P2 | Chuẩn hóa Knowledge Base | Hoàn thành |
| P3 | Embedding | Hoàn thành |
| P4 | FAISS Vector Store | Hoàn thành |
| P5 | Retrieval Engine | Hoàn thành |
| P6 | Retrieval Evaluation | Hoàn thành |
| P7 | Cải thiện Retrieval, bổ sung K028–K029 | Hoàn thành |
| P8 | Tích hợp LLM và RAG Chain | Hoàn thành |
| P9.1A | Food Database & PostgreSQL Migration | Hoàn thành |
| P9.1B | Nutrition Recommendation & RAG Explanation | Hoàn thành |
| P9.2 | Exercise Monitoring (MediaPipe Pose) | Chưa triển khai |
| P10 | Tích hợp, kiểm thử và đánh giá toàn hệ thống | Chưa triển khai |

## 4. Trạng thái kỹ thuật hiện tại

### RAG & AI Module
- 29 knowledge entries: K001–K029 (lưu đồng bộ tại FAISS, JSON và PostgreSQL `medical_knowledges`).
- 8 tài liệu nguồn y khoa: M001–M008 (lưu tại PostgreSQL `medical_sources`).
- 29 embedding vectors, dimension 384, FAISS `IndexFlatIP`.
- Retriever hỗ trợ tìm Top-K vector qua FAISS và tự động làm giàu thông tin chi tiết qua PostgreSQL.
- Đã tích hợp Gemini API/Mock LLM, Safety Engine và Source Resolver.
- Benchmark P8: Context Groundedness 100%, Citation Accuracy 100%, Relevance 91.67%, Unsafe Advice Rate 0%, Abstention Accuracy 100% (24/24 ca test đạt chuẩn).

### Backend & Database Module
- Database PostgreSQL 18: `diabetes_ai_dev` gồm 9 bảng (users, health_profiles, glucose_records, foods, meal_recommendations, meal_recommendation_items, medical_sources, medical_knowledges, alembic_version).
- 35 món ăn Việt Nam chuẩn Viện Dinh Dưỡng Quốc gia đã nạp vào bảng `foods`.
- Backend APIs: 6 nhóm endpoints (health, users, health-profiles, glucose-records, foods, nutrition).
- Kiểm thử Backend: 25/25 unit & integration tests đạt 100% PASSED.

### Các file quan trọng

```text
backend/
├── alembic/versions/ (001_core, 002_nutrition, 003_medical_knowledge)
├── app/
│   ├── api/v1/ (health, users, health_profiles, glucose_records, foods, nutrition)
│   ├── models/ (user, health_profile, glucose_record, food, meal_recommendation, medical_knowledge)
│   ├── services/ (database, user, health_profile, glucose, food, nutrition_engine, nutrition)
│   └── main.py
└── tests/ (25 test cases)

Root & AI/
├── medical_knowledge_base.json
├── knowledge_embeddings.npy
├── knowledge_metadata.json
├── knowledge.index
├── food_database.json / food_database.xlsx
├── vector_store.py
├── retriever.py
├── safety.py
├── source_resolver.py
├── generator.py
├── rag_chain.py
├── food_db.py
├── build_food_db.py
├── import_to_postgres.py
├── test_retrieval.py
├── test_rag.py
├── P7_retrieval_report.md
├── P8_rag_report.md
└── PROGRESS_OVERVIEW.md
```

## 5. Công việc tiếp theo — P9

**P9.1B – Nutrition Recommendation & RAG Integration**
- Hoàn thiện luồng kết nối giữa Nutrition Engine (sinh thực đơn Plate Method) và RAG Chain (giải thích cơ sở y khoa cho bệnh nhân dựa trên K001, K003, K014-K016).
- Kiểm thử recommendation với các hồ sơ bệnh nhân cụ thể (bình thường, thừa cân, dị ứng, có bệnh nền).

**P9.2 – Exercise Monitoring**
- Cài đặt MediaPipe và OpenCV.
- Lựa chọn 5–8 bài tập chuẩn cho T2DM (Squat nông, Calf Raise, Vươn tay, Đi bộ tại chỗ...).
- Tính toán góc khớp, đếm số lần lặp và cảnh báo tư thế sai/dấu hiệu dừng khẩn cấp theo K028-K029.

**P10 – System Integration**
- Ghép nối trọn vẹn Backend REST API với các phân hệ AI.
- Đánh giá toàn diện end-to-end.

## 6. Nguyên tắc phát triển dự án

1. Không tự tạo hoặc suy diễn kiến thức y khoa ngoài nguồn đã xác minh.
2. Mọi khuyến nghị quan trọng phải truy xuất được nguồn.
3. Không để LLM tự quyết định toàn bộ thực đơn hoặc bài tập.
4. Mọi cải tiến phải có kiểm thử và so sánh kết quả thực tế.
5. Sau mỗi giai đoạn, cập nhật trạng thái và kết quả đánh giá vào tài liệu này.

**Trạng thái hiện tại: Hoàn thành P1–P8, P9.1A và P9.1B (Nutrition Recommendation + RAG Explanation; 30/30 backend tests & 30 synthetic profiles benchmark PASSED). Sẵn sàng cho P9.2.**