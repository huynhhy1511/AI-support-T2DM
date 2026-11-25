import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
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
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Nạp dữ liệu gốc
with open(BASE_DIR / "medical_knowledge_base.json", "r", encoding="utf-8") as f:
    knowledge_base = json.load(f)

# Danh sách 15 câu hỏi kiểm thử chuẩn
# Với Câu 6 ("Người mắc tiểu đường nên vận động như thế nào?"):
# Cho phép mở rộng expected_ids gồm các kiến thức vận động cốt lõi (K011, K012, K013, K017, K018, K019, K020)
TEST_CASES_BASE = [
    {
        "id": 1,
        "group": "Nutrition",
        "question": "Người bị tiểu đường nên xây dựng chế độ ăn như thế nào?",
        "expected_ids": ["K001", "K002", "K003", "K004", "K014", "K015"]
    },
    {
        "id": 2,
        "group": "Nutrition",
        "question": "Có tỷ lệ carbohydrate protein chất béo cố định cho mọi người không?",
        "expected_ids": ["K001", "K002", "K005"]
    },
    {
        "id": 3,
        "group": "Nutrition",
        "question": "Người tiểu đường có nên ăn thực phẩm giàu chất xơ không?",
        "expected_ids": ["K003"]
    },
    {
        "id": 4,
        "group": "Nutrition",
        "question": "Có nên ưu tiên thực phẩm ít qua chế biến không?",
        "expected_ids": ["K004"]
    },
    {
        "id": 5,
        "group": "Nutrition",
        "question": "Chế độ ăn có cần cá nhân hóa không?",
        "expected_ids": ["K001", "K002"]
    },
    {
        "id": 6,
        "group": "Exercise",
        "question": "Người mắc tiểu đường nên vận động như thế nào?",
        # Bao gồm cả hướng dẫn ngắt quãng ngồi tĩnh (K011, K012, K013) và thời lượng aerobic/kháng lực (K017-K020)
        "expected_ids": ["K011", "K012", "K013", "K017", "K018", "K019", "K020"]
    },
    {
        "id": 7,
        "group": "Exercise",
        "question": "Người tiểu đường cần hoạt động thể lực bao nhiêu mỗi tuần?",
        "expected_ids": ["K017", "K018", "K019", "K020"]
    },
    {
        "id": 8,
        "group": "Exercise",
        "question": "Người bị neuropathy cần lưu ý gì khi tập?",
        "expected_ids": ["K007", "K008", "K009"]
    },
    {
        "id": 9,
        "group": "Exercise",
        "question": "Người có vấn đề về võng mạc cần lưu ý gì khi tập?",
        "expected_ids": ["K006"]
    },
    {
        "id": 10,
        "group": "Exercise",
        "question": "Bơi hoặc đạp xe có thể được sử dụng trong trường hợp nào?",
        "expected_ids": ["K007", "K008", "K009"]
    },
    {
        "id": 11,
        "group": "Safety",
        "question": "Có cần đánh giá biến chứng trước khi tập luyện không?",
        "expected_ids": ["K007", "K010"]
    },
    {
        "id": 12,
        "group": "Safety",
        "question": "Người có nguy cơ bàn chân cần lưu ý gì?",
        "expected_ids": ["K007", "K008", "K009"]
    },
    {
        "id": 13,
        "group": "Safety",
        "question": "Khi nào không nên tiếp tục một bài tập?",
        "expected_ids": ["K006", "K008", "K010"]
    },
    {
        "id": 14,
        "group": "Safety",
        "question": "Người có biến chứng võng mạc có thể tập cường độ mạnh không?",
        "expected_ids": ["K006"]
    },
    {
        "id": 15,
        "group": "Treatment",
        "question": "Mục tiêu HbA1c có giống nhau cho tất cả mọi người không?",
        "expected_ids": ["K021", "K022", "K023", "K024", "K025", "K026"]
    }
]

def build_index_for_docs(docs: List[str], model: SentenceTransformer) -> faiss.IndexFlatIP:
    emb = model.encode(docs, convert_to_numpy=True, normalize_embeddings=True)
    if emb.dtype != np.float32:
        emb = emb.astype(np.float32)
    dim = emb.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(emb)
    return index

def evaluate_method(
    name: str,
    index: faiss.IndexFlatIP,
    metadata: List[Dict[str, Any]],
    model: SentenceTransformer,
    test_cases: List[Dict[str, Any]]
) -> Dict[str, Any]:
    hits_3 = 0
    hits_5 = 0
    recall_3_list = []
    recall_5_list = []
    per_question_results = []

    for tc in test_cases:
        q = tc["question"]
        expected = set(tc["expected_ids"])
        q_vec = model.encode([q], convert_to_numpy=True, normalize_embeddings=True)
        if q_vec.dtype != np.float32:
            q_vec = q_vec.astype(np.float32)

        scores, indices = index.search(q_vec, 5)
        top_ids = [metadata[idx]["kb_id"] for idx in indices[0] if 0 <= idx < len(metadata)]
        top_scores = [round(float(s), 4) for s in scores[0]]

        top_3 = set(top_ids[:3])
        top_5 = set(top_ids[:5])

        hit_3 = len(top_3 & expected) > 0
        hit_5 = len(top_5 & expected) > 0
        rec_3 = len(top_3 & expected) / len(expected)
        rec_5 = len(top_5 & expected) / len(expected)

        if hit_3:
            hits_3 += 1
        if hit_5:
            hits_5 += 1
        recall_3_list.append(rec_3)
        recall_5_list.append(rec_5)

        per_question_results.append({
            "id": tc["id"],
            "question": q,
            "expected": sorted(list(expected)),
            "retrieved": top_ids,
            "scores": top_scores,
            "hit_3": hit_3,
            "hit_5": hit_5,
            "rec_3": rec_3,
            "rec_5": rec_5
        })

    n = len(test_cases)
    return {
        "name": name,
        "hitrate_3": (hits_3 / n) * 100,
        "hitrate_5": (hits_5 / n) * 100,
        "mean_recall_3": (sum(recall_3_list) / n) * 100,
        "mean_recall_5": (sum(recall_5_list) / n) * 100,
        "details": per_question_results
    }

def main():
    print("Đang nạp mô hình SentenceTransformer...")
    model = SentenceTransformer(MODEL_NAME)

    # 1. Phương án A: Topic + Subtopic + Knowledge (Gốc)
    docs_A = []
    for item in knowledge_base:
        t = f"Topic: {item['topic']}\nSubtopic: {item['subtopic']}\nKnowledge: {item['knowledge']}"
        docs_A.append(t)
    index_A = build_index_for_docs(docs_A, model)
    res_A = evaluate_method("Phương án A (Gốc: Topic + Subtopic + Knowledge)", index_A, knowledge_base, model, TEST_CASES_BASE)

    # 2. Phương án B: Topic + Subtopic + Population + Knowledge
    docs_B = []
    for item in knowledge_base:
        t = (
            f"Topic: {item['topic']}\n"
            f"Subtopic: {item['subtopic']}\n"
            f"Population: {item.get('population', '')}\n"
            f"Knowledge: {item['knowledge']}"
        )
        docs_B.append(t)
    index_B = build_index_for_docs(docs_B, model)
    res_B = evaluate_method("Phương án B (+ Population)", index_B, knowledge_base, model, TEST_CASES_BASE)

    # In so sánh tổng quan
    print("\n" + "=" * 70)
    print("BẢNG SO SÁNH HIỆU NĂNG RETRIEVAL (EMPIRICAL BENCHMARK)")
    print("=" * 70)
    print(f"{'Chỉ số':<25} | {'Phương án A (Gốc)':<22} | {'Phương án B (+Population)':<22}")
    print("-" * 75)
    print(f"{'HitRate@3':<25} | {res_A['hitrate_3']:>6.2f}%                 | {res_B['hitrate_3']:>6.2f}%")
    print(f"{'HitRate@5':<25} | {res_A['hitrate_5']:>6.2f}%                 | {res_B['hitrate_5']:>6.2f}%")
    print(f"{'Mean Recall@3':<25} | {res_A['mean_recall_3']:>6.2f}%                 | {res_B['mean_recall_3']:>6.2f}%")
    print(f"{'Mean Recall@5':<25} | {res_A['mean_recall_5']:>6.2f}%                 | {res_B['mean_recall_5']:>6.2f}%")
    print("=" * 70)

    # So sánh chi tiết từng câu hỏi
    print("\nCHI TIẾT THAY ĐỔI THEO TỪNG CÂU HỎI:")
    print("-" * 75)
    for q_a, q_b in zip(res_A["details"], res_B["details"]):
        q_id = q_a["id"]
        status_a = f"H@3:{'Y' if q_a['hit_3'] else 'N'}, H@5:{'Y' if q_a['hit_5'] else 'N'}, R@5:{q_a['rec_5']:.2f}"
        status_b = f"H@3:{'Y' if q_b['hit_3'] else 'N'}, H@5:{'Y' if q_b['hit_5'] else 'N'}, R@5:{q_b['rec_5']:.2f}"
        
        diff = ""
        if (not q_a["hit_3"] and q_b["hit_3"]) or (not q_a["hit_5"] and q_b["hit_5"]) or (q_b["rec_5"] > q_a["rec_5"]):
            diff = "-> [TĂNG CHẤT LƯỢNG]"
        elif (q_a["hit_3"] and not q_b["hit_3"]) or (q_a["hit_5"] and not q_b["hit_5"]) or (q_b["rec_5"] < q_a["rec_5"]):
            diff = "-> [GIẢM CHẤT LƯỢNG]"
        else:
            diff = "-> [KHÔNG ĐỔI]"

        print(f"Câu {q_id:2d}: {diff}")
        print(f"   PA A: Retrieved: {q_a['retrieved']} ({status_a})")
        print(f"   PA B: Retrieved: {q_b['retrieved']} ({status_b})")

    # Lưu kết quả ra file JSON để làm bằng chứng thực nghiệm
    report_data = {
        "method_A": {k: v for k, v in res_A.items() if k != "details"},
        "method_B": {k: v for k, v in res_B.items() if k != "details"},
        "details_A": res_A["details"],
        "details_B": res_B["details"]
    }
    with open(BASE_DIR / "experiment_embedding_results.json", "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    print("\nĐã lưu kết quả thực nghiệm tại: experiment_embedding_results.json")

if __name__ == "__main__":
    main()
