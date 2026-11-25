import sys
import json
from pathlib import Path
from typing import Tuple, List, Dict, Any
import numpy as np
import faiss

# Hỗ trợ hiển thị tiếng Việt trên terminal Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Thư mục gốc chứa script
BASE_DIR = Path(__file__).resolve().parent

def resolve_file_path(filename: str) -> Path:
    """
    Tìm đường dẫn file trong thư mục hiện tại hoặc thư mục Docs/.
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

def build_vector_store(
    embeddings_file: str = "knowledge_embeddings.npy",
    metadata_file: str = "knowledge_metadata.json",
    output_index_file: str = "knowledge.index"
) -> Tuple[faiss.IndexFlatIP, List[Dict[str, Any]]]:
    """
    Xây dựng FAISS Vector Store từ embeddings và metadata.
    
    1. Load knowledge_embeddings.npy
    2. Load knowledge_metadata.json
    3. Kiểm tra số lượng vector và metadata
    4. Tạo FAISS IndexFlatIP (Cosine Similarity qua Inner Product)
    5. Lưu index ra file knowledge.index
    """
    emb_path = resolve_file_path(embeddings_file)
    meta_path = resolve_file_path(metadata_file)
    
    print(f"Đang đọc embeddings từ: {emb_path}")
    embeddings = np.load(emb_path)
    
    print(f"Đang đọc metadata từ: {meta_path}")
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
        
    num_vectors, dim = embeddings.shape
    num_metadata = len(metadata)
    
    print(f"-> Số lượng vector: {num_vectors}")
    print(f"-> Số chiều embedding: {dim}")
    print(f"-> Số lượng metadata records: {num_metadata}")
    
    # Kiểm tra tính toàn vẹn 1-1 giữa vector và metadata
    if num_vectors != num_metadata:
        raise ValueError(
            f"LỖI: Số lượng vector ({num_vectors}) không khớp với số lượng metadata ({num_metadata})!"
        )
        
    # Đảm bảo kiểu dữ liệu float32 cho FAISS
    if embeddings.dtype != np.float32:
        embeddings = embeddings.astype(np.float32)
        
    # Tạo FAISS index bằng IndexFlatIP vì vectors đã được chuẩn hóa độ dài (L2-norm = 1)
    # Tích vô hướng (Inner Product) của các vector chuẩn hóa tương đương Cosine Similarity
    print(f"Đang khởi tạo faiss.IndexFlatIP({dim})...")
    index = faiss.IndexFlatIP(dim)
    
    # Thêm vectors vào index (giữ nguyên thứ tự 0 -> metadata[0], 1 -> metadata[1]...)
    index.add(embeddings)
    print(f"Đã thêm {index.ntotal} vector vào FAISS index.")
    
    # Lưu file index ở thư mục gốc
    out_path = BASE_DIR / output_index_file
    faiss.write_index(index, str(out_path))
    print(f"Đã lưu FAISS index thành công tại: {out_path}")
    
    # Đồng bộ lưu thêm 1 bản trong thư mục Docs/ nếu có
    docs_dir = BASE_DIR / "Docs"
    if docs_dir.exists():
        faiss.write_index(index, str(docs_dir / output_index_file))
        
    return index, metadata

if __name__ == "__main__":
    print("=" * 60)
    print("BẮT ĐẦU XÂY DỰNG FAISS VECTOR STORE")
    print("=" * 60)
    try:
        build_vector_store()
        print("Hoàn tất xây dựng Vector Store thành công!")
    except Exception as e:
        print(f"Lỗi: {e}")
        sys.exit(1)
