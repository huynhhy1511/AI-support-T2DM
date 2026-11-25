import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Hỗ trợ hiển thị tiếng Việt trên terminal Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent

def resolve_file_path(filename: str) -> Path:
    """
    Tìm đường dẫn file trong thư mục hiện tại hoặc Docs/.
    """
    candidates = [
        BASE_DIR / filename,
        BASE_DIR / "Docs" / filename,
        Path(filename)
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(f"Không tìm thấy file: {filename}. Đã tìm tại: {[str(c) for c in candidates]}")


class MedicalRetriever:
    """
    Retriever tìm kiếm kiến thức y khoa dựa trên FAISS và mô hình Sentence-Transformers.
    """
    MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    def __init__(
        self,
        index_file: str = "knowledge.index",
        metadata_file: str = "knowledge_metadata.json",
        model_name: Optional[str] = None
    ):
        self.index_path = resolve_file_path(index_file)
        self.metadata_path = resolve_file_path(metadata_file)
        self.model_name = model_name or self.MODEL_NAME

        # 1. Load FAISS Index
        print(f"Đang nạp FAISS index từ: {self.index_path}")
        self.index = faiss.read_index(str(self.index_path))

        # 2. Load Metadata Mapping
        print(f"Đang nạp Metadata từ: {self.metadata_path}")
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            self.metadata: List[Dict[str, Any]] = json.load(f)

        if self.index.ntotal != len(self.metadata):
            raise ValueError(
                f"Lỗi: Số lượng vector trong FAISS ({self.index.ntotal}) không khớp với metadata ({len(self.metadata)})"
            )

        # 3. Load Embedding Model
        print(f"Đang nạp mô hình Embedding: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        print("MedicalRetriever đã sẵn sàng!")

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        topic: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Truy xuất tri thức y khoa phù hợp với câu hỏi người dùng.

        Quy trình:
        query -> embedding -> normalize -> FAISS search -> kết quả kèm metadata và điểm số.
        
        Args:
            query: Câu hỏi hoặc văn bản cần tìm kiếm.
            top_k: Số lượng kết quả nhiều nhất cần trả về.
            topic: Lọc theo chủ đề (ví dụ: 'Nutrition', 'Exercise', 'Safety', 'Treatment'). Nếu None, tìm trên toàn bộ KB.
        
        Returns:
            Danh sách dict kết quả, sắp xếp theo similarity_score giảm dần.
        """
        if not query or not query.strip():
            return []

        # 1. Tạo embedding cho câu truy vấn
        query_vector = self.model.encode(
            [query.strip()],
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        if query_vector.dtype != np.float32:
            query_vector = query_vector.astype(np.float32)

        # 2. Tìm kiếm qua FAISS
        # Nếu có filter topic: tìm rộng hơn (hoặc toàn bộ index) rồi lọc theo topic
        search_k = self.index.ntotal if topic else min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_vector, search_k)

        # 3. Ghép kết quả với metadata
        results: List[Dict[str, Any]] = []
        raw_scores = scores[0]
        raw_indices = indices[0]

        for score, idx in zip(raw_scores, raw_indices):
            if idx < 0 or idx >= len(self.metadata):
                continue

            meta = self.metadata[idx]

            # Kiểm tra lọc theo topic (không phân biệt hoa thường)
            if topic and meta.get("topic", "").strip().lower() != topic.strip().lower():
                continue

            item = {
                "kb_id": meta.get("kb_id", ""),
                "topic": meta.get("topic", ""),
                "subtopic": meta.get("subtopic", ""),
                "knowledge": meta.get("knowledge", ""),
                "source_id": meta.get("source_id", ""),
                "section_page": meta.get("section_page", ""),
                "safety_level": meta.get("safety_level", ""),
                "action": meta.get("action", ""),
                "similarity_score": round(float(score), 4)
            }
            results.append(item)

            if len(results) >= top_k:
                break

        # Sắp xếp kết quả giảm dần theo similarity_score
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results


# Singleton instance để tái sử dụng nhanh khi gọi hàm retrieve toàn cục
_default_retriever: Optional[MedicalRetriever] = None

def retrieve(
    query: str,
    top_k: int = 5,
    topic: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Hàm tiện ích retrieve toàn cục theo yêu cầu bài toán.
    """
    global _default_retriever
    if _default_retriever is None:
        _default_retriever = MedicalRetriever()
    return _default_retriever.retrieve(query=query, top_k=top_k, topic=topic)


if __name__ == "__main__":
    print("=" * 60)
    print("DEMO KIỂM THỬ NHANH RETRIEVER")
    print("=" * 60)
    test_q = "Người bị tiểu đường nên xây dựng chế độ ăn như thế nào?"
    print(f"Câu hỏi: {test_q}\n")
    
    res = retrieve(test_q, top_k=3)
    for i, item in enumerate(res, 1):
        print(f"[{i}] {item['kb_id']} (Score: {item['similarity_score']})")
        print(f"    Topic: {item['topic']} | Subtopic: {item['subtopic']}")
        print(f"    Knowledge: {item['knowledge']}")
        print(f"    Action: {item['action']} | Safety: {item['safety_level']}\n")
