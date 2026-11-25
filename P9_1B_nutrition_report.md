# BÁO CÁO P9.1B – NUTRITION RECOMMENDATION & TÍCH HỢP RAG

**Đề tài:** Ứng dụng AI hỗ trợ tự quản lý đái tháo đường type 2 thông qua tư vấn tri thức, gợi ý dinh dưỡng và giám sát tư thế tập luyện.
**Ngày báo cáo:** 25/11/2026

## 1. Kiến trúc tổng thể và nguyên tắc tách biệt trách nhiệm

Hệ thống gợi ý dinh dưỡng được thiết kế theo kiến trúc tách biệt 3 tầng:
1. **Nutrition Recommendation Engine (`backend/app/services/nutrition_engine.py`, `nutrition_service.py`):**
   - Đọc dữ liệu thực phẩm chính thức từ PostgreSQL (`foods` – 35 món ăn Việt Nam chuẩn Viện Dinh Dưỡng Quốc gia, kết hợp ánh xạ `sodium_mg` và `allergens` từ `food_database.json` mà không thay đổi cấu trúc schema database).
   - Kiểm tra an toàn đầu vào qua `NutritionSafetyGuard` (kiểm tra hồ sơ thiếu thông tin, xử lý thận trọng bệnh thận mạn CKD, siết natri với bệnh nhân tăng huyết áp).
   - Lọc ràng buộc tuyệt đối qua `ConstraintEngine` (loại trừ dị ứng theo từ khóa + từ đồng nghĩa + metadata allergens; không fallback về danh sách không an toàn khi không tìm được món thỏa mãn).
   - Chấm điểm theo `NutritionScoringEngine` (chất xơ, GI, GL, đường đơn, đạm nạc, natri, sở thích ăn uống, mục tiêu kiểm soát cân nặng).
   - Tổ chức thực đơn 1 bữa hoặc cả ngày (4 bữa: sáng, trưa, tối, phụ) theo Plate Method qua `MealComposer`, hỗ trợ thay thế món ăn cùng nhóm (`suggest_substitutes`).
2. **RAG & Knowledge Retrieval (`retriever.py`, `source_resolver.py`):**
   - `MedicalRetriever` truy xuất kiến thức y khoa liên quan (`K001`–`K029`) từ FAISS kết hợp PostgreSQL (`medical_knowledges`, `medical_sources`).
   - `SourceResolver` ánh xạ nguồn trích dẫn thật (`M001`–`M008` từ ADA, WHO, IDF, Bộ Y tế).
3. **LLM Explanation (`nutrition_rag.py`, `generator.py`):**
   - Chỉ nhận thực đơn đã chốt từ Engine cùng số liệu đã tính, tuyệt đối không tự thêm món, sửa định lượng hoặc bịa citation.

## 2. API Endpoints đã hoàn thiện

- `POST /api/v1/nutrition/recommend`: Gợi ý 1 bữa ăn theo hồ sơ và ràng buộc.
- `POST /api/v1/nutrition/recommend-daily`: Gợi ý thực đơn cả ngày (sáng, trưa, tối, phụ) kèm tổng năng lượng, macro, tỷ lệ % calo và tổng natri.
- `POST /api/v1/nutrition/substitute`: Đề xuất tối đa N món ăn thay thế cùng nhóm dinh dưỡng, bảo đảm ràng buộc dị ứng/chế độ ăn.
- `POST /api/v1/nutrition/explain`: Tạo thực đơn cả ngày và sinh giải thích RAG + LLM kèm danh sách trích dẫn nguồn y khoa.

## 3. Kết quả kiểm thử (30 Synthetic User Profiles & 30 Backend Unit Tests)

### A. Kiểm thử Backend Unit & API Tests (`pytest`)
- Tổng số ca kiểm thử: **30/30 PASSED (100%)** (gồm 25 tests nền tảng có sẵn + 5 tests chuyên biệt cho P9.1B tại `backend/tests/test_nutrition_engine_p91b.py`).

### B. Đánh giá trên 30 hồ sơ giả lập (`test_nutrition_30_profiles.py`)
Phân bố 30 hồ sơ giả lập: kiểm soát cân nặng (6), mức độ vận động (5), sở thích ăn uống chay/low-carb/low-sodium (5), dị ứng thực phẩm (5), tăng huyết áp/tim mạch (4), bệnh thận mạn CKD (3 – kỳ vọng từ chối), hồ sơ thiếu dữ liệu bắt buộc (2 – kỳ vọng từ chối).

| Tiêu chí đánh giá | Kết quả | Ghi chú |
|---|---|---|
| 1. Nutritional Calculation Accuracy | 100.00% (25/25) | Tổng dinh dưỡng từng bữa và cả ngày khớp chính xác với khẩu phần |
| 2. Constraint Satisfaction Rate | 100.00% (25/25) | Tuân thủ chế độ chay và giới hạn natri < 2000mg/ngày cho tăng huyết áp |
| 3. Allergy Violation Rate | 0.00% (0/5 ca dị ứng) | Đạt mục tiêu 0% vi phạm dị ứng |
| 4. Personalization | 100.00% (14/14) | Đáp ứng sở thích ăn uống và mục tiêu cân nặng |
| 5. RAG Groundedness | 100.00% (25/25) | Lời giải thích giữ nguyên số liệu Engine và bám sát `[Kxxx]` (chế độ Mock LLM) |
| 6. Citation Accuracy | 100.00% (25/25) | 100% trích dẫn ánh xạ đúng nguồn thật `M001`–`M008` |
| 7. Abstention Accuracy | 100.00% (5/5) | Từ chối đúng 3/3 ca CKD và 2/2 ca thiếu hồ sơ bắt buộc |

*Lưu ý khoa học:* Các số liệu trên là kết quả kiểm thử tự động trên hồ sơ giả lập (synthetic profiles) với chế độ Mock LLM có kiểm soát; chưa thay thế đánh giá lâm sàng trực tiếp từ bác sĩ hoặc chuyên gia dinh dưỡng.
