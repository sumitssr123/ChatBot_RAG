# Simple RAG Chatbot 📄🤖

[![Live Demo](https://img.shields.io/badge/Demo-Live%20on%20Render-blue)](https://chatbot-suni.onrender.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev)
[![FAISS](https://img.shields.io/badge/FAISS-Vector%20Search-orange.svg)](https://github.com/facebookresearch/faiss)
[![Gemini](https://img.shields.io/badge/Google-Gemini%20API-4285F4.svg)](https://ai.google.dev)

A minimalist, beginner-friendly **Retrieval-Augmented Generation (RAG)** chatbot built with **FastAPI**, **React.js**, **FAISS**, and **Google Gemini**.

Designed specifically to be simple to read, easy to run, and straightforward to explain in an interview.

---

## 🏗️ Architecture & How It Works

```text
1. PDF Upload ────► Extract Text (pypdf) ────► Sliding Window Chunker
                                                       │
                                                       ▼
2. User Question ──► Gemini Embedding ──► FAISS Index (Vector Search)
                             │                         │
                             ▼                         ▼
                      Embedded Query ────────► Top 3 Matching Chunks
                                                       │
                                                       ▼
                                             Gemini 2.5 Flash
                                             (Prompt with context)
                                                       │
                                                       ▼
                                                 Final Answer
```

### The 6 RAG Steps Explained (Interview Ready)

1. **Extraction**: `pypdf` extracts raw text page-by-page from the uploaded PDF document.
2. **Chunking**: A clean sliding-window function splits the text into chunks of 500 characters with 100 characters of overlap (preserving contextual meaning across boundaries).
3. **Embeddings**: Each text chunk is converted into high-dimensional semantic vector embeddings using Google's `gemini-embedding-001` model.
4. **Vector Store**: The embeddings are loaded into a `faiss.IndexFlatL2` vector index for fast similarity lookup.
5. **Retrieval**: When the user asks a question, the question is embedded and FAISS retrieves the top 3 nearest text chunks.
6. **Generation**: The retrieved chunks are formatted into a strict system prompt and passed to `gemini-2.5-flash`. If the answer is not in the context, Gemini replies:
   > *"I couldn't find this information in the uploaded document."*

---

## 🔌 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/upload` | Upload PDF file (`multipart/form-data`, max 15MB), chunk & index embeddings |
| `POST` | `/chat` | Query RAG pipeline with `{"question": "..."}` and get grounded answer |
| `POST` | `/clear` | Clear currently loaded document and reset FAISS vector index |
| `GET` | `/health` | Health check endpoint returning status, version, and indexed chunk metrics |

---

## ✨ Features

- **Document Ingestion**: Fast extraction using `pypdf` with validation for empty files and 15MB file size limits.
- **Smart Chunking**: 500-character chunks with 100-character sliding overlap for smooth context boundaries.
- **Vector Search**: In-memory `faiss.IndexFlatL2` similarity search with Google Gemini embeddings.
- **Context-Strict Generation**: Zero hallucination answers grounded directly in document content.
- **Modern React Interface**: Includes active document badge, prompt suggestion chips, and clear chat actions.
- **Production Ready**: Configured for Render deployment via `render.yaml` blueprint.

---

## 📁 Project Structure

```text
simple-rag-chatbot/
│
├── backend/
│   ├── main.py              # FastAPI endpoints (/upload, /chat, /clear, /health)
│   ├── rag.py               # RAG logic (PDF extraction, chunking, FAISS, Gemini)
│   ├── requirements.txt     # Python backend dependencies
│   └── uploads/             # Temporary storage for uploaded PDFs
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # React UI (file upload, chips, chat interface)
│   │   ├── App.css          # Minimal, clean CSS styling
│   │   └── main.jsx         # React entry point
│   ├── index.html           # HTML template
│   ├── package.json         # Frontend dependencies (React + Vite)
│   └── vite.config.js       # Vite configuration
│
├── render.yaml              # Render Blueprint specification (backend + static frontend)
├── .env.example             # Template for API keys
├── .gitignore
└── README.md
```

---

## 🚀 Quickstart Guide

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- A **Google Gemini API Key** (Get a free key at [Google AI Studio](https://aistudio.google.com/))

---

### Step 1: Configure Environment (.env)

In the `simple-rag-chatbot/` directory, create a `.env` file (or copy from `.env.example`):

```bash
cp .env.example .env
```

Open `.env` and add your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

---

### Step 2: Run the Backend (FastAPI)

1. Open a terminal and navigate to the backend folder:
   ```bash
   cd backend
   ```

2. (Optional but recommended) Create and activate a virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

The backend will be running at `http://127.0.0.1:8000`. You can view interactive Swagger docs at `http://127.0.0.1:8000/docs`.

---

### Step 3: Run the Frontend (React + Vite)

1. Open a second terminal and navigate to the frontend folder:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```

4. Open your browser at `http://localhost:5173`.

---

## 🎯 How to Use

1. Click **Choose PDF** to upload any PDF document (e.g. an article, resume, or report).
2. Wait a few seconds for the document to be chunked and indexed into FAISS.
3. Click a **prompt chip** or type a custom question in the chat input and hit **Send**.
4. The chatbot retrieves the relevant sections from your PDF and answers accurately using Gemini!
5. If you ask something not present in the document, it will correctly reply that the information cannot be found.
6. Use **Clear Chat** or the document reset button (✕) to start fresh anytime.

---

## 💡 Quick Interview Cheat Sheet

| Question | Simple Explanation |
| :--- | :--- |
| **Why chunk text?** | LLMs have context limits and embedding an entire 50-page document produces poor semantic resolution. Chunking isolates specific concepts. |
| **Why overlap chunks?** | Overlap (e.g. 100 characters) prevents sentences or ideas from being cut in half at chunk boundaries. |
| **Why FAISS?** | FAISS (Facebook AI Similarity Search) is an ultra-fast, lightweight in-memory vector index that does exact or approximate nearest neighbor search with zero database overhead. |
| **How to prevent hallucinations?** | By constraining the system prompt with: *"Answer ONLY based on the context. If not present, reply 'I couldn't find this information in the uploaded document.'"* |

---

## 🌐 Live Demo & Deployment

- **Live URL**: [https://chatbot-suni.onrender.com](https://chatbot-suni.onrender.com)
- **Deployment**: Configured for Render deployment via [`render.yaml`](render.yaml) blueprint.
