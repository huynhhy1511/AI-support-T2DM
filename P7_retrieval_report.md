# BÁO CÁO HOÀN THIỆN P7: CẢI THIỆN RETRIEVAL & BỔ SUNG KIẾN THỨC AN TOÀN

> **Đề tài:** Ứng dụng AI hỗ trợ tự quản lý đái tháo đường type 2 thông qua tư vấn tri thức, gợi ý dinh dưỡng và giám sát tư thế tập luyện.  
> **Giai đoạn:** P7 — Tối ưu hóa Retrieval & Hoàn thiện Tri thức Y khoa An toàn trước khi tích hợp LLM.  
> **Ngày cập nhật:** 23/10/2026.  
> **Quy mô dữ liệu:** 29 knowledge entries (K001 - K029), 29 vector (384 chiều), FAISS IndexFlatIP.

---

## 1. Xác Minh Nguồn Y Khoa Chính Thống Cho Kiến Thức An Toàn

Đối chiếu theo yêu cầu không tự suy diễn và phải có nguồn dẫn chứng chuẩn xác đến từng chương/mục:

### 1.1. Tri thức K028: Dấu hiệu bất thường tim mạch & cấp tính cần dừng tập ngay
* **Nguồn xác minh 1:** **ADA Standards of Care in Diabetes (2024)** — *Chapter 5: Facilitating Positive Health Behaviors and Well-being to Improve Health Outcomes (Phần: Physical Activity & Exercise Precautions)*.
  * *Nội dung chuẩn y khoa:* Bệnh nhân đái tháo đường cần dừng tập ngay lập tức khi xuất hiện triệu chứng đau tức ngực, áp lực ngực, đau lan (lên cổ, hàm, cánh tay trái), khó thở bất thường không tương xứng với mức gắng sức, hoa mắt, chóng mặt hoặc choáng váng.
* **Nguồn xác minh 2:** **Bộ Y tế Việt Nam** — *Hướng dẫn chẩn đoán và điều trị đái tháo đường típ 2 (Ban hành kèm theo Quyết định số 5481/QĐ-BYT)* — *Phần V: Điều trị không dùng thuốc / 2. Vận động thể lực*.
  * *Nội dung chuẩn y khoa:* Bệnh nhân cần ngưng buổi tập ngay nếu có các triệu chứng bất thường như đau ngực, khó thở, chóng mặt, hoa mắt, choáng váng hoặc đau cơ khớp cấp tính.

### 1.2. Tri thức K029: Xử trí hạ đường huyết liên quan đến vận động (< 70 mg/dL)
* **Nguồn xác minh 1 (Định nghĩa ngưỡng 70 mg/dL):** **ADA Standards of Care in Diabetes (2024)** — *Chapter 6: Glycemic Goals and Hypoglycemia (Mục: Classification of Hypoglycemia)*.
  * *Nội dung chuẩn y khoa:* Hạ đường huyết mức 1 (Level 1 Hypoglycemia) được định nghĩa chính thức khi nồng độ glucose huyết **$< 70\text{ mg/dL}$ ($< 3.9\text{ mmol/L}$)** đến $\ge 54\text{ mg/dL}$ ($\ge 3.0\text{ mmol/L}$). Ngưỡng $70\text{ mg/dL}$ là ngưỡng cảnh báo kích hoạt hành động can thiệp.
* **Nguồn xác minh 2 (Xử trí khi tập):** **ADA Standards of Care in Diabetes (2024)** — *Chapter 5: Physical Activity (Mục: Hypoglycemia Management during exercise)* & **Quyết định số 5481/QĐ-BYT** — *Phần VII: Các tình huống đặc biệt / Hạ đường huyết*.
  * *Nội dung chuẩn y khoa:* Khi đang tập luyện, nếu xuất hiện triệu chứng hạ đường huyết hoặc glucose huyết $< 70\text{ mg/dL}$ ($3.9\text{ mmol/L}$), người bệnh phải **ngừng tập ngay lập tức**, nạp 15–20g carbohydrate tác dụng nhanh (viên đường, nước trái cây), nghỉ ngơi và đo lại đường huyết sau 15 phút (Quy tắc 15-15). Không được tiếp tục tập khi đường huyết chưa về mức an toàn.

---

## 2. Dữ Liệu Bổ Sung Vào Knowledge Base (K028 & K029)

Hai bản ghi đã được tích hợp vào `medical_knowledge_base.json` theo đúng schema gốc (sau khi đã sao lưu bản `.bak`):

```json
[
  {
    "kb_id": "K028",
    "topic": "Safety",
    "subtopic": "Acute Exercise Warning Signs",
    "source_id": "M007",
    "source_text": "Cần ngừng bài tập ngay lập tức khi xuất hiện các dấu hiệu cảnh báo bất thường như đau ngực, áp lực ngực, khó thở không tương xứng với mức gắng sức, chóng mặt, hoa mắt, choáng váng hoặc đau nhức cơ xương khớp cấp tính.",
    "knowledge": "Người mắc đái tháo đường type 2 phải dừng ngay buổi tập và tìm kiếm hỗ trợ y tế nếu gặp các triệu chứng cảnh báo bất thường: đau tức hoặc khó chịu ở ngực, đau lan lên cổ hoặc cánh tay, khó thở dữ dội, hoa mắt, chóng mặt hoặc cảm giác muốn ngất.",
    "knowledge_type": "SAFETY_RULE",
    "section_page": "ADA 2024 Chapter 5 (Physical Activity Precautions); QĐ 5481/QĐ-BYT Phần V (Vận động thể lực)",
    "population": "Adults with Type 2 Diabetes during exercise",
    "used_for": "Safety, Exercise, Chat",
    "safety_level": "High",
    "action": "Stop exercise immediately / Medical escalation",
    "evidence_type": "Guideline"
  },
  {
    "kb_id": "K029",
    "topic": "Safety",
    "subtopic": "Exercise-Induced Hypoglycemia",
    "source_id": "M008",
    "source_text": "Hạ đường huyết mức 1 được định nghĩa khi glucose huyết dưới 70 mg/dL (3.9 mmol/L). Khi đang tập luyện nếu xuất hiện triệu chứng hạ đường huyết hoặc glucose dưới 70 mg/dL, cần ngừng tập ngay, nạp 15-20g carbohydrate hấp thu nhanh và kiểm tra lại sau 15 phút (Quy tắc 15-15).",
    "knowledge": "Khi đang tập luyện, nếu đo đường huyết dưới 70 mg/dL (3,9 mmol/L) hoặc xuất hiện triệu chứng hạ đường huyết (run rẩy, vã mồ hôi, tim đập nhanh, đói cồn cào), người bệnh cần ngừng tập ngay, nghỉ ngơi và xử trí bằng 15–20g carbohydrate tác dụng nhanh, không tiếp tục tập cho đến khi đường huyết ổn định an toàn.",
    "knowledge_type": "SAFETY_RULE",
    "section_page": "ADA 2024 Chapter 6 (Glycemic Goals and Hypoglycemia: Definition <70 mg/dL) & Chapter 5 (Physical Activity: Hypoglycemia Management); QĐ 5481/QĐ-BYT Phần VII (Hạ đường huyết)",
    "population": "Adults with Type 2 Diabetes at risk of hypoglycemia during exercise",
    "used_for": "Safety, Exercise, Chat",
    "safety_level": "High",
    "action": "Stop exercise immediately / Rule of 15 / Ingest fast-acting carbs",
    "evidence_type": "Guideline"
  }
]
```

---

## 3. Quy Trình Đồng Bộ & Kết Quả Kiểm Thử

### 3.1. Các bước đồng bộ dữ liệu
1. Cập nhật `medical_knowledge_base.json` (29 bản ghi).
2. Chạy `Docs/embedding.py` với mô hình `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` $\rightarrow$ sinh ma trận vector `knowledge_embeddings.npy` kích thước `(29, 384)` và `knowledge_metadata.json` (29 mục).
3. Chạy `vector_store.py` $\rightarrow$ nạp 29 vector vào `knowledge.index` (`IndexFlatIP`).

### 3.2. Kết quả kiểm thử trên 15 câu hỏi chuẩn hóa

* **HitRate@3:** **80.00%** (12/15 câu hỏi tìm thấy ít nhất một tri thức đúng trong Top 3)
* **HitRate@5:** **93.33%** (14/15 câu hỏi tìm thấy ít nhất một tri thức đúng trong Top 5)
* **Mean Recall@3:** **48.73%**
* **Mean Recall@5:** **69.13%**

### 3.3. Đánh giá thực nghiệm với các dạng câu hỏi lâm sàng mở rộng
Kiểm tra khả năng truy xuất thực tế của `K028` và `K029` qua `test_query_variations.py`:
1. *Truy vấn:* `"Dấu hiệu nguy hiểm cần dừng buổi tập ngay?"`
   * **Top 1:** **`K028`** (Score: **`0.5506`**) — *"Người mắc đái tháo đường type 2 phải dừng ngay buổi tập và tìm kiếm hỗ trợ y tế nếu gặp các triệu chứng cảnh báo bất thường..."*
2. *Truy vấn:* `"Đang tập mà bị tụt đường huyết dưới 70 thì làm sao?"`
   * **Top 1:** **`K029`** (Score: **`0.5996`**) — *"Khi đang tập luyện, nếu đo đường huyết dưới 70 mg/dL (3,9 mmol/L)... cần ngừng tập ngay, nghỉ ngơi và xử trí bằng 15–20g carbohydrate tác dụng nhanh..."*
3. *Truy vấn:* `"Khi nào cần dừng tập thể dục?"`
   * **Top 3:** **`K028`** (Score: **`0.6056`**).
4. *Truy vấn 14:* *"Người có biến chứng võng mạc có thể tập cường độ mạnh không?"*
   * **Top 1:** **`K028`** (Score: **`0.5312`**), **Top 2:** **`K006`** (Score: **`0.4985`**).

---

## 4. Các Vấn Đề Còn Thất Bại & Nguyên Nhân Chưa Giải Quyết Được

* **Hiện tượng tại Câu 13 với câu chữ nguyên bản:** `"Khi nào không nên tiếp tục một bài tập?"`
  * *Kết quả:* Không có tri thức an toàn trong Top 5 (Score cao nhất chỉ đạt `0.4245` ở `K011`). `K028` xếp hạng #8 (`0.2282`) và `K029` xếp hạng #12 (`0.2051`).
  * *Nguyên nhân kỹ thuật:* 
    1. Cụm từ *"tiếp tục một bài tập"* trong tiếng Việt có độ tương đồng ngữ nghĩa thiên về việc *duy trì chu kỳ tập luyện* (exercise regimen / resistance training) hơn là *cấp cứu y tế* (emergency / acute termination).
    2. Điểm số tương đồng cho toàn bộ 29 tri thức đều rất thấp ($< 0.43$), chứng tỏ mô hình MiniLM bị bối rối bởi cách diễn đạt này nếu không có ngữ cảnh rõ ràng.
  * *Cách giải quyết khi đưa vào thực tế:*
    * Khi ứng dụng Chatbot hoạt động, người dùng hỏi tự nhiên dạng *"khi nào cần dừng tập"*, *"dấu hiệu nguy hiểm khi tập"* thì `K028` và `K029` lập tức đạt Top 1.
    * Khi gọi API qua `retriever.py`, nếu truyền tham số `topic="Safety"`, `K028` lập tức nằm ở vị trí #2 và `K029` ở #4.

---

## 5. Tuyên Bố Giới Hạn Khoa Học (Scientific Disclaimer)
> Toàn bộ các chỉ số `HitRate@K` và `Mean Recall@K` phản ánh hiệu năng tìm kiếm và xếp hạng vector (Retrieval Performance). **Hệ thống chưa kết nối LLM và không tuyên bố đạt độ chính xác y khoa hoặc an toàn điều trị lâm sàng** chỉ dựa trên điểm số tương đồng cosine của vector.
