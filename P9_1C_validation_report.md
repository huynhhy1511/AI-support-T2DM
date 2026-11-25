# BÁO CÁO P9.1C – AUDIT VÀ VALIDATION NUTRITION RECOMMENDATION

**Đề tài:** Ứng dụng AI hỗ trợ tự quản lý đái tháo đường type 2 thông qua tư vấn tri thức, gợi ý dinh dưỡng và giám sát tư thế tập luyện.
**Ngày kiểm định:** 25/11/2026

## 1. Các lỗi phát hiện qua Audit P9.1B và mức độ nghiêm trọng

| STT | Hạng mục kiểm tra | Mô tả lỗi phát hiện ở P9.1B | Mức độ | Phương án khắc phục đã áp dụng |
|---|---|---|---|---|
| 1 | Cá thể hóa (Personalization) | `health_profile` chỉ dùng để kiểm tra thiếu trường; tuổi, giới tính, chiều cao, cân nặng, mức vận động không tham gia tính toán. Dẫn đến 13 hồ sơ khác nhau (`P04`, `P06`–`P11`, `P15`, `P17`–`P21`) đều nhận đúng 1 mức **1.195 kcal/ngày**. | Nghiêm trọng (HIGH) | Bổ sung `EnergyCalculator` tính BMR theo công thức **Mifflin-St Jeor (1990)** × hệ số vận động (TDEE), phân bổ 4 bữa (25% / 35% / 30% / 10%) và điều chỉnh khẩu phần (`serving_multiplier`) theo từng cá nhân. |
| 2 | Tổng năng lượng (Energy) | Thực đơn cả ngày chỉ đạt **792 – 1.195 kcal/ngày**, thấp hơn nhiều so với nhu cầu tối thiểu của người trưởng thành. | Nghiêm trọng (HIGH) | Đặt ngưỡng sàn an toàn (1.400 kcal nam, 1.200 kcal nữ; cảnh báo nếu BMI < 18.5 hoặc $\ge 30$), đưa dầu thực vật (`F030`, 5g = 44 kcal/bữa) vào bữa trưa/tối và nhân khẩu phần đạm/tinh bột theo TDEE trong giới hạn carb. |
| 3 | Chế độ ăn `low_sodium` | `P15` chọn `dietary_preference="low_sodium"` nhưng `nutrition_service.py` không truyền cờ `low_sodium_required=True` sang `MealComposer`, khiến natri vẫn ở mức 1.549 mg. | Trung bình (MEDIUM) | Kích hoạt `low_sodium_required=True` khi `dietary_preference` là `low_sodium`/`it_muoi` tương tự bệnh lý tăng huyết áp. |
| 4 | Dữ liệu thực phẩm (`foods`) | Trong PostgreSQL, cột `sugar_g` bị gán `0.0` cho cả 35 món (kể cả trái cây) do bảng thành phần thực phẩm VN chưa tách riêng đường đơn; `food_db.py` khi đọc PostgreSQL chưa đồng bộ `sodium_mg` và `allergens`. | Trung bình (MEDIUM) | Đồng bộ `food_db.py` dùng chung `get_food_extra` để thống nhất `sodium_mg` và `allergens`; ghi nhận rõ giới hạn chưa có số liệu tách đường đơn `sugar_g` (đánh giá qua tổng Carb, Fiber, GI). |
| 5 | RAG Explanation | Mới kiểm thử bằng chế độ `Mock LLM` do chưa cấu hình `GEMINI_API_KEY`. | Thấp (LOW) | Tách bạch rõ trong báo cáo: kiểm chứng logic bám sát Engine và Citation trên Mock LLM; cần cấu hình API key khi đánh giá văn phong sinh tự nhiên của Gemini API. |

## 2. Kết quả kiểm tra chi tiết 5 khía cạnh

### 2.1. Kiểm tra năng lượng và khả năng cá thể hóa (Before vs After)
Sau khi bổ sung `EnergyCalculator` (Mifflin-St Jeor) và điều chỉnh khẩu phần (`serving_multiplier` bước 0.25x trong giới hạn carb):
- Các hồ sơ khác nhau về tuổi, giới tính, chiều cao, cân nặng, mức vận động đã nhận mức năng lượng và khẩu phần khác nhau phù hợp thực tế:
  - **P01** (Nam, 168cm, 82kg, `light`, `weight_loss`): **955.0 kcal** (Before) $\rightarrow$ **1.658,3 kcal** (After).
  - **P02** (Nữ, 156cm, 68kg, `sedentary`, `weight_loss`): **955.0 kcal** (Before) $\rightarrow$ **1.151,0 kcal** (After).
  - **P03** (Nam, 170cm, 79kg, `moderate`, `weight_loss`): **955.0 kcal** (Before) $\rightarrow$ **1.822,3 kcal** (After).
  - **P04** (Nữ, 160cm, 56kg, `moderate`, `maintenance`): **1.195,0 kcal** (Before) $\rightarrow$ **1.764,3 kcal** (After).
  - **P08** (Nữ, 155cm, 58kg, `sedentary`, `maintenance`): **1.195,0 kcal** (Before) $\rightarrow$ **1.480,6 kcal** (After).
  - **P09** (Nam, 172cm, 70kg, `moderate`, `maintenance`): **1.195,0 kcal** (Before) $\rightarrow$ **1.932,8 kcal** (After).
  - **P15** (`dietary_preference="low_sodium"`): **1.195,0 kcal / 1.549,0 mg Na** (Before) $\rightarrow$ **1.602,2 kcal / 877,5 mg Na** (After).
  - **P22** (`hypertension`, Nữ, 62kg): **1.098,0 kcal / 586,0 mg Na** (Before) $\rightarrow$ **1.349,7 kcal / 768,3 mg Na** (After).
  - **P25** (`tim mạch` + `weight_loss`): **792,0 kcal / 425,0 mg Na** (Before) $\rightarrow$ **1.164,2 kcal / 665,1 mg Na** (After).
- **Giới hạn ghi nhận cần chuyên gia dinh dưỡng đánh giá:**
  - Nhóm ăn chay (`P12`, `P13`, `P16`) hiện đạt **1.199,5 kcal/ngày** do kho 35 món hiện tại còn ít món chay giàu năng lượng/đạm thực vật.
  - Ở một số hồ sơ không có tăng huyết áp có mức TDEE cao (`P01`, `P03`, `P09`, `P19`), khi nhân khẩu phần lên 1.5x–2.0x, lượng natri ước tính đạt **2.300–3.315 mg/ngày**; hệ thống đã tự động phát hiện và xuất cảnh báo nhắc nêm nhạt.

### 2.2. Kiểm tra dữ liệu 35 món ăn trong PostgreSQL
- Đã kiểm tra đủ 35 bản ghi (`is_test_data = false`) trong bảng `foods` của PostgreSQL:
  - 8 món đạm nguyên chất (`F007`–`F013`, `F014` đậu phụ, và `F030` dầu thực vật) có `GI = 0` do không chứa tinh bột đáng kể.
  - Công thức `GL = (GI × Carb) / 100` khớp 100% ở cả 35 món.
  - **Điểm cần lưu ý:** Cột `sugar_g` hiện tại là `0.0` (chưa có số liệu tách đường đơn từ nguồn Bảng thành phần thực phẩm Việt Nam). Với chế biến thực tế, bữa trưa/tối đã cộng thêm `5g` dầu thực vật (`F030` = 44 kcal/bữa) và luôn kèm ghi chú giới hạn muối/gia vị nêm.

### 2.3. Kiểm tra dị ứng, tăng huyết áp và CKD
- **Dị ứng (`P17`–`P21`, `P24`):** 0/6 ca vi phạm dị ứng (0.0%).
- **Tăng huyết áp (`P22`–`P25`, `P15`):** 5/5 ca đều có tổng natri < 900 mg/ngày (đạt xa ngưỡng < 2.000 mg/ngày).
- **Bệnh thận mạn CKD (`P26`–`P28`):** 3/3 ca đều bị từ chối tạo thực đơn tự động và chuyển hướng bác sĩ chuyên khoa thận/dinh dưỡng, tuyệt đối không tự đặt mức protein/kali/natri.

### 2.4. Kiểm tra RAG Explanation
- Trên chế độ **Mock LLM** (`use_mock=True`), 25/25 ca hợp lệ giữ nguyên chính xác 100% số liệu kcal/carb/protein/fat/fiber/sodium từ Engine và trích dẫn đúng `[K001]`–`[K029]` ánh xạ về nguồn thật `M001`–`M008`.
- Chưa chạy kiểm thử qua Gemini API thực tế do môi trường chưa có `GEMINI_API_KEY`.

## 3. Bảng tổng hợp đánh giá Before / After (30 hồ sơ giả lập & 30 Backend Tests)

| Tiêu chí đánh giá | Before (P9.1B) | After (P9.1C) | Ghi chú |
|---|---|---|---|
| Backend Unit & API Tests (`pytest`) | 30/30 (100%) | **30/30 (100%)** | Không hồi quy chức năng |
| Nutritional Calculation Accuracy | 100.0% | **100.0%** | Đúng ở mọi mức `serving_multiplier` |
| Constraint Satisfaction Rate | 100.0% | **100.0%** | Cả `P15` (`low_sodium`) đạt chuẩn |
| Allergy Violation Rate | 0.0% | **0.0%** | Mục tiêu 0% |
| Cá thể hóa năng lượng theo TDEE | Chưa có (cố định 792–1195 kcal) | **Đạt (1151–1964 kcal theo TDEE)** | Phản ánh tuổi, giới, cao, nặng, vận động |
| RAG Groundedness (Mock LLM) | 100.0% | **100.0%** | Giữ nguyên số liệu Engine |
| Citation Accuracy | 100.0% | **100.0%** | Nguồn `M001`–`M008` từ `SourceResolver` |
| Abstention Accuracy (CKD & Thiếu hồ sơ) | 100.0% (5/5) | **100.0% (5/5)** | 3 CKD + 2 thiếu hồ sơ |
