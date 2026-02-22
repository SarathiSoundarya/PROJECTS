import os
from pathlib import Path
from typing import List, Dict
import uuid
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from chromadb.utils import embedding_functions

# A recursive character splitter breaks down large texts into smaller, manageable chunks by using a prioritized list of separators (like paragraphs, sentences, then words), applying each separator in order until the resulting chunks are all below a specified maximum size

DATA_DIR = "knowledge_docs"
DB_DIR = Path(r"C:\Users\soundarya.sarathi\OneDrive - Accenture\study_materials\PROJECTS\MCP_AGENTIC_AI\servers\SERVER_A\tool_utilities\vector_db")

TOPICS = ["pollution", "climate", "disaster", "health"]
COUNTRIES = ["india", "global"]



client = chromadb.PersistentClient(path=DB_DIR)

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
) # gets stored in C:\Users\<your_username>\AppData\Local\huggingface\

collection = client.get_or_create_collection(
    name="policy_documents",
    embedding_function=embedding_fn
)



def extract_pdf_text(filepath: str) -> str:
    reader = PdfReader(filepath)
    text = ""

    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"

    return text


def chunk_text(text: str):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        length_function=len
    )

    return splitter.split_text(text)


def build_metadata(filename: str) -> Dict:
    topics_map={
        "Air_Quality_Guidelines": "pollution",
        "Health_Advisory_Air_Pollution": "health",
        "Climate_Change_and_Health": "climate",
        "Heatwave_Guidelines": "disaster",
        "Flood_Guidelines": "disaster"
    }
    if "who" in filename.lower():
        country = "global"
    else:
        country = "india"
    return {
        "source": filename,
        "topic": topics_map.get(filename, "unknown"),
        "country": country,
    }


def process_and_store():


    for file in os.listdir(DATA_DIR):

        if not file.lower().endswith(".pdf"):
            continue

        filepath = os.path.join(DATA_DIR, file)

        print(f"Processing: {file}")

        text = extract_pdf_text(filepath)

        print("extracted text")
        chunks = chunk_text(text)
        print(f"created {len(chunks)} chunks")
        metadata = build_metadata(file)

        for chunk in chunks:

            collection.add(
                documents=[chunk],
                metadatas=[metadata],
                ids=[f"doc_{uuid.uuid4()}"]
            )


    print("All documents stored successfully")


if __name__ == "__main__":
    process_and_store()
# extracted text
# created 75 chunks
# Processing: NDMA_Flood_Guidelines.pdf
# extracted text
# created 592 chunks
# Processing: NDMA_Heatwave_Guidelines.pdf
# extracted text
# created 8 chunks
# Processing: WHO_Air_Pollution_Compendium.pdf
# extracted text
# created 133 chunks
# Processing: WHO_Climate_Change_and_Health.pdf
# extracted text
# created 29 chunks
# All documents stored successfully