import os
import faiss
import numpy as np
from pypdf import PdfReader
from google import genai
from google.genai import errors


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract plain text from an uploaded PDF file."""
    reader = PdfReader(pdf_path)
    full_text = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            full_text.append(page_text)
    return "\n".join(full_text)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """
    Split text into overlapping chunks.
    Simple sliding-window approach that is easy to explain and understand.
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


# Recommended embedding and LLM models with automatic fallback
CANDIDATE_EMBEDDING_MODELS = [
    "gemini-embedding-001",
    "gemini-embedding-2",
]

CANDIDATE_LLM_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-3.8-flash",
]


class SimpleRAG:
    """
    Minimal RAG engine:
    1. Extracts text from PDF
    2. Chunks text
    3. Generates embeddings using Gemini embedding models
    4. Indexes embeddings in FAISS
    5. Retrieves top relevant chunks for a question
    6. Prompts Gemini with strict context
    """

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.embedding_model = os.getenv("EMBEDDING_MODEL", CANDIDATE_EMBEDDING_MODELS[0])
        self.llm_model = os.getenv("GEMINI_MODEL", CANDIDATE_LLM_MODELS[0])
        self.chunks: list[str] = []
        self.index: faiss.IndexFlatL2 | None = None

    def _ensure_client(self):
        """Ensure Gemini client is initialized with an API key."""
        if self.client is None:
            key = self.api_key or os.getenv("GEMINI_API_KEY", "")
            if not key:
                raise ValueError("GEMINI_API_KEY is not set. Please set it in your .env file.")
            self.api_key = key
            self.client = genai.Client(api_key=key)

    def get_embeddings(self, texts: list[str]) -> np.ndarray:
        """Call Gemini embedding API and return float32 numpy array with fallback."""
        self._ensure_client()

        models_to_try = [self.embedding_model] + [
            m for m in CANDIDATE_EMBEDDING_MODELS if m != self.embedding_model
        ]

        last_error = None
        for model_name in models_to_try:
            try:
                all_embeddings = []
                batch_size = 50

                for i in range(0, len(texts), batch_size):
                    batch = texts[i : i + batch_size]
                    response = self.client.models.embed_content(
                        model=model_name,
                        contents=batch,
                    )
                    for item in response.embeddings:
                        all_embeddings.append(item.values)

                # Save successful model for subsequent calls
                self.embedding_model = model_name
                return np.array(all_embeddings, dtype=np.float32)

            except Exception as e:
                last_error = e
                print(f"[RAG] Embedding model '{model_name}' failed: {e}. Trying fallback...")
                continue

        raise RuntimeError(f"All embedding models failed. Last error: {last_error}")

    def process_pdf(self, pdf_path: str) -> int:
        """Process a PDF and build the FAISS vector index. Returns number of chunks."""
        # 1. Extract text
        raw_text = extract_text_from_pdf(pdf_path)
        if not raw_text.strip():
            raise ValueError("The uploaded PDF does not contain extractable text.")

        # 2. Split into chunks
        self.chunks = chunk_text(raw_text, chunk_size=500, overlap=100)
        if not self.chunks:
            raise ValueError("Could not create any text chunks from the PDF.")

        # 3. Create embeddings
        embeddings = self.get_embeddings(self.chunks)

        # 4. Store in FAISS
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)

        return len(self.chunks)

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        """Search FAISS for the most relevant text chunks."""
        if self.index is None or len(self.chunks) == 0:
            return []

        # Embed the search query
        query_embedding = self.get_embeddings([query])

        # Search top-k nearest neighbors
        k = min(top_k, len(self.chunks))
        distances, indices = self.index.search(query_embedding, k)

        # Collect retrieved chunks
        retrieved_chunks = [self.chunks[idx] for idx in indices[0] if idx != -1]
        return retrieved_chunks

    def answer_question(self, question: str) -> str:
        """Generate an answer using retrieved chunks as strict context with fallback."""
        if self.index is None or len(self.chunks) == 0:
            return "Please upload a PDF document first."

        self._ensure_client()

        # Retrieve relevant chunks
        relevant_chunks = self.retrieve(question, top_k=3)
        context = "\n---\n".join(relevant_chunks)

        # Strict anti-hallucination prompt
        prompt = f"""You are a helpful assistant answering questions about an uploaded document.
Answer the user's question using ONLY the provided context below.
If the answer cannot be found in the context, reply EXACTLY with:
"I couldn't find this information in the uploaded document."

Do not assume or make up any facts outside this context.

Context:
{context}

Question:
{question}
"""

        models_to_try = [self.llm_model] + [
            m for m in CANDIDATE_LLM_MODELS if m != self.llm_model
        ]

        last_error = None
        for model_name in models_to_try:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                self.llm_model = model_name
                return response.text.strip()
            except Exception as e:
                last_error = e
                print(f"[RAG] LLM model '{model_name}' failed: {e}. Trying fallback...")
                continue

        raise RuntimeError(f"All generative models failed. Last error: {last_error}")
