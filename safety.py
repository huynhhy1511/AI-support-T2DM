"""
Module: safety.py
Chức năng: Cơ chế Safety Check y khoa độc lập cho hệ thống RAG đái tháo đường type 2.

Nguyên tắc:
1. Không chỉ dựa vào similarity score để quyết định an toàn/nguy hiểm.
2. Không để khuyến nghị tập luyện chung ghi đè lên cảnh báo an toàn chuyên biệt (K006, K007-K009, K028, K029).
3. Tuyệt đối từ chối chẩn đoán bệnh, kê đơn thuốc hoặc điều chỉnh liều; chuyển hướng đến bác sĩ.
4. Cảnh báo dừng tập ngay khi có dấu hiệu bất thường (đau ngực, chóng mặt, tụt đường huyết < 70 mg/dL).
"""

import re
from typing import List, Dict, Any, Tuple, Optional


class SafetyChecker:
    """
    Bộ kiểm tra và kích hoạt quy tắc an toàn y khoa.
    """

    # Nhận diện ý định hỏi về thuốc / kê đơn / chỉnh liều
    MEDICATION_PATTERNS = [
        r"\buống thuốc\b", r"\bthuốc gì\b", r"\bliều lượng\b", r"\bchỉnh liều\b",
        r"\btăng liều\b", r"\bgiảm liều\b", r"\bbỏ thuốc\b", r"\bngưng thuốc\b",
        r"\bkê đơn\b", r"\bmua thuốc\b", r"\bmetformin\b", r"\binsulin\b",
        r"\bsulfonylurea\b", r"\bthuốc nam\b", r"\bthuốc bắc\b", r"\bđông y\b",
        r"\bthuốc hạ đường\b", r"\btiêm mấy đơn vị\b"
    ]

    # Nhận diện ý định yêu cầu chẩn đoán bệnh
    DIAGNOSIS_PATTERNS = [
        r"\btôi có bị tiểu đường không\b", r"\btôi có mắc bệnh không\b",
        r"\bchẩn đoán giúp\b", r"\bchẩn đoán tôi\b", r"\bcó phải bị đái tháo đường\b",
        r"\bkết luận bệnh\b", r"\bbị bệnh gì\b"
    ]

    # Nhận diện dấu hiệu khẩn cấp khi tập luyện
    ACUTE_EMERGENCY_PATTERNS = [
        r"\bđau ngực\b", r"\btức ngực\b", r"\bkhó thở\b", r"\bchoáng váng\b",
        r"\bhoa mắt\b", r"\bchóng mặt\b", r"\bngất\b", r"\bvã mồ hôi lạnh\b",
        r"\brun rẩy\b", r"\btụt đường huyết\b", r"\bhạ đường huyết\b",
        r"\bdưới 70\b", r"\b< 70\b", r"\bdừng tập\b", r"\bngừng tập\b"
    ]

    # Nhận diện biến chứng võng mạc
    RETINOPATHY_PATTERNS = [
        r"\bvõng mạc\b", r"\bmắt\b", r"\bxuất huyết võng mạc\b", r"\bđục thủy tinh thể\b"
    ]

    # Nhận diện biến chứng thần kinh ngoại biên / bàn chân
    NEUROPATHY_PATTERNS = [
        r"\bthần kinh ngoại biên\b", r"\bmất cảm giác\b", r"\btê bì chân\b",
        r"\bbàn chân\b", r"\bloét chân\b", r"\bvết loét\b", r"\btổn thương chân\b"
    ]

    @classmethod
    def check_query_safety(cls, query: str) -> Dict[str, Any]:
        """
        Phân tích câu hỏi người dùng để xác định các yếu tố nhạy cảm / nguy cơ.
        """
        q_lower = query.lower()
        
        is_medication = any(re.search(pat, q_lower) for pat in cls.MEDICATION_PATTERNS)
        is_diagnosis = any(re.search(pat, q_lower) for pat in cls.DIAGNOSIS_PATTERNS)
        is_emergency = any(re.search(pat, q_lower) for pat in cls.ACUTE_EMERGENCY_PATTERNS)
        has_retinopathy = any(re.search(pat, q_lower) for pat in cls.RETINOPATHY_PATTERNS)
        has_neuropathy = any(re.search(pat, q_lower) for pat in cls.NEUROPATHY_PATTERNS)

        requires_abstention = False
        abstention_type = None
        safety_level = "Normal"
        safety_alerts = []

        if is_medication:
            requires_abstention = True
            abstention_type = "MEDICATION_REFUSAL"
            safety_level = "High"
            safety_alerts.append(
                "CẢNH BÁO AN TOÀN DƯỢC PHẨM: Ứng dụng hỗ trợ tự quản lý không được phép kê đơn, "
                "chỉ định thuốc hoặc thay đổi liều lượng điều trị. Vui lòng tham khảo trực tiếp bác sĩ điều trị."
            )

        if is_diagnosis:
            requires_abstention = True
            abstention_type = "DIAGNOSIS_REFUSAL"
            safety_level = "High"
            safety_alerts.append(
                "CẢNH BÁO CHẨN ĐOÁN: Ứng dụng không thay thế bác sĩ chẩn đoán bệnh. "
                "Để chẩn đoán xác định đái tháo đường, bạn cần đến cơ sở y tế làm xét nghiệm glucose huyết đói, HbA1c hoặc nghiệm pháp OGTT."
            )

        if is_emergency:
            safety_level = "High"
            safety_alerts.append(
                "CẢNH BÁO NGUY HIỂM CẤP TÍNH KHI TẬP: Nếu xuất hiện đau tức ngực, khó thở dữ dội, "
                "hoa mắt, cảm giác muốn ngất hoặc đo đường huyết dưới 70 mg/dL (3.9 mmol/L), "
                "cần DỪNG NGAY BÀI TẬP, nghỉ ngơi, xử trí hạ đường huyết (nạp 15-20g đường nhanh) và gọi hỗ trợ y tế nếu không thuyên giảm."
            )

        if has_retinopathy:
            if safety_level != "High":
                safety_level = "High"
            safety_alerts.append(
                "CẢNH BÁO BIẾN CHỨNG VÕNG MẠC: Bệnh nhân có biến chứng võng mạc tăng sinh nặng "
                "chống chỉ định các bài tập aerobic cường độ mạnh hoặc bài tập kháng lực nặng (nâng tạ nặng)."
            )

        if has_neuropathy:
            if safety_level == "Normal":
                safety_level = "Warning"
            safety_alerts.append(
                "CẢNH BÁO BIẾN CHỨNG THẦN KINH & BÀN CHÂN: Người có biến chứng thần kinh ngoại biên hoặc vết loét hở "
                "cần tránh các bài tập chịu tải trọng lớn lên bàn chân; ưu tiên bơi lội, đạp xe và kiểm tra giày/bàn chân kỹ lưỡng."
            )

        return {
            "query": query,
            "is_medication": is_medication,
            "is_diagnosis": is_diagnosis,
            "is_emergency": is_emergency,
            "has_retinopathy": has_retinopathy,
            "has_neuropathy": has_neuropathy,
            "requires_abstention": requires_abstention,
            "abstention_type": abstention_type,
            "safety_level": safety_level,
            "safety_alerts": safety_alerts,
            "needs_human_review": (safety_level == "High")
        }

    @classmethod
    def apply_safety_guardrails(
        cls,
        retrieved_items: List[Dict[str, Any]],
        safety_analysis: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], str, List[str]]:
        """
        Đảm bảo các quy tắc an toàn đặc hiệu không bị ghi đè bởi kiến thức chung.
        Ví dụ: nếu người dùng hỏi về biến chứng võng mạc, tri thức K006/K028 phải được đẩy lên ưu tiên cao nhất,
        không để tri thức tập kháng lực K019 đưa ra hướng dẫn tập tạ gây xuất huyết võng mạc.
        """
        final_items = list(retrieved_items)
        alerts = list(safety_analysis.get("safety_alerts", []))
        overall_safety_level = safety_analysis.get("safety_level", "Normal")

        # Rà soát safety_level từ metadata các knowledge đã truy xuất
        for item in final_items:
            lvl = item.get("safety_level", "Normal")
            if lvl == "High":
                overall_safety_level = "High"
            elif lvl == "Warning" and overall_safety_level != "High":
                overall_safety_level = "Warning"

        # Nếu phát hiện câu hỏi về võng mạc nhưng K006 chưa có trong top đầu, ưu tiên đưa K006 lên
        if safety_analysis.get("has_retinopathy"):
            final_items.sort(key=lambda x: 0 if x.get("kb_id") in ["K006", "K028"] else 1)

        # Nếu phát hiện câu hỏi về thần kinh/bàn chân, ưu tiên K007, K008, K009
        if safety_analysis.get("has_neuropathy"):
            final_items.sort(key=lambda x: 0 if x.get("kb_id") in ["K007", "K008", "K009", "K010"] else 1)

        # Nếu phát hiện câu hỏi về dấu hiệu dừng tập / hạ đường huyết, ưu tiên K028, K029
        if safety_analysis.get("is_emergency"):
            final_items.sort(key=lambda x: 0 if x.get("kb_id") in ["K028", "K029"] else 1)

        return final_items, overall_safety_level, alerts

