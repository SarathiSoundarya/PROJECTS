from pathlib import Path
import traceback
from typing import List, Dict, Optional
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer, CrossEncoder


DB_DIR = Path(
    r"C:\Users\soundarya.sarathi\OneDrive - Accenture\study_materials\PROJECTS\MCP_AGENTIC_AI\servers\SERVER_A\tool_utilities\vector_db"
)

BASE_DIR = Path(
    r"C:\Users\soundarya.sarathi\OneDrive - Accenture\study_materials\PROJECTS\MCP_AGENTIC_AI\servers\SERVER_A\tool_utilities"
)

MODEL_DIR = BASE_DIR / "models"
EMBED_MODEL_PATH = MODEL_DIR / "all-MiniLM-L6-v2"
RERANK_MODEL_PATH = MODEL_DIR / "cross-encoder-ms-marco-MiniLM-L-6-v2"

MODEL_DIR.mkdir(parents=True, exist_ok=True)



#save the models, only the first time
def save_models_if_needed():
    """
    Download and save models locally if not present.
    """
    
    if EMBED_MODEL_PATH.exists():
        print("Embedding model already exists locally at:", EMBED_MODEL_PATH)
    else:
        print("Saving embedding model locally...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        model.save(str(EMBED_MODEL_PATH))
        print("Embedding model saved at:", EMBED_MODEL_PATH)

    if RERANK_MODEL_PATH.exists():
        print("Cross-encoder model already exists locally at:", RERANK_MODEL_PATH)
    else:
        print("Saving cross-encoder model locally...")
        reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        reranker.save(str(RERANK_MODEL_PATH))
        print("Cross-encoder model saved at:", RERANK_MODEL_PATH)


save_models_if_needed()


#load models from local path
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=str(EMBED_MODEL_PATH)
)

reranker = CrossEncoder(str(RERANK_MODEL_PATH))
print("Models loaded successfully from local paths.")

#chroma db client
client = chromadb.PersistentClient(path=DB_DIR)

collection = client.get_collection(
    name="policy_documents",
    embedding_function=embedding_fn
)
print("Collection count: ", collection.count())
print("ChromaDB collection initialized successfully.")

def retrieve_documents(
    query: str,
    top_k: int = 10,
    topic: Optional[str] = None,
    country: Optional[str] = None,
) -> List[Dict]:

    filters = []
    if topic:
        filters.append({"topic": topic.lower()})

    if country:
        filters.append({"country": country.lower()})

    if len(filters) == 0:
        where_filter = None
    elif len(filters) == 1:
        where_filter = filters[0]
    else:
        where_filter = {"$and": filters}

    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        where=where_filter
    )

    retrieved_docs = []

    for doc, meta, doc_id, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["ids"][0],
        results["distances"][0],
    ):
        retrieved_docs.append({
            "id": doc_id,
            "content": doc,
            "metadata": meta,
            "distance": distance,
        })

    return retrieved_docs



def rerank_documents(query: str, docs: List[Dict], top_k: int = 5):

    if not docs:
        return docs

    pairs = [[query, d["content"]] for d in docs]

    scores = reranker.predict(pairs)

    for d, score in zip(docs, scores):
        d["rerank_score"] = float(score)

    docs = sorted(docs, key=lambda x: x["rerank_score"], reverse=True)

    return docs[:top_k]


def retrieve_with_rerank(
    query: str,
    topic: Optional[str] = None,
    country: Optional[str] = None,
    top_k: int = 5
):
    try:
        top_k = int(top_k) if top_k is not None else 5
        initial_docs = retrieve_documents(
            query=query,
            top_k=20,  # retrieve more for reranking
            topic=topic,
            country=country
        )
        print(f"Initial retrieved documents count: {len(initial_docs)}")
        final_docs = rerank_documents(query, initial_docs, top_k=top_k)
        print(f"Final reranked documents count: {len(final_docs)}")
        return final_docs
    except Exception as e:
        print(f"Error in retrieve_with_rerank: {e}")
        print(traceback.format_exc())
        return []
