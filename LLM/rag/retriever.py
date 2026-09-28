import chromadb
from sentence_transformers import SentenceTransformer


# ==========================================
# CONFIGURATION
# ==========================================

CHROMA_FOLDER = "rag/chroma_db"
COLLECTION_NAME = "weather_knowledge"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"


# ==========================================
# LOAD EMBEDDING MODEL
# ==========================================

print("\nLoading embedding model...")

model = SentenceTransformer(EMBEDDING_MODEL)

print("Embedding model loaded!")


# ==========================================
# CONNECT TO CHROMADB
# ==========================================

client = chromadb.PersistentClient(
    path=CHROMA_FOLDER
)

collection = client.get_collection(
    name=COLLECTION_NAME
)

print("Connected to WeatherGPT knowledge database!")


# ==========================================
# SEARCH KNOWLEDGE
# ==========================================

def search_knowledge(
    question: str,
    number_of_results: int = 3
):

    # Convert question into embedding
    question_embedding = model.encode(
        [question]
    ).tolist()

    # Search ChromaDB
    results = collection.query(
        query_embeddings=question_embedding,
        n_results=number_of_results
    )

    return results


# ==========================================
# DISPLAY RESULTS
# ==========================================

def display_results(results):

    print("\n======================================")
    print("       RELEVANT KNOWLEDGE")
    print("======================================")

    documents = results.get("documents", [[]])[0]

    metadatas = results.get("metadatas", [[]])[0]

    if not documents:

        print("\nNo relevant information found.")

        return

    for i, document in enumerate(documents):

        print(f"\n--- Result {i + 1} ---")

        print("\nCategory:")
        print(metadatas[i].get("category"))

        print("\nSource:")
        print(metadatas[i].get("source"))

        print("\nKnowledge:")
        print(document)

    print("\n======================================")


# ==========================================
# MAIN PROGRAM
# ==========================================

if __name__ == "__main__":

    print("\n======================================")
    print("      WeatherGPT RAG Retriever")
    print("======================================")

    print("\nType 'exit' to stop.")

    while True:

        question = input(
            "\nEnter your weather question: "
        )

        if question.lower().strip() == "exit":

            print("\nRetriever stopped.")

            break

        if not question.strip():

            print("\nPlease enter a question.")

            continue

        try:

            results = search_knowledge(
                question,
                number_of_results=3
            )

            display_results(results)

        except Exception as e:

            print("\nERROR:")
            print(e)