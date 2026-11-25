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
| P9.1A | Xây dựng Food Database (35 thực phẩm VN chuẩn hóa) | Hoàn thành |
| P9.1B | Nutrition Recommendation Engine & Ràng buộc | Đang thực hiện |
| P9.2 | Exercise Monitoring (MediaPipe Pose) | Chưa triển khai |
| P10 | Tích hợp, kiểm thử và đánh giá toàn hệ thống | Chưa triển khai |

## 4. Trạng thái kỹ thuật hiện tại

### RAG Module

- 29 knowledge entries: K001–K029.
- 29 embedding vectors, dimension 384.
- FAISS `IndexFlatIP`.
- Retriever hỗ trợ tìm Top-K và lọc Topic.
- Đã tích hợp Gemini API/Mock LLM.
- Đã có Safety Check, Prompt Assembly và Source Resolver.
- Đã có bộ 24 câu hỏi đánh giá RAG.

**Kết quả benchmark P8 theo báo cáo:**
- Context Groundedness: 100%.
- Citation Accuracy: 100%.
- Relevance: 91,67%.
- Unsafe Advice Rate: 0%.
- Abstention Accuracy: 100% (4/4 trường hợp).

Các chỉ số trên là kết quả kiểm thử nội bộ, chưa phải xác nhận an toàn lâm sàng.

### Các file quan trọng

```text
Docs/
├── prepare.py
├── embedding.py
├── medical_sources.xlsx
├── medical_knowledge_base_cleaned.xlsx
├── food_database.json
└── food_database.xlsx

Root/
├── medical_knowledge_base.json
├── knowledge_embeddings.npy
├── knowledge_metadata.json
├── knowledge.index
├── vector_store.py
├── retriever.py
├── rag_chain.py
├── generator.py
├── safety.py
├── source_resolver.py
├── test_retrieval.py
├── test_rag.py
├── build_food_db.py
├── food_db.py
├── food_database.json
├── food_database.xlsx
├── P7_retrieval_report.md
├── P8_rag_report.md
└── PROGRESS_OVERVIEW.md
```

## 5. Công việc tiếp theo — P9

**P9.1 – Nutrition Recommendation**
- Food Database: Hoàn thành 35 thực phẩm/món ăn VN (JSON, XLSX).
- food_db.py: Module tra cứu, lọc và kiểm tra dị nguyên.
- Xây dựng Recommendation Engine (tính TDEE, macronutrients, phân bổ bữa ăn theo guideline K003, K014-K016).
- Kết nối kết quả với RAG/LLM để giải thích thực đơn.

**P9.2 – Exercise Monitoring**
- Lựa chọn 5–8 bài tập trong phạm vi nghiên cứu (Squat, Calf Raise, Vươn tay, Đi bộ tại chỗ...).
- Tích hợp MediaPipe Pose và OpenCV.
- Tính toán góc khớp và đặc trưng chuyển động.
- Nhận diện giai đoạn động tác và đếm repetition.
- Phân loại lỗi tư thế và phản hồi người dùng.

**P9.3 – Integration**
- Kết nối Frontend, Backend và các module AI.
- Đồng bộ hồ sơ người dùng, thực đơn và lịch sử tập luyện.
- Tích hợp Safety Engine.

## 6. Nguyên tắc phát triển dự án

1. Không tự tạo hoặc suy diễn kiến thức y khoa ngoài nguồn đã xác minh.
2. Mọi khuyến nghị quan trọng phải truy xuất được nguồn.
3. Không để LLM tự quyết định toàn bộ thực đơn hoặc bài tập.
4. Không tự ý thay đổi cấu trúc Knowledge Base hoặc thêm cột dữ liệu khi chưa có yêu cầu.
5. Mọi cải tiến phải có kiểm thử và so sánh kết quả thực tế.
6. Ưu tiên hoàn thành các chức năng cốt lõi trước khi phát triển tính năng nâng cao.
7. Sau mỗi giai đoạn, cập nhật trạng thái, file bàn giao và kết quả đánh giá vào tài liệu này.

**Trạng thái hiện tại: Hoàn thành P1–P8 và P9.1A (Food Database); đang thực hiện P9.1B.**