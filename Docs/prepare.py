import sys
from pathlib import Path
import pandas as pd
import json

# Hỗ trợ hiển thị tiếng Việt trên terminal Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Lấy đường dẫn thư mục chứa file script hiện tại
CURRENT_DIR = Path(__file__).resolve().parent

# 1. Đọc file Excel
excel_path = CURRENT_DIR / "medical_knowledge_base_cleaned.xlsx"
df = pd.read_excel(excel_path)

# 2. Kiểm tra các cột bắt buộc
required_columns = [
    "KB_ID",
    "Topic",
    "Subtopic",
    "Source_ID",
    "Source_Text",
    "Knowledge",
    "Knowledge_Type",
    "Section/Page",
    "Population",
    "Dùng cho",
    "Safety_Level",
    "Action",
    "Evidence_Type"
]

missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    raise ValueError(
        f"Thiếu các cột trong Excel: {missing_columns}"
    )

# 3. Xử lý ô trống
df = df.fillna("")

# 4. Đổi tên cột sang snake_case
df = df.rename(columns={
    "KB_ID": "kb_id",
    "Topic": "topic",
    "Subtopic": "subtopic",
    "Source_ID": "source_id",
    "Source_Text": "source_text",
    "Knowledge": "knowledge",
    "Knowledge_Type": "knowledge_type",
    "Section/Page": "section_page",
    "Population": "population",
    "Dùng cho": "used_for",
    "Safety_Level": "safety_level",
    "Action": "action",
    "Evidence_Type": "evidence_type"
})

# 5. Chuyển thành list các dictionary
json_data = df.to_dict(orient="records")

# 6. Lưu JSON
output_json_path = CURRENT_DIR / "medical_knowledge_base.json"
with open(
    output_json_path,
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        json_data,
        f,
        ensure_ascii=False,
        indent=2
    )

print(f"Đã chuyển đổi thành công {len(json_data)} knowledge entries!")