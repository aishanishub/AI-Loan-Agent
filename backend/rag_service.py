# loan_agent/backend/rag_service.py
import semantic_kernel as sk
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader
import config

class RAGService:
    def __init__(self, kernel: sk.Kernel):
        self._kernel = kernel
        self._client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
        
        # --- Configure ChromaDB's embedding function to use the proxy ---
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=config.OPENAI_API_KEY,
            model_name=config.EMBEDDING_MODEL,
            api_base=config.OPENAI_BASE_URL,  # <-- Add this line
        )

        self._collection = self._client.get_or_create_collection(
            name=config.CHROMA_COLLECTION_NAME,
            embedding_function=openai_ef
        )

    # The rest of the RAGService class remains exactly the same
    def setup_rag(self, pdf_path: str):
        """Indexes the PDF document if not already indexed."""
        if self._collection.count() > 0:
            print("RAG collection is already set up.")
            return

        print("Setting up RAG collection...")
        reader = PdfReader(pdf_path)
        chunks = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                paragraphs = text.split('\n\n')
                for j, p in enumerate(paragraphs):
                    if len(p.strip()) > 50:
                        chunks.append({"id": f"page_{i+1}_para_{j+1}", "text": p.strip()})

        print(f"Indexing {len(chunks)} chunks...")
        self._collection.add(
            documents=[chunk['text'] for chunk in chunks],
            ids=[chunk['id'] for chunk in chunks]
        )
        print("RAG setup complete.")

    async def query(self, user_query: str, n_results: int = 3) -> str:
        """Queries the vector DB and returns the most relevant chunks."""
        results = self._collection.query(
            query_texts=[user_query],
            n_results=n_results
        )
        return "\n---\n".join(results['documents'][0])