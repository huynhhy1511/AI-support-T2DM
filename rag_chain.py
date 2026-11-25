"""
Module: rag_chain.py
Chức năng: Điều phối luồng xử lý RAG hoàn chỉnh cho đề tài đái tháo đường type 2.

Luồng xử lý (Pipeline Flow):
User Question
    ↓
MedicalRetriever (Tìm kiếm Top-K Vector FAISS)
    ↓
Safety Check (Kiểm tra nguy cơ cấp tính, biến chứng & quy tắc an toàn)
    ↓
Prompt Assembly (System Prompt 10 nguyên tắc + Context + Question)
    ↓
LLM Generator (Gemini API hoặc Mock LLM có gắn nhãn)
    ↓
Citation Enrichment (Tra cứu thông tin nguồn từ SourceResolver)
    ↓
Standardized Output (Answer, Citations, Safety Level, Needs Human Review)
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from retriever import MedicalRetriever, retrieve
from safety import SafetyChecker
from generator import GeminiLLMGenerator
from source_resolver import SourceResolver

# Hỗ trợ hiển thị tiếng Việt trên terminal Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent

SYSTEM_INSTRUCTION = """Bạn là trợ lý AI chuyên cung cấp thông tin y khoa hỗ trợ người bệnh tự quản lý đái tháo đường type 2, dựa trên các hướng dẫn lâm sàng đã được xác minh (ADA, WHO, IDF, Bộ Y tế Việt Nam).

BẮT BUỘC TUÂN THỦ TUYỆT ĐỐI 10 NGUYÊN TẮC SAU:
1. Bạn là công cụ hỗ trợ thông tin, KHÔNG PHẢI BÁC SĨ và KHÔNG THAY THẾ CHUYÊN GIA Y TẾ.
2. CHỈ sử dụng kiến thức y khoa có trong CONTEXT được cung cấp để đưa ra khuyến nghị. Tuyệt đối không bịa đặt hoặc sử dụng thông tin ngoài context.
3. KHÔNG tự chẩn đoán bệnh, KHÔNG kê đơn thuốc, KHÔNG hướng dẫn thay đổi liều lượng thuốc (như insulin, metformin, sulfonylurea...) hay khuyên bỏ thuốc.
4. KHÔNG tự suy diễn thêm các con số, ngưỡng đường huyết hay chỉ số không có trong nguồn.
5. Nếu Context KHÔNG ĐỦ THÔNG TIN để trả lời, phải nói rõ ràng là chưa có đủ cơ sở dữ liệu và khuyến nghị người dùng tham khảo nhân viên y tế chuyên khoa.
6. KHÔNG tự tạo ra nguồn tham khảo hoặc mã trích dẫn giả mạo. Chỉ trích dẫn các mã [K001], [K002]... thực sự có trong Context.
7. Sử dụng ngôn ngữ tiếng Việt chuẩn mực, rõ ràng, dễ hiểu, thân thiện và phù hợp với người trưởng thành.
8. Phân biệt rõ giữa kiến thức chung và khuyến nghị mang tính cá thể hóa (phụ thuộc vào tình trạng sức khỏe cụ thể của mỗi người).
9. KHÔNG BAO GIỜ khẳng định rằng một chế độ ăn hay bài tập nhất định là phù hợp tuyệt đối cho tất cả bệnh nhân.
10. LUÔN LUÔN kèm theo lời nhắc nhở rằng thông tin mang tính hỗ trợ tự quản lý, người bệnh cần tham khảo ý kiến bác sĩ điều trị trước khi thay đổi chế độ dinh dưỡng, tập luyện hoặc điều trị."""


class RAGChain:
    """
    Chuỗi xử lý RAG hoàn chỉnh (Retriever + Safety Guard + Generator + Citation Resolver).
    """
    def __init__(
        self,
        retriever: Optional[MedicalRetriever] = None,
        generator: Optional[GeminiLLMGenerator] = None,
        source_resolver: Optional[SourceResolver] = None
    ):
        self.retriever = retriever or MedicalRetriever()
        self.generator = generator or GeminiLLMGenerator()
        self.source_resolver = source_resolver or SourceResolver()

    def query(
        self,
        question: str,
        top_k: int = 5,
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Xử lý câu hỏi người dùng qua toàn bộ pipeline RAG.
        """
        clean_q = (question or "").strip()
        if not clean_q:
            return {
                "question": question,
                "answer": "Vui lòng nhập câu hỏi để được hỗ trợ thông tin đái tháo đường type 2.",
                "citations": [],
                "safety_level": "Normal",
                "safety_alerts": [],
                "needs_human_review": False,
                "retrieved_kb_ids": [],
                "is_mock": False
            }

        # BƯỚC 1: Phân tích an toàn tiền truy vấn (Safety Analysis)
        safety_analysis = SafetyChecker.check_query_safety(clean_q)

        # BƯỚC 2: Truy xuất tri thức liên quan từ FAISS
        # Nếu câu hỏi nhắm đến chủ đề cụ thể, ưu tiên lọc theo topic
        retrieved_raw = self.retriever.retrieve(query=clean_q, top_k=top_k, topic=topic)

        # BƯỚC 3: Áp dụng cơ chế Safety Guardrails lên Context
        # Đảm bảo cảnh báo biến chứng/cấp tính không bị ghi đè bởi kiến thức chung
        retrieved_items, safety_level, safety_alerts = SafetyChecker.apply_safety_guardrails(
            retrieved_raw, safety_analysis
        )
        retrieved_kb_ids = [item["kb_id"] for item in retrieved_items]

        # BƯỚC 4: Xây dựng Prompt Context
        context_blocks = []
        for idx, item in enumerate(retrieved_items, 1):
            block = (
                f"[{item['kb_id']}] Topic: {item['topic']} | Subtopic: {item['subtopic']}\n"
                f"Mức độ an toàn: {item['safety_level']} | Hành động: {item['action']}\n"
                f"Nội dung: {item['knowledge']}"
            )
            context_blocks.append(block)

        context_str = "\n\n".join(context_blocks) if context_blocks else "Không có tri thức phù hợp trong cơ sở dữ liệu."

        # Bổ sung chỉ thị an toàn đặc biệt vào User Prompt nếu có cảnh báo
        safety_directive = ""
        if safety_alerts:
            safety_directive = "\n\nCẢNH BÁO AN TOÀN Y TẾ ĐẶC BIỆT CẦN LƯU Ý KHI TRẢ LỜI:\n" + "\n".join(f"- {a}" for a in safety_alerts)

        user_prompt = f"""Dưới đây là thông tin tham khảo từ Cơ sở tri thức y khoa đã được xác thực:
--- CONTEXT BẮT ĐẦU ---
{context_str}
--- CONTEXT KẾT THÚC ---
{safety_directive}

CÂU HỎI CỦA NGƯỜI DÙNG:
{clean_q}

YÊU CẦU TRẢ LỜI:
- Trả lời bằng tiếng Việt tự nhiên, chính xác, bám sát các tri thức trong CONTEXT trên.
- Trích dẫn mã tri thức (ví dụ: [K001], [K006]...) ngay sau câu có sử dụng thông tin.
- Nếu câu hỏi yêu cầu kê đơn, chỉnh liều thuốc hoặc chẩn đoán bệnh, hãy TỪ CHỐI thực hiện và giải thích rõ lý do an toàn y khoa, hướng người dùng gặp bác sĩ chuyên khoa.
- Nhắc nhở người bệnh tham khảo ý kiến bác sĩ trước khi áp dụng."""

        # BƯỚC 5: Gửi Prompt tới LLM Generator
        gen_res = self.generator.generate(
            prompt=user_prompt,
            system_instruction=SYSTEM_INSTRUCTION,
            retrieved_items=retrieved_items,
            safety_analysis=safety_analysis
        )

        answer_text = gen_res.get("text", "")
        is_mock = gen_res.get("is_mock", False)

        # BƯỚC 6: Tra cứu và đóng gói Citation
        citations = []
        for item in retrieved_items:
            sid = item.get("source_id", "")
            resolved_source = self.source_resolver.resolve(
                source_id=sid,
                default_section_page=item.get("section_page", "")
            )
            citations.append({
                "kb_id": item.get("kb_id", ""),
                "source_id": sid,
                "section_page": item.get("section_page", resolved_source.get("section_page", "")),
                "source_title": resolved_source.get("title", ""),
                "organization": resolved_source.get("organization", ""),
                "year": resolved_source.get("year", 2024),
                "url": resolved_source.get("url", ""),
                "safety_level": item.get("safety_level", "Normal"),
                "similarity_score": item.get("similarity_score", 0.0)
            })

        return {
            "question": clean_q,
            "answer": answer_text,
            "citations": citations,
            "safety_level": safety_level,
            "safety_alerts": safety_alerts,
            "needs_human_review": (safety_level == "High" or safety_analysis.get("requires_abstention", False)),
            "retrieved_kb_ids": retrieved_kb_ids,
            "is_mock": is_mock,
            "model": gen_res.get("model", "")
        }


def run_cli_interactive():
    """
    Giao diện dòng lệnh (CLI) tương tác trực tiếp kiểm thử RAG.
    """
    print("=" * 70)
    print("HỆ THỐNG RAG HỖ TRỢ TỰ QUẢN LÝ ĐÁI THÁO ĐƯỜNG TYPE 2 (P8)")
    print("=" * 70)
    print("Đang khởi tạo RAG Chain...")
    chain = RAGChain()
    print("Hệ thống đã sẵn sàng!")
    print("Nhập câu hỏi bằng tiếng Việt (hoặc gõ 'exit' / 'quit' để thoát).\n")

    while True:
        try:
            q = input("\n[NGƯỜI DÙNG NHẬP] >> ").strip()
            if not q:
                continue
            if q.lower() in ["exit", "quit", "q"]:
                print("Tạm biệt!")
                break

            print("\nĐang xử lý truy xuất và sinh câu trả lời...")
            res = chain.query(q)

            print("\n" + "-" * 70)
            print(f"CÂU HỎI: {res['question']}")
            print(f"CÁC KB_ID TRUY XUẤT: {res['retrieved_kb_ids']}")
            print(f"MỨC ĐỘ AN TOÀN: {res['safety_level']} | CẦN BÁC SĨ ĐÁNH GIÁ: {res['needs_human_review']}")
            if res["safety_alerts"]:
                print("CẢNH BÁO AN TOÀN:")
                for alert in res["safety_alerts"]:
                    print(f"  ⚠️ {alert}")

            print("\n[CÂU TRẢ LỜI CỦA HỆ THỐNG]:")
            print(res["answer"])

            print("\n[DANH SÁCH NGUỒN TRÍCH DẪN (CITATIONS)]:")
            for cit in res["citations"][:3]:
                print(f"  • [{cit['kb_id']}] {cit['source_title']} ({cit['organization']} - {cit['year']})")
                print(f"    Mục/Trang: {cit['section_page']}")
                if cit['url']:
                    print(f"    URL: {cit['url']}")
                print(f"    Điểm tương đồng Cosine: {cit['similarity_score']}")

            print("-" * 70)

        except (KeyboardInterrupt, EOFError):
            print("\nĐã thoát chương trình.")
            break
        except Exception as e:
            print(f"Lỗi: {e}")


if __name__ == "__main__":
    run_cli_interactive()

