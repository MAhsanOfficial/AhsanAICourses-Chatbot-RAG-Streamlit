import os
import pickle
import numpy as np

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")

KB_DIR = os.path.join(os.path.dirname(__file__), "..", "kb")
VECTOR_STORE_PATH = os.path.join(os.path.dirname(__file__), "kb_vectors.pkl")


model = None
nn_model = None
documents = []
embeddings = None


def ingest_kb():
    global nn_model, documents, embeddings
    print("📘 Ingesting Knowledge Base...")

    docs = []
    for fname in os.listdir(KB_DIR):
        if fname.endswith(".md"):
            with open(os.path.join(KB_DIR, fname), "r", encoding="utf-8") as f:
                text = f.read()
                docs.append(text)

    if not docs:
        raise ValueError("No KB markdown files found in kb/ folder!")

    global model
    from sentence_transformers import SentenceTransformer
    from sklearn.neighbors import NearestNeighbors

    model = SentenceTransformer("all-MiniLM-L6-v2")

   
    embeddings = model.encode(docs, convert_to_numpy=True)

    
    nn_model = NearestNeighbors(n_neighbors=3, metric="cosine")
    nn_model.fit(embeddings)
    documents = docs

    
    with open(VECTOR_STORE_PATH, "wb") as f:
        pickle.dump((docs, embeddings), f)

    print("✅ KB ingested and saved without FAISS!")


def load_kb():
    global nn_model, documents, embeddings
    if os.path.exists(VECTOR_STORE_PATH):
        from sklearn.neighbors import NearestNeighbors

        with open(VECTOR_STORE_PATH, "rb") as f:
            docs, embs = pickle.load(f)
            documents = docs
            embeddings = embs
            nn_model = NearestNeighbors(n_neighbors=3, metric="cosine")
            nn_model.fit(embeddings)
        print("✅ KB loaded successfully (using sklearn NearestNeighbors).")
    else:
        print("⚠️ No KB found. Run ingest_kb() first.")


def get_relevant_docs(query: str, top_k: int = 3):
    """Return the top_k most relevant documents from the KB for a query."""
    global nn_model, documents, embeddings
    
    if nn_model is None or not documents:
        load_kb()
        if nn_model is None:
       
            print("⚠️ KB not available: returning empty context for query.")
            return []

    
    global model
    if model is None:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("all-MiniLM-L6-v2")

    query_vec = model.encode([query], convert_to_numpy=True)
    distances, indices = nn_model.kneighbors(query_vec, n_neighbors=min(top_k, len(documents)))

    results = [documents[i] for i in indices[0]]
    return results


if __name__ == "__main__":
    ingest_kb()
