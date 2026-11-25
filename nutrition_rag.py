"""
Module: nutrition_rag.py
Chức năng: Kết nối Nutrition Recommendation Engine với RAG Pipeline (MedicalRetriever +
SafetyChecker + GeminiLLMGenerator + SourceResolver) để giải thích thực đơn kèm trích dẫn nguồn y khoa.

Nguyên tắc:
- Recommendation Engine quyết định món ăn và tính toán số liệu.
- RAG truy xuất kiến thức y khoa từ Knowledge Base (PostgreSQL + FAISS).
- LLM chỉ giải thích kết quả, KHÔNG tự tạo món ăn, KHÔNG sửa số liệu, KHÔNG tự tạo citation.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from generator import GeminiLLMGenerator
from retriever import MedicalRetriever
from source_resolver import SourceResolver

NUTRITION_SYSTEM_INSTRUCTION = """Bạn là trợ lý AI chuyên giải thích thực đơn hỗ trợ người trưởng thành mắc đái tháo đường type 2, dựa trên thực đơn đã được Nutrition Recommendation Engine tính toán và kiến thức y khoa trong CONTEXT.

BẮT BUỘC TUÂN THỦ:
1. KHÔNG tự thêm món ăn mới, KHÔNG thay đổi khẩu phần hay sửa bất kỳ con số dinh dưỡng nào (kcal, carb, protein, fat, chất xơ, natri) từ Engine.
2. CHỈ sử dụng kiến thức y khoa có trong CONTEXT để giải thích nguyên tắc dinh dưỡng. Nếu Context không đủ thông tin cho một khía cạnh nào đó, hãy nói rõ giới hạn.
3. Giải thích rõ vì sao các món ăn được lựa chọn (GI thấp/trung bình, chất xơ, đạm nạc, Plate Method) và nêu lưu ý dựa trên hồ sơ người dùng.
4. CHỈ trích dẫn các mã [K001], [K002]... thực sự xuất hiện trong CONTEXT. Tuyệt đối KHÔNG tự bịa tên tài liệu hoặc URL.
5. KHÔNG chẩn đoán bệnh, KHÔNG kê đơn hoặc hướng dẫn thay đổi thuốc.
6. Luôn nhắc nhở người bệnh tham khảo bác sĩ hoặc chuyên gia dinh dưỡng khi cần điều chỉnh chế độ ăn cá nhân."""


class NutritionRAGExplainer:
    """Cầu nối RAG + LLM để giải thích thực đơn từ Nutrition Recommendation Engine."""

    def __init__(
        self,
        retriever: Optional[MedicalRetriever] = None,
        generator: Optional[GeminiLLMGenerator] = None,
        source_resolver: Optional[SourceResolver] = None,
    ):
        self.retriever = retriever or MedicalRetriever()
        self.generator = generator or GeminiLLMGenerator()
        self.source_resolver = source_resolver or SourceResolver()

    def _build_retrieval_query(
        self,
        meal_plan: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> str:
        parts = [
            "Nguyên tắc dinh dưỡng cho người đái tháo đường type 2, chất xơ, chỉ số đường huyết GI thấp, ít qua chế biến"
        ]
        if user_profile:
            comorbidities = user_profile.get("comorbidities") or []
            com_str = " ".join(str(c).lower() for c in comorbidities)
            if any(k in com_str for k in ["hypertension", "tăng huyết áp", "tim mạch"]):
                parts.append("hạn chế natri muối tăng huyết áp")
            if user_profile.get("nutrition_goal") == "weight_loss":
                parts.append("kiểm soát cân nặng giảm cân thừa cân béo phì")
            pref = str(user_profile.get("dietary_preference") or "").lower()
            if pref in ["vegetarian", "chay", "vegan"]:
                parts.append("kế hoạch dinh dưỡng cá thể hóa đạm thực vật")
        return ". ".join(parts)

    def _format_meal_summary(self, meal_plan: Dict[str, Any]) -> str:
        """Biểu diễn thực đơn từ Engine thành văn bản khóa chặt số liệu cho LLM."""
        if "meals" in meal_plan and isinstance(meal_plan["meals"], dict):
            lines = [
                f"THỰC ĐƠN CẢ NGÀY (Tổng: {meal_plan.get('daily_total_energy_kcal', 0)} kcal | "
                f"Carb: {meal_plan.get('daily_total_carbohydrate_g', 0)}g | "
                f"Đạm: {meal_plan.get('daily_total_protein_g', 0)}g | "
                f"Béo: {meal_plan.get('daily_total_fat_g', 0)}g | "
                f"Xơ: {meal_plan.get('daily_total_fiber_g', 0)}g | "
                f"Natri: {meal_plan.get('daily_total_sodium_mg', 0)}mg):"
            ]
            for mtype, mdata in meal_plan["meals"].items():
                lines.append(f"- Bữa {mtype}: {mdata.get('total_energy_kcal', 0)} kcal, Carb {mdata.get('total_carbohydrate_g', 0)}g")
                for it in mdata.get("items", []):
                    lines.append(
                        f"  + {it['food_name']} (x{it.get('serving_multiplier', 1.0)}, {it['serving_size_g']}g/suất, GI={it.get('glycemic_index')})"
                    )
            return "\n".join(lines)

        lines = [
            f"THỰC ĐƠN BỮA {meal_plan.get('meal_type', '').upper()} "
            f"(Tổng: {meal_plan.get('total_energy_kcal', 0)} kcal | "
            f"Carb: {meal_plan.get('total_carbohydrate_g', 0)}g | "
            f"Đạm: {meal_plan.get('total_protein_g', 0)}g | "
            f"Béo: {meal_plan.get('total_fat_g', 0)}g | "
            f"Xơ: {meal_plan.get('total_fiber_g', 0)}g | "
            f"Natri: {meal_plan.get('total_sodium_mg', 0)}mg):"
        ]
        for it in meal_plan.get("items", []):
            lines.append(
                f"  + {it['food_name']} (x{it.get('serving_multiplier', 1.0)}, {it['serving_size_g']}g/suất, GI={it.get('glycemic_index')})"
            )
        return "\n".join(lines)

    def _build_grounded_mock_explanation(
        self,
        meal_plan: Dict[str, Any],
        retrieved_items: List[Dict[str, Any]],
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Tạo lời giải thích bám sát hoàn toàn số liệu Engine và Knowledge Base khi chạy chế độ Mock LLM.
        """
        lines = ["[Mock LLM - Giải thích thực đơn dựa trên Engine & Knowledge Base]"]
        if "meals" in meal_plan:
            lines.append(
                f"Thực đơn cả ngày cung cấp tổng {meal_plan.get('daily_total_energy_kcal')} kcal "
                f"({meal_plan.get('daily_total_carbohydrate_g')}g carb, "
                f"{meal_plan.get('daily_total_protein_g')}g protein, "
                f"{meal_plan.get('daily_total_fat_g')}g chất béo, "
                f"{meal_plan.get('daily_total_fiber_g')}g chất xơ, "
                f"{meal_plan.get('daily_total_sodium_mg')}mg natri)."
            )
        else:
            lines.append(
                f"Bữa {meal_plan.get('meal_type')} cung cấp {meal_plan.get('total_energy_kcal')} kcal, "
                f"{meal_plan.get('total_carbohydrate_g')}g carbohydrate, "
                f"{meal_plan.get('total_fiber_g')}g chất xơ và {meal_plan.get('total_sodium_mg')}mg natri."
            )

        lines.append("\nCơ sở y khoa từ Knowledge Base:")
        for item in retrieved_items:
            lines.append(f"- [{item['kb_id']}] {item['knowledge']}")

        notes = meal_plan.get("safety_notes") or []
        if notes:
            lines.append("\nLưu ý từ hồ sơ người dùng:")
            for n in notes:
                lines.append(f"- {n}")

        lines.append(
            "\nLưu ý: Thông tin mang tính hỗ trợ tự quản lý; vui lòng tham khảo ý kiến bác sĩ hoặc chuyên gia dinh dưỡng trước khi thay đổi chế độ ăn."
        )
        return "\n".join(lines)

    def explain_meal_plan(
        self,
        meal_plan: Dict[str, Any],
        user_profile: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """Giải thích thực đơn từ Engine bằng RAG + LLM kèm nguồn trích dẫn thật."""
        if meal_plan.get("is_abstained"):
            return {
                "explanation": (
                    f"Hệ thống tạm dừng gợi ý thực đơn tự động: {meal_plan.get('abstention_reason')}. "
                    "Vui lòng bổ sung thông tin hồ sơ hoặc tham khảo ý kiến bác sĩ/chuyên gia dinh dưỡng."
                ),
                "citations": [],
                "retrieved_kb_ids": [],
                "is_mock": self.generator.use_mock,
            }

        query = self._build_retrieval_query(meal_plan, user_profile)
        retrieved_items = self.retriever.retrieve(query=query, top_k=top_k, topic="Nutrition")
        retrieved_kb_ids = [item["kb_id"] for item in retrieved_items]

        context_blocks = [
            f"[{it['kb_id']}] ({it['topic']} - {it['subtopic']}): {it['knowledge']}"
            for it in retrieved_items
        ]
        context_str = "\n".join(context_blocks) if context_blocks else "Không có tri thức phù hợp."
        meal_summary = self._format_meal_summary(meal_plan)
        profile_str = str(user_profile) if user_profile else "Chưa cung cấp chi tiết bổ sung."

        prompt = (
            f"HỒ SƠ NGƯỜI DÙNG:\n{profile_str}\n\n"
            f"{meal_summary}\n\n"
            f"CẢNH BÁO AN TOÀN TỪ ENGINE:\n{meal_plan.get('safety_notes', [])}\n\n"
            f"CONTEXT Y KHOA:\n{context_str}\n\n"
            "Hãy giải thích vì sao thực đơn trên phù hợp với người bệnh đái tháo đường type 2, "
            "các nguyên tắc dinh dưỡng liên quan dựa trên CONTEXT, và lưu ý cá nhân (không sửa số liệu của Engine)."
        )

        if self.generator.use_mock or not self.generator.api_key:
            explanation_text = self._build_grounded_mock_explanation(
                meal_plan, retrieved_items, user_profile
            )
            is_mock = True
        else:
            llm_res = self.generator.generate(
                prompt=prompt,
                system_instruction=NUTRITION_SYSTEM_INSTRUCTION,
                retrieved_items=retrieved_items,
            )
            explanation_text = llm_res.get("text", "")
            is_mock = bool(llm_res.get("is_mock", False))

        citations = []
        for it in retrieved_items:
            src_info = self.source_resolver.resolve(
                it.get("source_id", ""),
                default_section_page=it.get("section_page", ""),
            )
            citations.append({
                "kb_id": it.get("kb_id"),
                "source_id": it.get("source_id"),
                "title": src_info.get("title"),
                "organization": src_info.get("organization"),
                "year": src_info.get("year"),
                "section_page": src_info.get("section_page"),
                "url": src_info.get("url"),
            })
        return {
            "explanation": explanation_text,
            "citations": citations,
            "retrieved_kb_ids": retrieved_kb_ids,
            "is_mock": is_mock,
        }
