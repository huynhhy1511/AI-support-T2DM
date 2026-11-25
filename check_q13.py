import sys
from retriever import MedicalRetriever

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

r = MedicalRetriever()
q = "Khi nào không nên tiếp tục một bài tập?"
results = r.retrieve(q, top_k=29)

print(f"BẢNG XẾP HẠNG TOÀN BỘ 29 TRI THỨC CHO CÂU HỎI:\n'{q}'\n")
for i, item in enumerate(results, 1):
    print(f"{i:2d}. {item['kb_id']} | Score: {item['similarity_score']} | Topic: {item['topic']:<9} | Subtopic: {item['subtopic']:<28} | Knowledge: {item['knowledge'][:60]}...")
