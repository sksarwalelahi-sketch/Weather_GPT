import os
import chromadb
from sentence_transformers import SentenceTransformer


# ==========================================
# CONFIGURATION
# ==========================================

KNOWLEDGE_FOLDER = "knowledge"
CHROMA_FOLDER = "rag/chroma_db"

COLLECTION_NAME = "weather_knowledge"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"


# ==========================================
# LOAD EMBEDDING MODEL
# ==========================================

print("\nLoading embedding model...")

model = SentenceTransformer(EMBEDDING_MODEL)

print("Embedding model loaded successfully!")


# ==========================================
# CREATE CHROMADB
# ==========================================

print("\nCreating vector database...")

client = chromadb.PersistentClient(
    path=CHROMA_FOLDER
)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME
)

print("ChromaDB ready!")


# ==========================================
# TEXT CHUNKING
# ==========================================

def create_chunks(text, chunk_size=500):

    words = text.split()

    chunks = []

    for i in range(0, len(words), chunk_size):

        chunk = " ".join(
            words[i:i + chunk_size]
        )

        if chunk.strip():
            chunks.append(chunk)

    return chunks


# ==========================================
# READ KNOWLEDGE FILES
# ==========================================

def load_documents():

    documents = []

    print("\nReading knowledge files...")

    for root, dirs, files in os.walk(KNOWLEDGE_FOLDER):

        for file in files:

            if file.endswith(".txt"):

                file_path = os.path.join(
                    root,
                    file
                )

                print(f"Reading: {file_path}")

                with open(
                    file_path,
                    "r",
                    encoding="utf-8"
                ) as f:

                    text = f.read()

                chunks = create_chunks(text)

                category = os.path.basename(root)

                for index, chunk in enumerate(chunks):

                    documents.append({
                        "text": chunk,
                        "source": file,
                        "category": category,
                        "chunk_id": index
                    })

    return documents


# ==========================================
# ADD DOCUMENTS TO VECTOR DATABASE
# ==========================================

def ingest_documents():

    documents = load_documents()

    if not documents:

        print("\nNo knowledge documents found.")

        return

    print(
        f"\nTotal chunks found: {len(documents)}"
    )

    texts = [
        doc["text"]
        for doc in documents
    ]

    print("\nCreating embeddings...")

    embeddings = model.encode(
        texts,
        show_progress_bar=True
    )

    print("Embeddings created successfully!")


    # Unique IDs
    ids = []

    metadatas = []

    for index, doc in enumerate(documents):

        ids.append(
            f"{doc['category']}_{doc['source']}_{index}"
        )

        metadatas.append({
            "source": doc["source"],
            "category": doc["category"],
            "chunk_id": doc["chunk_id"]
        })


    print("\nStoring documents in ChromaDB...")

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings.tolist(),
        metadatas=metadatas
    )

    print("\n======================================")
    print("       RAG INGESTION COMPLETE")
    print("======================================")

    print(
        f"\nDocuments stored: {len(documents)}"
    )

    print(
        f"Database location: {CHROMA_FOLDER}"
    )


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    ingest_documents()