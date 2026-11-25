# HỆ THỐNG RAG CHO ĐỀ TÀI QUẢN LÝ ĐÁI THÁO ĐƯỜNG TYPE 2 (T2DM)

> **Đề tài:** Ứng dụng AI hỗ trợ tự quản lý đái tháo đường type 2 thông qua tư vấn tri thức, gợi ý dinh dưỡng và giám sát tư thế tập luyện.  
> **Phiên bản:** 2.0 (Hoàn thành P8 — Tích hợp LLM, Kiểm tra An toàn & Trích dẫn Nguồn).  
> **Cập nhật:** 03/11/2026.

---

## 1. Kiến Trúc Luồng Xử Lý (Architecture Flow)

```text
medical_knowledge_base_cleaned.xlsx
          ↓ (prepare.py)
medical_knowledge_base.json (29 knowledge entries K001–K029)
          ↓ (embedding.py)
knowledge_embeddings.npy (29 x 384) + knowledge_metadata.json
          ↓ (vector_store.py)
   knowledge.index (FAISS IndexFlatIP)
          ↓ (retriever.py)
   MedicalRetriever (Top-K Cosine Search + Lọc Topic)
          ↓ (safety.py)
   Safety Check & Guardrails (Ưu tiên K006, K007-009, K028, K029; Từ chối kê đơn/chẩn đoán)
          ↓ (generator.py)
   LLM Generator Adapter (Gemini API 1.5 Flash / Mock LLM minh bạch)
          ↓ (source_resolver.py)
   RAG Chain Output: Câu trả lời + Cảnh báo an toàn + Danh sách Citations có URL & số trang
          ↓ (test_rag.py)
   Bộ kiểm thử tự động 24 câu hỏi lâm sàng (Đánh giá Groundedness, Citation, An toàn)
```

---

## 2. Giải Thích Các Khái Niệm Cốt Lõi

### 2.1. Knowledge Base
* Cơ sở tri thức y khoa có cấu trúc gồm 29 bản ghi (`K001` đến `K029`), được trích xuất và chuẩn hóa từ các hướng dẫn lâm sàng uy tín: **ADA Standards of Care in Diabetes (2024)**, **WHO**, **IDF**, và **Bộ Y tế Việt Nam (QĐ 5481/QĐ-BYT)**.
* Mỗi bản ghi chứa: `kb_id`, `topic` (Nutrition, Exercise, Safety, Treatment), `subtopic`, nội dung tri thức (`knowledge`), mức độ an toàn (`safety_level`), hành động hệ thống (`action`) và nguồn gốc (`source_id`, `section_page`).

### 2.2. Embedding Model & FAISS Vector Store
* **Embedding Model:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 chiều, chuẩn hóa vector độ dài đơn vị $L_2$).
* **Vector Store:** `faiss.IndexFlatIP` (Cosine Similarity thông qua tích vô hướng).

### 2.3. Safety Check & Guardrails (`safety.py`)
* Ngăn chặn tuyệt đối việc tự ý chẩn đoán bệnh, kê đơn thuốc hoặc thay đổi liều lượng điều trị.
* Đảm bảo các cảnh báo nguy cơ biến chứng võng mạc (`K006`), loét bàn chân (`K008`) và dấu hiệu cấp tính dừng tập (`K028`, `K029`) **không bao giờ bị ghi đè bởi các khuyến nghị tập luyện thông thường**.

### 2.4. LLM Generator & Citation Resolver (`generator.py` & `source_resolver.py`)
* Hỗ trợ Google Gemini API thông qua REST endpoint tiêu chuẩn, cấu hình an toàn với `temperature=0.1` để triệt tiêu ảo giác.
* Hỗ trợ chế độ Mock LLM có dán nhãn minh bạch khi chạy kiểm thử hoặc chưa có API Key.
* Tự động ánh xạ `source_id` sang tên tài liệu chính thức, tổ chức ban hành, năm và URL kiểm chứng y khoa.

---

## 3. Cấu Trúc Thư Mục Dự Án

```text
d:\NCKH-2026-2027/
│
├── .venv/                         # Môi trường ảo Python 3.10
├── requirements.txt               # Danh sách thư viện phụ thuộc
├── .gitignore                     # Bỏ qua file nặng (.venv, .cache) và .env
├── .env.example                   # Mẫu cấu hình API Key và tham số LLM
│
├── medical_knowledge_base.json    # 29 tri thức y khoa JSON (K001–K029)
├── knowledge_embeddings.npy       # Ma trận 29 vector 384 chiều
├── knowledge_metadata.json        # Metadata mapping 1-1 với vector
├── knowledge.index                # FAISS Index Flat Inner Product
│
├── vector_store.py                # Nạp vector & tạo FAISS index
├── retriever.py                   # Lớp MedicalRetriever & hàm retrieve()
├── safety.py                      # Module Safety Check & Guardrails
├── source_resolver.py             # Tra cứu thông tin nguồn tài liệu & URL
├── generator.py                   # Adapter Gemini API & Mock LLM
├── rag_chain.py                   # Pipeline RAG hoàn chỉnh & CLI tương tác
├── test_retrieval.py              # Bộ 15 câu test Retrieval (HitRate@K, Mean Recall@K)
├── test_rag.py                    # Bộ 24 câu test Answer Generation & An toàn
│
├── README_RAG.md                  # Hướng dẫn kiến trúc & sử dụng
├── P7_retrieval_report.md         # Báo cáo tối ưu Retrieval & kiểm định tri thức an toàn
├── P8_rag_report.md               # Báo cáo nghiệm thu hoàn thiện RAG Chain
└── PROGRESS_OVERVIEW.md           # Bảng tổng quan tiến độ đề tài
```

---

## 4. Hướng Dẫn Sử Dụng

### Bước 1: Kích hoạt môi trường ảo
```powershell
.\.venv\Scripts\Activate.ps1
```

### Bước 2: Cấu hình API Key (Tùy chọn)
Nếu muốn gọi trực tiếp Google Gemini API:
```powershell
copy .env.example .env
```
Điền `GEMINI_API_KEY` của bạn vào file `.env`. Nếu không có API Key, hệ thống tự động chạy Mock LLM phục vụ kiểm thử mà không bị lỗi.

### Bước 3: Chạy giao diện dòng lệnh tương tác (CLI)
```powershell
python rag_chain.py
```
Nhập câu hỏi bằng tiếng Việt để xem:
* Tri thức được FAISS tìm thấy
* Điểm tương đồng Cosine
* Cảnh báo an toàn (nếu có)
* Câu trả lời từ LLM
* Nguồn tài liệu trích dẫn cụ thể (kèm URL và số mục/trang)

### Bước 4: Chạy kiểm thử tự động
* Kiểm thử chất lượng Retrieval (15 câu):
  ```powershell
  python test_retrieval.py
  ```
* Kiểm thử chất lượng Answer Generation & An toàn (24 câu):
  ```powershell
  python test_rag.py
  ```

---

## 5. Kết Quả Đánh Giá Hiệu Năng (Benchmark)

* **Retrieval HitRate@3:** **80.00%** | **HitRate@5:** **93.33%**
* **Context Groundedness:** **100.00%** (24/24)
* **Citation Accuracy:** **100.00%** (24/24)
* **Relevance:** **91.67%** (22/24)
* **Unsafe Advice Rate:** **0.00%** (0/24)
* **Abstention Accuracy (Từ chối kê đơn / chẩn đoán):** **100.00%** (4/4)
