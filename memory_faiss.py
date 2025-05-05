import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# ✅ Load mô hình embedding
model = SentenceTransformer("keepitreal/vietnamese-sbert")

def embed_text(texts):
    return model.encode(texts, convert_to_numpy=True)

def build_faiss_index(data_file="exchange_policy.txt", index_path="faiss_index"):
    with open(data_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    vectors = embed_text(lines).astype("float32")
    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors)

    os.makedirs(index_path, exist_ok=True)
    faiss.write_index(index, f"{index_path}/index.faiss")
    with open(f"{index_path}/data.json", "w", encoding="utf-8") as f:
        json.dump(lines, f, ensure_ascii=False, indent=2)

    print(f"✅ Đã xây xong FAISS index với {len(lines)} dòng dữ liệu.")

def load_faiss_index(path="faiss_index"):
    index = faiss.read_index(f"{path}/index.faiss")
    with open(f"{path}/data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return index, data

def search_similar_step(query, k=1):
    index, data = load_faiss_index()
    vector = embed_text([query])[0].astype("float32")
    vector = np.array([vector])
    distances, indices = index.search(vector, k)
    results = []
    for i in indices[0]:
        if i < len(data):
            results.append(data[i])
    return results

if __name__ == "__main__":
    build_faiss_index("exchange_policy.txt")
    query = "Khách muốn đổi sang sản phẩm khác thì làm sao?"
    print("🔍 Gợi ý từ trí nhớ:")
    for result in search_similar_step(query, k=2):
        print("-", result)
