import sys
from retriever import MedicalRetriever

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

r = MedicalRetriever()
queries = [
    "Khi nào cần dừng tập thể dục?",
    "Dấu hiệu nguy hiểm cần dừng buổi tập ngay?",
    "Đang tập mà bị tụt đường huyết dưới 70 thì làm sao?",
    "Khi nào không nên tiếp tục một bài tập?"
]

for q in queries:
    print(f"\nQUERY: '{q}'")
    res = r.retrieve(q, top_k=3)
    for i, x in enumerate(res, 1):
        print(f"  {i}. {x['kb_id']} (Score: {x['similarity_score']}) | {x['subtopic']}: {x['knowledge'][:60]}...")
