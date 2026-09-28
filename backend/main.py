import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag import SimpleRAG

# Load environment variables from .env file (check backend/.env or root .env)
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent / ".env")

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("WARNING: GEMINI_API_KEY is not set. Please set it in your .env file.")

# Initialize FastAPI app
app = FastAPI(title="Simple RAG Chatbot API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Upload directory
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Initialize RAG engine instance
rag_engine = SimpleRAG(api_key=api_key or "")


class ChatRequest(BaseModel):
    question: str


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    1. Receive PDF file
    2. Save temporarily to uploads/
    3. Extract text, split into chunks, embed, and index with FAISS
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Save uploaded file
    file_path = UPLOAD_DIR / file.filename
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Refresh API key if it was updated in environment
        current_key = os.getenv("GEMINI_API_KEY")
        if not current_key:
            raise HTTPException(
                status_code=500,
                detail="GEMINI_API_KEY is missing. Please add it to your .env file."
            )
        rag_engine.api_key = current_key
        rag_engine.client = None

        # Build index from PDF
        chunks_count = rag_engine.process_pdf(str(file_path))

        return {
            "message": "File processed and indexed successfully!",
            "filename": file.filename,
            "chunks_count": chunks_count,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    1. Receive user question
    2. Retrieve top matching chunks from FAISS
    3. Query Gemini with the strict context
    4. Return the answer
    """
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        answer = rag_engine.answer_question(question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
