"""
Module: generator.py
Chức năng: Adapter kết nối mô hình ngôn ngữ lớn (Gemini API) và Mock LLM phục vụ kiểm thử.

Yêu cầu kỹ thuật:
- Đọc cấu hình từ .env (GEMINI_API_KEY, GEMINI_MODEL, LLM_TEMPERATURE, LLM_MAX_OUTPUT_TOKENS).
- Tuyệt đối không hard-code API Key.
- Xử lý lỗi đầy đủ: mất kết nối mạng, hết quota (429), API key sai (400), timeout.
- Hỗ trợ Mock LLM minh bạch khi chưa có API key để phục vụ unit test và kiểm thử pipeline,
  có gắn nhãn rõ ràng, không giả lập là câu trả lời thật từ remote LLM.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import httpx
from dotenv import load_dotenv

# Hỗ trợ hiển thị tiếng Việt trên terminal Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Nạp biến môi trường từ file .env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class GeminiLLMGenerator:
    """
    Adapter tương tác với Google Gemini API thông qua REST API chuẩn.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        use_mock: Optional[bool] = None
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
        
        try:
            self.temperature = float(temperature if temperature is not None else os.getenv("LLM_TEMPERATURE", "0.1"))
        except ValueError:
            self.temperature = 0.1
            
        try:
            self.max_output_tokens = int(max_output_tokens if max_output_tokens is not None else os.getenv("LLM_MAX_OUTPUT_TOKENS", "1024"))
        except ValueError:
            self.max_output_tokens = 1024

        env_mock = os.getenv("USE_MOCK_LLM", "false").strip().lower() in ["true", "1", "yes"]
        self.use_mock = use_mock if use_mock is not None else (env_mock or not bool(self.api_key))

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        retrieved_items: Optional[List[Dict[str, Any]]] = None,
        safety_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Gửi prompt đến LLM và nhận câu trả lời.
        Nếu use_mock=True hoặc chưa có API Key, sử dụng Mock Generator có gắn nhãn rõ ràng.
        """
        if self.use_mock or not self.api_key:
            return self._generate_mock_response(prompt, retrieved_items, safety_analysis)

        return self._generate_gemini_api(prompt, system_instruction)

    def _generate_gemini_api(self, prompt: str, system_instruction: Optional[str]) -> Dict[str, Any]:
        """
        Gọi Google Gemini REST API.
        """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        
        payload: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_output_tokens,
                "topP": 0.95
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [
                    {"text": system_instruction}
                ]
            }

        headers = {"Content-Type": "application/json"}

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        return {
                            "text": text.strip(),
                            "status": "success",
                            "model": self.model_name,
                            "is_mock": False
                        }
                    return {
                        "text": "Lỗi: Không nhận được nội dung trả lời hợp lệ từ mô hình.",
                        "status": "empty_candidate",
                        "model": self.model_name,
                        "is_mock": False
                    }
                elif response.status_code == 400:
                    return {
                        "text": f"Lỗi yêu cầu (HTTP 400): API Key không hợp lệ hoặc cấu trúc yêu cầu sai ({response.text}).",
                        "status": "error_bad_request",
                        "model": self.model_name,
                        "is_mock": False
                    }
                elif response.status_code == 429:
                    return {
                        "text": "Lỗi giới hạn (HTTP 429): Đã vượt quá hạn ngạch gọi API của mô hình Gemini (Quota Exceeded).",
                        "status": "error_quota_exceeded",
                        "model": self.model_name,
                        "is_mock": False
                    }
                else:
                    return {
                        "text": f"Lỗi máy chủ Gemini (HTTP {response.status_code}): {response.text}",
                        "status": f"error_http_{response.status_code}",
                        "model": self.model_name,
                        "is_mock": False
                    }
                    
        except httpx.ConnectTimeout:
            return {
                "text": "Lỗi kết nối: Quá thời gian chờ kết nối tới Gemini API (Connection Timeout). Vui lòng kiểm tra đường truyền mạng.",
                "status": "error_timeout",
                "model": self.model_name,
                "is_mock": False
            }
        except httpx.RequestError as exc:
            return {
                "text": f"Lỗi mạng: Không thể kết nối tới máy chủ Google Gemini ({str(exc)}).",
                "status": "error_network",
                "model": self.model_name,
                "is_mock": False
            }
        except Exception as exc:
            return {
                "text": f"Lỗi không xác định khi gọi LLM: {str(exc)}",
                "status": "error_unknown",
                "model": self.model_name,
                "is_mock": False
            }

    def _generate_mock_response(
        self,
        prompt: str,
        retrieved_items: Optional[List[Dict[str, Any]]],
        safety_analysis: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Sinh phản hồi giả lập có gắn nhãn rõ ràng dựa trên context được truy xuất.
        Dùng cho kiểm thử logic pipeline khi chưa cấu hình API key.
        """
        prefix = (
            "[MOCK_LLM_MODE: Chưa cấu hình GEMINI_API_KEY hoặc bật USE_MOCK_LLM. "
            "Câu trả lời dưới đây được bộ suy luận quy tắc tổng hợp trực tiếp từ Knowledge Base "
            "nhằm phục vụ kiểm thử pipeline RAG, không phải kết quả từ remote LLM.]\n\n"
        )

        # Xử lý trường hợp từ chối (Abstention)
        if safety_analysis and safety_analysis.get("requires_abstention"):
            abstention_type = safety_analysis.get("abstention_type")
            if abstention_type == "MEDICATION_REFUSAL":
                content = (
                    "Hệ thống hỗ trợ tự quản lý đái tháo đường type 2 không được phép kê đơn, "
                    "chỉ định thuốc, tư vấn dùng thuốc cụ thể hoặc thay đổi liều lượng điều trị. "
                    "Việc sử dụng thuốc (như Metformin, Insulin, thuốc hạ đường huyết hoặc các bài thuốc khác) "
                    "cần tuân thủ tuyệt đối theo phác đồ cá thể hóa do bác sĩ chuyên khoa chỉ định. "
                    "Vui lòng liên hệ trực tiếp bác sĩ điều trị hoặc cơ sở y tế để được thăm khám và hướng dẫn dùng thuốc an toàn."
                )
            elif abstention_type == "DIAGNOSIS_REFUSAL":
                content = (
                    "Hệ thống không thể và không được phép đưa ra kết luận chẩn đoán bạn có mắc đái tháo đường hay không. "
                    "Theo hướng dẫn của Bộ Y tế và Hiệp hội Đái tháo đường Hoa Kỳ (ADA), chẩn đoán đái tháo đường "
                    "cần dựa trên các xét nghiệm cận lâm sàng chuẩn (như đường huyết lúc đói, HbA1c hoặc nghiệm pháp dung nạp glucose) "
                    "thực hiện tại cơ sở y tế đủ điều kiện. Bạn hãy đến bệnh viện để được bác sĩ khám và chẩn đoán chính xác."
                )
            else:
                content = "Yêu cầu nằm ngoài phạm vi hỗ trợ tự quản lý y tế an toàn. Vui lòng tham vấn chuyên gia y tế."
            return {
                "text": prefix + content,
                "status": "mock_abstention",
                "model": "mock-rule-engine",
                "is_mock": True
            }

        # Nếu không có context tri thức nào
        if not retrieved_items:
            content = (
                "Hiện tại cơ sở tri thức y khoa chưa có đủ thông tin tin cậy để trả lời câu hỏi của bạn. "
                "Ứng dụng khuyến nghị bạn tham khảo ý kiến của bác sĩ chuyên khoa hoặc nhân viên y tế."
            )
            return {
                "text": prefix + content,
                "status": "mock_no_context",
                "model": "mock-rule-engine",
                "is_mock": True
            }

        # Tổng hợp câu trả lời dựa trên tri thức trích xuất
        content_lines = []
        content_lines.append("Dựa trên các hướng dẫn y khoa được trích xuất từ cơ sở tri thức:")
        
        for idx, item in enumerate(retrieved_items[:3], 1):
            kb_id = item.get("kb_id", "")
            knowledge = item.get("knowledge", "")
            subtopic = item.get("subtopic", "")
            content_lines.append(f"- ({kb_id} - {subtopic}): {knowledge}")

        content_lines.append("\nLưu ý an toàn: Thông tin trên mang tính chất hỗ trợ tự quản lý dựa trên guideline y khoa đã được xác minh và không thay thế cho chỉ định điều trị của bác sĩ chuyên khoa.")
        
        return {
            "text": prefix + "\n".join(content_lines),
            "status": "mock_generated",
            "model": "mock-rule-engine",
            "is_mock": True
        }

