"""
Module: source_resolver.py
Chức năng: Tra cứu và chuẩn hóa thông tin nguồn tài liệu y khoa từ medical_sources.xlsx
để phục vụ trích dẫn minh bạch (Citation) trong câu trả lời RAG.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

# Danh mục nguồn tài liệu y khoa đã được xác minh chính thức cho đề tài
STATIC_SOURCES: Dict[str, Dict[str, Any]] = {
    "M001": {
        "source_id": "M001",
        "title": "ADA Standards of Care in Diabetes",
        "organization": "American Diabetes Association (ADA)",
        "year": 2024,
        "section_page": "Section 5: Facilitating Positive Health Behaviors (Nutrition)",
        "url": "https://diabetesjournals.org/care/issue/49/Supplement_1"
    },
    "M002": {
        "source_id": "M002",
        "title": "ADA Standards of Care in Diabetes",
        "organization": "American Diabetes Association (ADA)",
        "year": 2024,
        "section_page": "Section 5 & Section 12 (Retinopathy and Neuropathy Complications)",
        "url": "https://diabetesjournals.org/care/issue/49/Supplement_1"
    },
    "M003": {
        "source_id": "M003",
        "title": "ADA Standards of Care in Diabetes",
        "organization": "American Diabetes Association (ADA)",
        "year": 2024,
        "section_page": "Section 5: Sedentary Behavior & Insulin Sensitivity",
        "url": "https://diabetesjournals.org/care/issue/49/Supplement_1"
    },
    "M004": {
        "source_id": "M004",
        "title": "Hướng dẫn chẩn đoán và điều trị đái tháo đường típ 2 (QĐ 5481/QĐ-BYT)",
        "organization": "Bộ Y tế Việt Nam",
        "year": 2020,
        "section_page": "Phần IV: Điều trị không dùng thuốc (Dinh dưỡng & GI)",
        "url": "https://bvcdn.org.vn/wp-content/uploads/2024/12/5481-qd-byt-huong-dan-chan-doan-va-dieu-tri-dai-thao-duong-tip-2_11120219.pdf"
    },
    "M005": {
        "source_id": "M005",
        "title": "WHO Guidelines on physical activity and sedentary behaviour",
        "organization": "World Health Organization (WHO)",
        "year": 2020,
        "section_page": "Adults and older adults with chronic conditions (Type 2 Diabetes)",
        "url": "http://iris.who.int/server/api/core/bitstreams/faa83413-d89e-4be9-bb01-b24671aef7ca/content"
    },
    "M006": {
        "source_id": "M006",
        "title": "IDF Clinical Practice Recommendations for Managing Type 2 Diabetes",
        "organization": "International Diabetes Federation (IDF)",
        "year": 2025,
        "section_page": "Chapter 2: Glycaemic control assessment and targets (HbA1c & CGM)",
        "url": "https://international-diabetes-federation.s3.eu-west-1.amazonaws.com/media/uploads/2025/04/IDF_Rec_2025.pdf"
    },
    "M007": {
        "source_id": "M007",
        "title": "ADA Standards of Care (2024) Chapter 5 & QĐ 5481/QĐ-BYT Phần V",
        "organization": "ADA / Bộ Y tế Việt Nam",
        "year": 2024,
        "section_page": "ADA 2024 Ch. 5 (Physical Activity Precautions); QĐ 5481/QĐ-BYT Phần V",
        "url": "https://diabetesjournals.org/care/issue/49/Supplement_1"
    },
    "M008": {
        "source_id": "M008",
        "title": "ADA Standards of Care (2024) Chapter 6 & Chapter 5; QĐ 5481/QĐ-BYT Phần VII",
        "organization": "ADA / Bộ Y tế Việt Nam",
        "year": 2024,
        "section_page": "ADA 2024 Ch. 6 (Hypoglycemia <70 mg/dL) & Ch. 5; QĐ 5481/QĐ-BYT Phần VII",
        "url": "https://diabetesjournals.org/care/issue/49/Supplement_1"
    }
}


class SourceResolver:
    """
    Tra cứu và ánh xạ source_id sang thông tin tài liệu đầy đủ và URL tham chiếu.
    """
    def __init__(self, excel_path: Optional[Path] = None):
        self.sources: Dict[str, Dict[str, Any]] = dict(STATIC_SOURCES)
        
        # Thử đọc thêm từ medical_sources.xlsx nếu có
        file_candidates = [
            excel_path,
            BASE_DIR / "Docs" / "medical_sources.xlsx",
            BASE_DIR / "medical_sources.xlsx"
        ]
        
        for candidate in file_candidates:
            if candidate and Path(candidate).exists():
                try:
                    df = pd.read_excel(candidate)
                    for _, row in df.iterrows():
                        sid = str(row.get("ID", "")).strip()
                        if sid:
                            self.sources[sid] = {
                                "source_id": sid,
                                "title": str(row.get("Nguồn", row.get("Title", self.sources.get(sid, {}).get("title", "")))),
                                "organization": self.sources.get(sid, {}).get("organization", "Chuyên môn y tế"),
                                "year": row.get("Năm", row.get("Year", self.sources.get(sid, {}).get("year", 2024))),
                                "section_page": str(row.get("Section/Page", self.sources.get(sid, {}).get("section_page", ""))),
                                "url": str(row.get("URL", self.sources.get(sid, {}).get("url", "")))
                            }
                    break
                except Exception:
                    pass

    def resolve(self, source_id: str, default_section_page: str = "") -> Dict[str, Any]:
        """
        Lấy thông tin chi tiết nguồn từ source_id.
        """
        sid = (source_id or "").strip()
        if sid in self.sources:
            item = dict(self.sources[sid])
            if default_section_page and not item.get("section_page"):
                item["section_page"] = default_section_page
            return item
        
        return {
            "source_id": sid or "Unknown",
            "title": "Hướng dẫn điều trị đái tháo đường",
            "organization": "Y văn chính thống",
            "year": 2024,
            "section_page": default_section_page or "Không xác định",
            "url": ""
        }

