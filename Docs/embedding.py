import sys
from pathlib import Path
import json
import numpy as np
from sentence_transformers import SentenceTransformer

# Hỗ trợ hiển thị tiếng Việt trên terminal Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Thư mục hiện tại chứa script
CURRENT_DIR = Path(__file__).resolve().parent

# ============================================================
# 1. Đọc Knowledge Base JSON
# ============================================================

INPUT_FILE = CURRENT_DIR / "medical_knowledge_base.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    knowledge_base = json.load(f)

print(f"Đã đọc {len(knowledge_base)} knowledge entries.")


# ============================================================
# 2. Tạo nội dung dùng để embedding
# ============================================================

documents = []

for item in knowledge_base:
    text = (
        f"Topic: {item['topic']}\n"
        f"Subtopic: {item['subtopic']}\n"
        f"Knowledge: {item['knowledge']}"
    )

    documents.append(text)


# ============================================================
# 3. Load Embedding Model
# ============================================================

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

print("Đang load embedding model...")
model = SentenceTransformer(MODEL_NAME)


# ============================================================
# 4. Tạo embeddings
# ============================================================

print("Đang tạo embeddings...")

embeddings = model.encode(
    documents,
    convert_to_numpy=True,
    normalize_embeddings=True,
    show_progress_bar=True
)

print(f"Kích thước embedding: {embeddings.shape}")


# ============================================================
# 5. Lưu vectors
# ============================================================

output_emb_path = CURRENT_DIR / "knowledge_embeddings.npy"
np.save(
    output_emb_path,
    embeddings
)

print(f"Đã lưu {output_emb_path.name}")


# ============================================================
# 6. Lưu metadata để sau này RAG truy nguồn
# ============================================================

metadata = []

for item in knowledge_base:
    metadata.append({
        "kb_id": item["kb_id"],
        "topic": item["topic"],
        "subtopic": item["subtopic"],
        "source_id": item["source_id"],
        "source_text": item["source_text"],
        "knowledge": item["knowledge"],
        "knowledge_type": item["knowledge_type"],
        "section_page": item["section_page"],
        "population": item["population"],
        "used_for": item["used_for"],
        "safety_level": item["safety_level"],
        "action": item["action"],
        "evidence_type": item["evidence_type"]
    })

output_meta_path = CURRENT_DIR / "knowledge_metadata.json"
with open(
    output_meta_path,
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        metadata,
        f,
        ensure_ascii=False,
        indent=2
    )

print(f"Đã lưu {output_meta_path.name}")