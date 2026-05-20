# CS5610 Final Project - Smart Study Assistant

Team web development project archived locally for CS5610.

This project is a full-stack Retrieval-Augmented Generation (RAG) chat application that combines document retrieval with AI-powered responses. Users can upload documents and receive AI responses grounded in their uploaded content with citation support. The project allows users to switch between two interaction modes:
* **Normal mode**: Application runs in normal chat mode, LLM works as a simple chatbot.
* **Professional mode**: Application runs in professional mode, LLM works as a RAG chatbot.
---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Features](#features)
3. [Local Setup](#local-setup)
4. [Environment Variables](#environment-variables)
5. [API Documentation](#api-documentation)
6. [Database Schema](#database-schema)
7. [User Persona & Story](#user-persona--story)
8. [AI Integration](#ai-integration)
9. [Deployment](#deployment)

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS |
| **Backend** | Express.js, TypeScript, Node.js |
| **Database** | Qdrant (Vector Database) |
| **AI Providers** | Google Gemini, OpenAI GPT |
| **Embeddings** | FastEmbed (BGE-Small-EN-v1.5) |
| **Authentication** | express-session, bcrypt |
| **Styling** | Tailwind CSS, Lucide Icons |
| **Markdown** | react-markdown, remark-gfm, rehype-raw |

---

## Features

- **Dual AI Provider Support**: Switch between Google Gemini and OpenAI models
- **RAG Mode**: Ground AI responses in uploaded documents with inline citations
- **Real-time Streaming**: Server-sent events for streaming AI responses
- **Document Management**: Upload, store, and search documents with vector embeddings
- **User Authentication**: Secure signup/signin with session management
- **Chat History**: Persistent chat storage with preview snippets
- **Configurable RAG Parameters**: Adjust Top-K results and similarity thresholds
- **Responsive UI**: Mobile-friendly design with collapsible sidebars
- **Citation Reference**: View source document information and similarity scores for AI responses

---

## Local Setup

### Prerequisites

- Node.js 18+
- npm
- Docker (for Qdrant)

### Installation

1. **Deploy local [Qdrant](https://qdrant.tech/documentation/quickstart/) service via [Docker](https://hub.docker.com/r/qdrant/qdrant)**
    ```bash
    docker pull qdrant/qdrant
    ```

2. **Start Qdrant (Docker)**
    ```bash
    docker run -p 6333:6333 qdrant/qdrant
    ```
   > Qdrant GUI available at `http://localhost:6333/dashboard#/collections`

3. **Clone the repository**
    ```bash
    git clone <repository-url>
    cd <final-project-root>
    ```

4. **Install dependencies**
    ```bash
    cd ./frontend
    npm install
    ```
    ```bash
    cd ./backend
    npm install
    ```

5. **Build the frontend**
    ```bash
    cd ./frontend
    npm run build
    ```

6. **Build the backend**
    ```bash
    cd ./backend
    npx tsc
    ```
    > `server.js` should appear in `./backend/dist/` after compilation.

7. **Copy frontend build to backend**
    ```bash
    cp -r ./frontend/dist/* ./backend/dist/
    ```
8. **Setup `.env`**
    ```bash
    touch .env
    ```
    Add environment variables to `.env`
    ```dotenv
    PORT=5500
    OPENAI_API_KEY=<openai-api-key>
    GEMINI_API_KEY=<gemini-api-key>
    ```

8. **Start the server**
    ```bash
    cd ./backend
    node ./dist/server.js
    ```

9. **Access the application**
    Open `http://localhost:5500` in browser

### Document Upload Sample

The original local JSONL/PDF study materials are intentionally omitted from this public archive. To test RAG mode, upload a JSONL file with one document chunk per line:

```jsonl
{"title":"Sample Notes","author":"Course Staff","page":1,"content":"This is a short passage to retrieve from."}
```
---

## Environment Variables

Create a `.env` file in the project root:

```env
# Server Configuration
HOST=0.0.0.0
PORT=5500
STATIC_DIR=./dist
SESSION_SECRET=<long-random-session-secret>

# AI Provider Keys (at least one required)
GEMINI_API_KEY=<gemini-api-key>
GEMINI_MODEL=gemini-2.0-flash-exp

OPENAI_API_KEY=<openai-api-key>
OPENAI_MODEL=gpt-4o-mini

# Qdrant Vector Database
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Embedding Model Cache
EMBEDDING_CACHE_DIR=./.cache/embeddings
```

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | One of Gemini/OpenAI | Google AI API key |
| `OPENAI_API_KEY` | One of Gemini/OpenAI | OpenAI API key |
| `QDRANT_HOST` | Yes | Qdrant server hostname |
| `QDRANT_PORT` | Yes | Qdrant server port |
| `SESSION_SECRET` | Yes | Secret for session encryption |

---

## API Documentation

### Authentication Endpoints

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|--------------|
| `POST` | `/api/auth/signup` | Create new account | `{ username, password }` |
| `POST` | `/api/auth/signin` | Sign in user | `{ username, password }` |
| `POST` | `/api/auth/signout` | Sign out user | - |
| `GET` | `/api/auth/me` | Get current user | - |

### Chat Endpoints

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|--------------|
| `GET` | `/api/chats` | List user's chats | - |
| `POST` | `/api/chats` | Create new chat | `{ settings }` |
| `GET` | `/api/chats/:chatId` | Get chat by ID | - |
| `PATCH` | `/api/chats/:chatId` | Update chat | `{ settings?, messages? }` |
| `DELETE` | `/api/chats/:chatId` | Delete chat | - |
| `POST` | `/api/chats/:chatId/stream` | Stream AI response | `{ userPrompt, settings }` |

### Document Endpoints

| Method | Endpoint | Description | Request Body |
|--------|----------|-------------|--------------|
| `GET` | `/api/documents/count` | Get document count | - |
| `POST` | `/api/documents/upload` | Upload documents | `multipart/form-data` |
| `DELETE` | `/api/documents/delete` | Delete all user docs | - |

### Chat Settings Schema

```json
{
  "professionalMode": true,
  "topK": 5,
  "similarityThreshold": 0.6
}
```

### Stream Response Format (SSE)

```
data: {"type": "references", "references": [...]}
data: {"type": "content", "text": "..."}
data: {"type": "error", "message": "..."}
data: [DONE]
```

---

## Database Schema

The application uses Qdrant, a vector database optimized for similarity search. Qdrant collections can also store metadata for each vector, which is used to retrieve the original document content when generating citations. Each collection also support indexing for faster read operations.

Alhough Qdrant is not a relational database, the application's database schema is based on the Entity-Relationship Diagram:
> NOTE: `USERS` and `CHATS` stores dummy embedding vectors for consistency. This also allows for future integration with other features that might involve similarity search on user info or chat history.
```
┌─────────────────────────────────────────────────────────────────────────┐
│                           QDRANT COLLECTIONS                            │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     USERS       │       │     CHATS       │       │   DOCUMENTS     │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ userId (PK)     │──┐    │ chatId (PK)     │       │ docId (PK)      │
│ username        │  │    │ userId (FK) ────│───────│ userId (FK) ────│───┐
│ passwordHash    │  └────│─────────────────│       │ srcId           │   │
│ createdAt       │       │ messages[]      │       │ title           │   │
│ vector[384]     │       │ preview         │       │ author          │   │
└─────────────────┘       │ settings        │       │ page            │   │
                          │ createdAt       │       │ content         │   │
                          │ updatedAt       │       │ createdAt       │   │
                          │ vector[384]     │       │ vector[384]     │   │
                          └─────────────────┘       └─────────────────┘   │
                                                                          │
                                    ┌─────────────────────────────────────┘
                                    │
                                    ▼
                          ONE USER → MANY CHATS
                          ONE USER → MANY DOCUMENTS
                          (One-to-Many Relationships)
```

### Collection Schemas

**Users Collection**
| Field | Type | Indexed | Description |
|-------|------|---------|-------------|
| userId | UUID | Primary | Unique identifier |
| username | string | keyword | Lowercase username |
| passwordHash | string | - | bcrypt hash |
| createdAt | ISO string | - | Account creation time |

**Chats Collection**
| Field | Type | Indexed | Description |
|-------|------|---------|-------------|
| chatId | UUID | Primary | Unique identifier |
| userId | UUID | keyword | Owner reference |
| messages | Message[] | - | Chat history |
| preview | string | - | First 50 chars of first message |
| settings | ChatSettings | - | RAG configuration |
| createdAt | ISO string | - | Timestamps |
| updatedAt | ISO string | - | Timestamps |

**Documents Collection**
| Field | Type | Indexed | Description |
|-------|------|---------|-------------|
| docId | UUID | Primary | Unique chunk identifier |
| srcId | UUID | - | Source file identifier |
| userId | UUID | keyword | Owner reference |
| title | string | text | Document title |
| author | string | keyword | Document author |
| page | number | - | Source page number |
| content | string | - | Text chunk content |
| vector | float[384] | HNSW | BGE embedding |

---

## User Persona & Story

### Persona 1: Graduate Student (Research-Focused)

**Name**: Demo
**Background**: MS student in Computer Science researching Machine Learning
**Goals**: Quickly find relevant information in local knowledge based derived from various sources, get cited answers

**User Stories**:
- I want to create a personal knowledge base for my own study so I can search across them simultaneously.
- I want to see similarity scores so I can judge the relevance of sources.
- I want inline citations (e.g., [1][2]) so I can verify AI claims against original sources.
- I want to adjust the top K and similarity threshold so I can control answer precision.

---

## AI Integration

### Dual Provider Architecture

The application supports two AI providers with automatic fallback:

```
┌─────────────────┐     ┌─────────────────┐
│  Google Gemini  │     │    OpenAI       │
│  (Primary)      │     │  (Fallback)     │
├─────────────────┤     ├─────────────────┤
│ gemini-2.0-     │     │ gpt-4o-mini     │
│ flash-exp       │     │                 │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
              ┌──────▼──────┐
              │ Stream API  │
              │   Router    │
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │    SSE      │
              │  Response   │
              └─────────────┘
```

### RAG Pipeline

1. **Query Embedding**: User query → BGE-Small-EN-v1.5 → 384-dim vector
2. **Similarity Search**: Vector → Qdrant cosine search → Top-K documents
3. **Context Injection**: Retrieved documents appended to prompt
4. **System Prompting**: Mode-specific instructions for citation behavior
5. **Streaming Generation**: AI response with inline [1][2] citations

### System Prompts

**RAG Mode (with references)**:
```
You are a RAG assistant. ONLY use information from the references.
Cite sources using [1], [2], etc. If references aren't relevant,
say "I don't have enough relevant information."
```

**RAG Mode (no references found)**:
```
No relevant documents were found. Respond with the default message
explaining the user should upload documents or adjust settings.
```

**Standard Mode**:
```
You are a helpful AI assistant. Provide clear and accurate responses.
```

---

## Deployment

### Recommended Platforms

| Component | Platform | Notes |
|-----------|----------|-------|
| Frontend + Backend | Google Cloud VM | Serve one public endpoint|
| Vector Database | Google Cloud VM | Same VM|

### Deployment Checklist

- Check if CORS is disabled in the backend
- Build frontend assets and place them in the `dist/` directory
- Create Google Cloud VM
- Set up `Firewall` rules to allow traffic to the correct host port (backend port and Qdrant service port if necessary)
- Deploy `Docker` container for `Qdrant` on the VM
- Use `scp` to copy project directory to the VM
- Install dependencies and build the project
- Setup `.env` file with necessary environment variables
- Start the backend server and verify it's running (or use `systemctl` to create daemon)

### Public URL

> http://34.121.30.101:5500

---
