<img src="frontend/public/favicon.svg" width="64" height="64" alt="Daleel AI logo" />

# Daleel AI

[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-0ea5e9?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![shadcn/ui](https://img.shields.io/badge/shadcn%2Fui-000000?style=for-the-badge&logo=shadcnui&logoColor=white)](https://ui.shadcn.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)
[![Pinecone](https://img.shields.io/badge/Pinecone-000000?style=for-the-badge&logo=pinecone&logoColor=white)](https://pinecone.io/)
[![Cohere](https://img.shields.io/badge/Cohere-D97757?style=for-the-badge&logo=cohere&logoColor=white)](https://cohere.com/)

---

## About

I use [IslamQA](https://islamqa.info) regularly for Islamic rulings and guidance. The problem: finding a precise answer is slow. A single topic can have multiple overlapping Q&As, answers are often long without a summary, and you end up reading through several pages just to find what you need.

I built Daleel AI to fix that — ask a question in plain English and get a direct, summarised answer with the relevant sources cited. No browsing, no skimming.

It was also a hands-on project to properly learn RAG end-to-end, built by [Mubashir](https://github.com/Mubashir21).

**Live demo:** [islamic-rag-ten.vercel.app](https://islamic-rag-ten.vercel.app)

---

## How It Works

This is not a standard RAG pipeline. Daleel AI uses an agentic architecture that decides what to do with each message rather than blindly retrieving on every query:

1. **Router** — a fast LLM call classifies the message: does it need new Islamic sources, can it be answered from conversation context, or is it out of scope?
2. **Hybrid retrieval** — when retrieval is needed, the question is embedded and matched against ~39,000 IslamQA chunks using both dense vector search (OpenAI embeddings) and sparse keyword search (BM25), with query rewriting for follow-up questions
3. **Reranking** — top 40 candidates are reranked by Cohere's reranking model to surface the 5 most relevant passages
4. **Generation** — gpt-5.6-terra generates a grounded answer using only the retrieved sources, strictly instructed to cite every claim and say "I could not find a clear answer" rather than hallucinate
5. **Streaming** — the answer streams back token by token via SSE with live status updates; the `### Sources` block is parsed client-side and rendered as links

Conversation context is maintained per session with a 6-message sliding window. Follow-ups like "explain that more simply" skip retrieval entirely and reuse cached chunks from the previous turn.

---

## Stack

| Layer         | Technology                                       |
| ------------- | ------------------------------------------------ |
| Frontend      | React + Vite, Tailwind CSS v4, shadcn/ui         |
| Backend       | FastAPI, Python                                  |
| Embeddings    | OpenAI `text-embedding-3-large` (3072 dims)      |
| Vector DB     | Pinecone (serverless, hybrid index)              |
| Sparse search | BM25 via `pinecone-text`                         |
| Reranking     | Cohere `rerank-v4.0-pro`                         |
| Router        | OpenAI `gpt-5.6-luna` (intent classification)    |
| Generation    | OpenAI `gpt-5.6-terra`                           |

---

## Project Structure

```
daleel-ai/
├── ingestion/              # Async scraper for IslamQA
│   ├── pipeline.py
│   ├── parser.py
│   ├── io.py
│   └── run_ingestion.py
│
├── processing/             # Data processing pipelines
│   ├── chunker.py          # Paragraph-aware chunking
│   ├── embedder.py         # OpenAI batch embedder
│   ├── run_chunking.py
│   └── run_embeddings.py
│
├── backend/app/            # FastAPI backend
│   ├── main.py
│   ├── api/routes.py       # /chat/stream endpoint
│   ├── core/
│   │   ├── config.py       # Centralised settings
│   │   └── session_store.py # In-memory sessions with TTL
│   ├── rag/                # Agentic RAG pipeline
│   │   ├── orchestrator.py  # Main control flow
│   │   ├── router.py        # Intent classification
│   │   ├── conversation.py  # Per-session state
│   │   ├── retriever.py
│   │   ├── generator.py
│   │   └── prompt_builder.py
│   ├── retrieval/          # Search implementations
│   │   ├── dense.py
│   │   ├── sparse.py
│   │   ├── hybrid.py
│   │   └── reranker.py
│   ├── db/                 # Pinecone client + setup
│   └── schemas/query.py
│
├── backend/evals/          # Manual regression evals (false premises, corrections, follow-ups)
│   └── run_chat_evals.py
│
├── frontend/               # React frontend
│   └── src/
│       ├── components/
│       └── lib/api.js
│
├── artifacts/
│   └── bm25_encoder.pkl    # Fitted BM25 encoder
│
└── data/                   # (gitignored) raw + processed data
```

---

## Setup

### 1. Clone

```bash
git clone https://github.com/Mubashir21/islamic-rag.git
cd islamic-rag
```

### 2. Install backend dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Configure environment variables

Create a `.env` file at the root:

```env
OPENAI_API_KEY=
PINECONE_API_KEY=
COHERE_API_KEY=

PINECONE_INDEX_NAME=islamic-rag-hybrid
PINECONE_NAMESPACE=islamic-rag-v1

OPENAI_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_GENERATION_MODEL=gpt-5.6-terra
OPENAI_ROUTER_MODEL=gpt-5.6-luna
COHERE_RERANK_MODEL=rerank-v4.0-pro
COHERE_RERANK_TIMEOUT=5   # seconds; on timeout/error, falls back to hybrid search order

RETRIEVAL_K=40
FINAL_K=5
HYBRID_ALPHA=0.8

FRONTEND_URL=http://localhost:5173
```

### 4. Run the data pipeline (first time only)

```bash
# Scrape IslamQA
python ingestion/run_ingestion.py

# Chunk the raw data
python processing/run_chunking.py

# Embed the chunks
python processing/run_embeddings.py

# Upload to Pinecone
python backend/app/db/upsert_vectors.py
```

### 5. Start the backend

```bash
uvicorn backend.app.main:app --reload
```

### 6. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Evals

`backend/evals/run_chat_evals.py` runs a handful of tricky multi-turn conversations (impossible premises like "fasting Ramadan during Hajj", user corrections, follow-ups, out-of-scope) through the full pipeline and prints the route, retrieved sources and answer for manual review. Run it after changing any prompt:

```bash
python backend/evals/run_chat_evals.py               # all cases
python backend/evals/run_chat_evals.py hajj_ramadan  # one case
```

---

## API

| Method | Endpoint        | Description                          |
| ------ | --------------- | ------------------------------------ |
| POST   | `/chat/stream`  | Agentic chat with SSE status events  |
| POST   | `/query/stream` | Legacy single-turn streaming         |
| GET    | `/health`       | Health check                         |

**Request body (`/chat/stream`):**

```json
{ "message": "What is the ruling on combining prayers while travelling?", "session_id": null }
```

**SSE event types:**

```
event: session   → {"session_id": "..."}
event: status    → {"message": "Searching Islamic sources..."}
event: token     → {"text": "..."}
event: done      → {}
```

---

## Data

- ~15,000 IslamQA questions and answers scraped
- ~39,000 chunks after paragraph-aware splitting
- Chunks include title, question, URL and source metadata

---

## Roadmap

- [ ] Cron job to automatically fetch new and updated IslamQA content
- [ ] Tools: gold/silver price and currency exchange for zakat calculations

---

## Disclaimer

This tool is a personal project. Answers are AI-generated summaries of IslamQA content and may be incomplete or incorrect. Always verify with a qualified Islamic scholar.

---

## Acknowledgements

- [IslamQA](https://islamqa.info) for the source content
- [OpenAI](https://openai.com) for embeddings and generation
- [Pinecone](https://pinecone.io) for vector search
- [Cohere](https://cohere.com) for reranking
