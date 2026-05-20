# CS5100 Smart Study Assistant

AI-based study assistant project for CS5100 (Intro to AI). The app combines a React/Vite frontend with an Express/TypeScript backend, Qdrant vector storage, local FastEmbed embeddings, and either Gemini or OpenAI for chat completion.

## Features

- Account-based chat history with session authentication.
- Normal chat mode and RAG-backed study mode.
- JSONL document upload with chunking, embedding, similarity search, and citations.
- Streaming responses over server-sent events.
- Provider fallback between Gemini and OpenAI when API keys are configured.

## Repository Notes

This public coursework copy intentionally excludes `.env` files, uploaded documents, embedding caches, build outputs, and the original local textbook-derived JSONL/PDF materials. To test RAG mode, prepare your own JSONL file with one document chunk per line:

```jsonl
{"title":"Sample Notes","author":"Course Staff","page":1,"content":"This is a short passage to retrieve from."}
```

## Local Setup

1. Start Qdrant:

```bash
docker run -p 6333:6333 qdrant/qdrant
```

2. Install dependencies:

```bash
cd frontend
npm install

cd ../backend
npm install
```

3. Create `backend/.env` from `backend/.env.example` and add at least one AI provider key.

4. Run the backend:

```bash
cd backend
npm run dev
```

5. In another terminal, run the frontend:

```bash
cd frontend
npm run dev
```

## Environment

Required for normal operation:

```env
SESSION_SECRET=<long-random-session-secret>
GEMINI_API_KEY=<gemini-api-key>
OPENAI_API_KEY=<openai-api-key>
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

At least one of `GEMINI_API_KEY` or `OPENAI_API_KEY` is required for model responses. `ENABLE_DEMO_USER=true` can be used during local demos, but production deployments should create user accounts through the signup flow.
