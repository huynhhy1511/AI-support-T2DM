import sys
from typing import List, Dict, Any
from retriever import MedicalRetriever

# Hỗ trợ hiển thị tiếng Việt trên terminal Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ============================================================
# 1. BỘ 15 CÂU HỎI TEST & EXPECTED KB_IDS
# ============================================================

TEST_CASES = [
    # Nhóm 1: Nutrition (Dinh dưỡng)
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
        "expected_ids": ["K002", "K005", "K001"]
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

    # Nhóm 2: Exercise (Vận động / Luyện tập)
    {
        "id": 6,
        "group": "Exercise",
        "question": "Người mắc tiểu đường nên vận động như thế nào?",
        # Cho phép các tri thức vận động liên quan: ngắt quãng ngồi tĩnh (K011, K012, K013) và thời lượng aerobic/kháng lực (K017-K020)
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
        "expected_ids": ["K009", "K007", "K008"]
    },

    # Nhóm 3: Safety (An toàn & Cảnh báo)
    {
        "id": 11,
        "group": "Safety",
        "question": "Có cần đánh giá biến chứng trước khi tập luyện không?",
        "expected_ids": ["K010", "K007"]
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
        # K028 (dấu hiệu cấp tính: đau ngực, khó thở, chóng mặt) và K029 (hạ đường huyết < 70 mg/dL khi tập)
        "expected_ids": ["K028", "K029", "K008", "K006", "K010"]
    },
    {
        "id": 14,
        "group": "Safety",
        "question": "Người có biến chứng võng mạc có thể tập cường độ mạnh không?",
        "expected_ids": ["K006"]
    },

    # Nhóm 4: Glycemic / Treatment (Mục tiêu đường huyết & Điều trị)
    {
        "id": 15,
        "group": "Treatment",
        "question": "Mục tiêu HbA1c có giống nhau cho tất cả mọi người không?",
        "expected_ids": ["K021", "K026", "K022", "K023", "K024", "K025"]
    }
]


def run_evaluation() -> None:
    """
    Chạy 15 câu hỏi kiểm thử qua MedicalRetriever và đánh giá HitRate@K và Mean Recall@K.
    """
    retriever = MedicalRetriever()
    
    hits_at_3 = 0
    hits_at_5 = 0
    recall_scores_3 = []
    recall_scores_5 = []
    total_questions = len(TEST_CASES)

    print("\n" + "#" * 70)
    print("CHẠY ĐÁNH GIÁ RETRIEVAL CHO 15 CÂU HỎI TEST")
    print("#" * 70 + "\n")

    for test in TEST_CASES:
        q_id = test["id"]
        group = test["group"]
        question = test["question"]
        expected_ids = set(test["expected_ids"])

        # Truy xuất top 5 kết quả
        results = retriever.retrieve(query=question, top_k=5)
        retrieved_ids = [r["kb_id"] for r in results]

        # Kiểm tra Top-3 và Top-5
        top_3_ids = set(retrieved_ids[:3])
        top_5_ids = set(retrieved_ids[:5])

        # 1. HitRate@K: 1 nếu có ít nhất 1 expected ID nằm trong Top-K, ngược lại 0
        is_hit_3 = len(top_3_ids & expected_ids) > 0
        is_hit_5 = len(top_5_ids & expected_ids) > 0

        if is_hit_3:
            hits_at_3 += 1
        if is_hit_5:
            hits_at_5 += 1

        # 2. Recall@K chuẩn: |Retrieved@K ∩ Expected| / |Expected|
        rec_3 = len(top_3_ids & expected_ids) / len(expected_ids)
        rec_5 = len(top_5_ids & expected_ids) / len(expected_ids)
        recall_scores_3.append(rec_3)
        recall_scores_5.append(rec_5)

        # Hiển thị kết quả chi tiết từng câu hỏi
        print("=" * 60)
        print(f"CÂU HỎI {q_id} [{group}]:")
        print(f"QUESTION:\n{question}\n")
        print(f"EXPECTED KB_IDs: {sorted(list(expected_ids))}")
        print(f"RETRIEVED KB_IDs: {retrieved_ids}")
        print(f"STATUS: HitRate@3 = {'HIT' if is_hit_3 else 'MISS'} | HitRate@5 = {'HIT' if is_hit_5 else 'MISS'}")
        print(f"METRIC: Recall@3 = {rec_3:.2f} | Recall@5 = {rec_5:.2f}")
        print("\nTOP RESULTS:")

        for i, item in enumerate(results, 1):
            is_match = "*" if item["kb_id"] in expected_ids else " "
            print(f"{i}. {item['kb_id']}{is_match}")
            print(f"   Topic: {item['topic']} | Subtopic: {item['subtopic']}")
            print(f"   Score: {item['similarity_score']}")
            print(f"   Source: {item['source_id']} ({item['section_page']}) | Safety: {item['safety_level']}")
            print(f"   Knowledge: {item['knowledge']}\n")

    # ============================================================
    # TỔNG HỢP KẾT QUẢ ĐÁNH GIÁ (EVALUATION SUMMARY)
    # ============================================================
    hitrate_3 = (hits_at_3 / total_questions) * 100
    hitrate_5 = (hits_at_5 / total_questions) * 100
    mean_recall_3 = (sum(recall_scores_3) / total_questions) * 100
    mean_recall_5 = (sum(recall_scores_5) / total_questions) * 100

    print("=" * 60)
    print("TỔNG HỢP KẾT QUẢ ĐÁNH GIÁ (EVALUATION SUMMARY)")
    print("=" * 60)
    print(f"Tổng số câu hỏi kiểm thử: {total_questions}")
    print("\n--- 1. HIT RATE (Tỷ lệ câu hỏi tìm thấy >= 1 expected ID trong Top-K) ---")
    print(f"HitRate@3 = {hitrate_3:.2f}% ({hits_at_3}/{total_questions})")
    print(f"HitRate@5 = {hitrate_5:.2f}% ({hits_at_5}/{total_questions})")
    print("\n--- 2. MEAN RECALL@K CHUẨN (|Retrieved ∩ Expected| / |Expected|) ---")
    print(f"Mean Recall@3 = {mean_recall_3:.2f}%")
    print(f"Mean Recall@5 = {mean_recall_5:.2f}%")
    print("=" * 60)


if __name__ == "__main__":
    run_evaluation()
