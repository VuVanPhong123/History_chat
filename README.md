# History Chat — Vietnamese History AI Chatbot & Quiz Generator

History Chat is an AI-powered learning application for Vietnamese history. The system allows users to chat with an AI assistant about Vietnamese history and generate multiple-choice history quizzes based on selected historical periods.

The project combines a web application, a FastAPI proxy backend, Retrieval-Augmented Generation (RAG), FAISS vector search artifacts, fine-tuned language model workflows, and Kaggle/ngrok-based AI worker serving.

## Features

### AI History Chat

* Ask natural language questions about Vietnamese history.
* Receive streamed AI responses in real time.
* Maintain chat sessions through the backend database.
* Forward user questions to external AI chat workers.
* Store user and assistant messages for later session continuity.

### AI Quiz Generator

* Generate multiple-choice quizzes about Vietnamese history.
* Select one or multiple historical topic ranges.
* Choose quiz size: 10, 20, 30, or 40 questions.
* Stream quiz generation progress from backend to frontend.
* Generate questions in parallel using one or more quiz worker URLs.
* Return question, answer options, correct answer, explanation, source context, and source ID.

### Retrieval-Augmented Generation Support

* Load historical knowledge chunks from a local `rag.jsonl` file.
* Use source IDs returned by the AI worker to map generated quiz questions back to supporting context.
* Store FAISS and metadata artifacts under `vectorDB`.

### Fine-tuning and Model Workflow

* Includes notebook-based workflows for model fine-tuning and evaluation.
* Separate model workflow directories for answer generation and quiz generation.
* Kaggle notebooks are used to deploy model workers for chat and quiz generation.

## Project Structure

```text
History_chat/
├── app/
│   ├── BE/
│   │   ├── app/
│   │   │   ├── core/
│   │   │   │   ├── rag_store.py
│   │   │   │   └── worker_manager.py
│   │   │   ├── routers/
│   │   │   │   ├── auth.py
│   │   │   │   ├── admin.py
│   │   │   │   ├── chat.py
│   │   │   │   └── quiz.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── main.py
│   │   │   ├── crud.py
│   │   │   ├── schemas.py
│   │   │   └── auth.py
│   │   ├── data/
│   │   ├── .env.example
│   │   ├── requirements.txt
│   │   └── run.py
│   │
│   └── frontend-history/
│       ├── src/
│       │   ├── components/
│       │   │   ├── Chat/
│       │   │   └── Quiz/
│       │   ├── pages/
│       │   │   ├── index.jsx
│       │   │   └── quiz.jsx
│       │   └── services/
│       ├── package.json
│       ├── tailwind.config.js
│       └── next.config.js
│
├── data/
│   ├── chat/
│   └── genQuiz/
│
├── finetune/
│   ├── evaluate/
│   ├── modelAnswer/
│   └── modelGenQuiz/
│
├── kaggle/
│   ├── deploy_kaggle_chat.ipynb
│   └── deploy_kaggle_genQuiz.ipynb
│
├── vectorDB/
│   ├── genDataRAG.ipynb
│   ├── vectordb.ipynb
│   ├── rag_index.faiss
│   └── rag_metadata.pkl
│
└── README.md
```

## Tech Stack

### Frontend

* Next.js 14
* React 18
* Tailwind CSS
* Axios
* React Hot Toast
* Streaming response handling with `fetch()` and `ReadableStream`

### Backend

* FastAPI
* Uvicorn
* SQLite
* SQLAlchemy
* Pydantic Settings
* JWT authentication
* HTTPX async client
* NDJSON streaming responses
* Optional ngrok tunnel support

### AI / RAG / Model Serving

* RAG data in JSONL format
* FAISS vector index
* Pickle metadata storage
* Kaggle notebooks for running AI workers
* Separate AI workers for chat and quiz generation
* Fine-tuning workflow notebooks for answer and quiz models

## System Architecture

```text
User
 │
 ▼
Next.js Frontend
 │
 ├── /                → Chat UI
 └── /quiz            → Quiz Generator UI
 │
 ▼
FastAPI Backend Proxy
 │
 ├── /api/chat        → streams chat response from chat worker
 ├── /api/quiz/generate
 │                    → streams quiz generation progress/results
 ├── /api/auth/login  → admin JWT login
 ├── /api/admin       → admin endpoints
 ├── /health          → health check
 └── /docs            → Swagger API docs
 │
 ▼
AI Worker URLs
 │
 ├── Chat worker      → /chat
 └── Quiz worker      → /generate_quiz
 │
 ▼
Fine-tuned LLM + RAG context
```

The backend acts as a proxy layer between the frontend and external AI workers. This design allows the heavy model inference process to run separately, for example on Kaggle notebooks exposed through ngrok, while the frontend and backend remain lightweight.

## Main User Flows

### 1. Chat Flow

```text
User enters a question
→ Frontend sends POST /api/chat
→ Backend creates or reuses a chat session
→ Backend forwards the question to a configured chat worker
→ Chat worker streams response chunks
→ Backend forwards chunks to frontend as NDJSON
→ Frontend renders the answer progressively
→ Backend stores the final assistant response
```

### 2. Quiz Generation Flow

```text
User selects topics and number of questions
→ Frontend sends POST /api/quiz/generate
→ Backend creates a quiz test record
→ Backend distributes generation work across configured quiz workers
→ Workers stream progress and generated questions
→ Backend merges the generated questions
→ Backend enriches each question with RAG context by source_id
→ Frontend displays the completed quiz
→ User selects answers and submits
→ Frontend calculates the score
```

## Historical Topic Ranges

The quiz generator supports 15 Vietnamese history topic ranges:

| ID | Topic                                                   |
| -: | ------------------------------------------------------- |
|  1 | Lịch Sử Việt Nam Tập 1: Từ khởi thủy đến thế kỷ X       |
|  2 | Lịch Sử Việt Nam Tập 2: Từ thế kỷ X đến thế kỷ XIV      |
|  3 | Lịch Sử Việt Nam Tập 3: Từ thế kỷ XV đến thế kỷ XVI     |
|  4 | Lịch Sử Việt Nam Tập 4: Từ thế kỷ XVII đến thế kỷ XVIII |
|  5 | Lịch Sử Việt Nam Tập 5: Từ năm 1802 đến năm 1858        |
|  6 | Lịch Sử Việt Nam Tập 6: Từ năm 1859 đến năm 1896        |
|  7 | Lịch Sử Việt Nam Tập 7: Từ năm 1897 đến năm 1918        |
|  8 | Lịch Sử Việt Nam Tập 8: Từ năm 1919 đến năm 1930        |
|  9 | Lịch Sử Việt Nam Tập 9: Từ năm 1930 đến năm 1945        |
| 10 | Lịch Sử Việt Nam Tập 10: Từ năm 1945 đến năm 1950       |
| 11 | Lịch Sử Việt Nam Tập 11: Từ năm 1951 đến năm 1954       |
| 12 | Lịch Sử Việt Nam Tập 12: Từ năm 1954 đến năm 1965       |
| 13 | Lịch Sử Việt Nam Tập 13: Từ năm 1965 đến năm 1975       |
| 14 | Lịch Sử Việt Nam Tập 14: Từ năm 1975 đến năm 1986       |
| 15 | Lịch Sử Việt Nam Tập 15: Từ năm 1986 đến năm 2000       |

## Prerequisites

Before running the project, install:

* Python 3.10+
* Node.js 18+
* npm or yarn
* Git
* Optional: ngrok account and auth token
* Optional: Kaggle environment for AI worker notebooks

## Backend Setup

Go to the backend directory:

```bash
cd app/BE
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment.

On Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Edit `.env`:

```env
ENVIRONMENT=development
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

DATABASE_URL=sqlite:///./data/history.db

SECRET_KEY=replace-with-a-strong-random-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=5
ADMIN_PASSWORD=replace-with-a-strong-admin-password

RAG_JSONL_PATH=./data/rag.jsonl

NGROK_AUTH_TOKEN=

FRONTEND_URL=http://localhost:3000

CHAT_WORKER_URLS_STR=
QUIZ_WORKER_URLS_STR=
```

Generate a secure secret key:

```bash
openssl rand -hex 32
```

Make sure the RAG file exists:

```text
app/BE/data/rag.jsonl
```

Then run the backend:

```bash
python run.py
```

When prompted:

```text
Do you want to expose server to public via ngrok? (y/n):
```

Choose:

* `n` for local development.
* `y` if you want to expose the backend through ngrok.

Backend default URL:

```text
http://localhost:8000
```

API documentation:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/health
```

## Frontend Setup

Open a new terminal and go to the frontend directory:

```bash
cd app/frontend-history
```

Install dependencies:

```bash
npm install
```

Or with yarn:

```bash
yarn install
```

Create a frontend environment file if needed:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Run the development server:

```bash
npm run dev
```

Or:

```bash
yarn dev
```

Frontend default URL:

```text
http://localhost:3000
```

## Running the Full Application Locally

Start the backend:

```bash
cd app/BE
python run.py
```

Start the frontend:

```bash
cd app/frontend-history
npm run dev
```

Open:

```text
http://localhost:3000
```

Available frontend pages:

```text
/       Chat with AI about Vietnamese history
/quiz   Generate Vietnamese history multiple-choice quizzes
```

## AI Worker Configuration

The backend does not run the heavy AI model directly. Instead, it forwards requests to one or more external worker URLs.

### Chat Worker

Configure chat workers in `.env`:

```env
CHAT_WORKER_URLS_STR=https://your-chat-worker-url.ngrok-free.app
```

The chat worker should expose:

```text
POST /chat
```

Expected request body:

```json
{
  "question": "Your question here",
  "session_id": "1"
}
```

Expected streaming response format:

```json
{"text": "partial answer"}
{"text": " next chunk"}
{"status": "completed"}
```

### Quiz Worker

Configure quiz workers in `.env`:

```env
QUIZ_WORKER_URLS_STR=https://your-quiz-worker-url.ngrok-free.app
```

The quiz worker should expose:

```text
POST /generate_quiz
```

Expected request body:

```json
{
  "num_questions": 10,
  "topic_ids": [1, 2, 3],
  "session_id": "worker_1"
}
```

Expected streaming response format:

```json
{
  "status": "processing",
  "new_questions": [
    {
      "question": "Question text",
      "options": ["A", "B", "C", "D"],
      "correct_answer": "A",
      "explanation": "Explanation text",
      "source_id": 0
    }
  ]
}
```

Final backend response to frontend:

```json
{
  "test_id": 1,
  "status": "completed",
  "questions": [
    {
      "question": "Question text",
      "options": ["A", "B", "C", "D"],
      "correct_answer": "A",
      "explanation": "Explanation text",
      "context": "Retrieved context from RAG data",
      "source_id": 0
    }
  ],
  "message": "Đề thi đã được tạo thành công!"
}
```

## Kaggle Worker Notebooks

The `kaggle/` directory contains notebooks for deploying model workers:

```text
kaggle/deploy_kaggle_chat.ipynb
kaggle/deploy_kaggle_genQuiz.ipynb
```

Typical workflow:

1. Upload or attach the required model artifacts to Kaggle.
2. Run the notebook.
3. Start the FastAPI worker inside the notebook.
4. Expose the worker through ngrok.
5. Copy the public ngrok URL.
6. Paste the URL into backend `.env` as either `CHAT_WORKER_URLS_STR` or `QUIZ_WORKER_URLS_STR`.
7. Restart the backend.

## RAG Data

The backend expects a JSONL file at:

```text
app/BE/data/rag.jsonl
```

Each line should contain a JSON object. A simplified example:

```json
{"text": "Historical context paragraph...", "metadata": {"source": "book", "topic_id": 1}}
```

The backend loads this file during startup and uses `source_id` values from generated quiz questions to retrieve the related context.

## Vector Database

The `vectorDB/` directory contains FAISS-related artifacts and notebooks:

```text
vectorDB/genDataRAG.ipynb
vectorDB/vectordb.ipynb
vectorDB/rag_index.faiss
vectorDB/rag_metadata.pkl
```

These files are used for preparing and storing retrieval data for the RAG pipeline.

## Fine-tuning

The `finetune/` directory contains model-related workflows:

```text
finetune/evaluate/
finetune/modelAnswer/
finetune/modelGenQuiz/
```

Suggested usage:

* `modelAnswer/`: fine-tuning or preparing the model for historical question answering.
* `modelGenQuiz/`: fine-tuning or preparing the model for quiz generation.
* `evaluate/`: evaluating model outputs.

## Backend API Overview

### Root

```http
GET /
```

Returns server status, environment, worker counts, and quiz topic metadata.

### Health Check

```http
GET /health
```

Returns backend health status, RAG loading status, database status, and worker counts.

### API Docs

```http
GET /docs
```

Opens Swagger UI.

### Login

```http
POST /api/auth/login
```

Uses admin password and returns a bearer token.

### Chat

```http
POST /api/chat
```

Request:

```json
{
  "message": "Ai là người lãnh đạo cuộc khởi nghĩa Lam Sơn?",
  "session_id": null
}
```

Response type:

```text
application/x-ndjson
```

### Generate Quiz

```http
POST /api/quiz/generate
```

Request:

```json
{
  "num_questions": 10,
  "topic_ids": [1, 2, 3]
}
```

Response type:

```text
application/x-ndjson
```

### Monitoring

```http
GET /api/monitor/connections
GET /api/monitor/system
GET /api/monitor/logs
```

Used to inspect worker connections, system status, and recent logs.

## Environment Variables

### Backend

| Variable                      |     Required | Description                                    |
| ----------------------------- | -----------: | ---------------------------------------------- |
| `ENVIRONMENT`                 |           No | Runtime environment, for example `development` |
| `SERVER_HOST`                 |           No | Backend bind host                              |
| `SERVER_PORT`                 |           No | Backend port, default `8000`                   |
| `DATABASE_URL`                |          Yes | SQLite database URL                            |
| `SECRET_KEY`                  |          Yes | Secret key for JWT                             |
| `ALGORITHM`                   |           No | JWT algorithm, default `HS256`                 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` |           No | JWT token lifetime                             |
| `ADMIN_PASSWORD`              |          Yes | Admin login password                           |
| `RAG_JSONL_PATH`              |          Yes | Path to RAG JSONL data                         |
| `NGROK_AUTH_TOKEN`            |           No | Optional ngrok auth token                      |
| `FRONTEND_URL`                |           No | Frontend URL for CORS                          |
| `CHAT_WORKER_URLS_STR`        | Yes for chat | Comma-separated chat worker URLs               |
| `QUIZ_WORKER_URLS_STR`        | Yes for quiz | Comma-separated quiz worker URLs               |

### Frontend

| Variable              | Required | Description                                                  |
| --------------------- | -------: | ------------------------------------------------------------ |
| `NEXT_PUBLIC_API_URL` |       No | Backend API URL. Defaults to `http://localhost:8000` in code |

## Troubleshooting

### Backend fails with `.env not found`

Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

### Backend fails with `File RAG không tồn tại`

Make sure this file exists:

```text
app/BE/data/rag.jsonl
```

Or update:

```env
RAG_JSONL_PATH=your/path/to/rag.jsonl
```

### Chat does not work

Check:

1. `CHAT_WORKER_URLS_STR` is configured.
2. The worker URL is online.
3. The worker exposes `POST /chat`.
4. The backend can access the worker URL.
5. The frontend points to the correct backend through `NEXT_PUBLIC_API_URL`.

### Quiz generation does not work

Check:

1. `QUIZ_WORKER_URLS_STR` is configured.
2. The worker URL is online.
3. The worker exposes `POST /generate_quiz`.
4. The selected number of questions is one of `10`, `20`, `30`, or `40`.
5. At least one topic is selected.

### CORS error in browser

Check backend `.env`:

```env
FRONTEND_URL=http://localhost:3000
```

Then restart the backend.

### Frontend cannot connect to backend

Create or update frontend environment variable:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Then restart the frontend dev server.

## Development Notes

* The frontend consumes streaming backend responses through `ReadableStream`.
* The backend streams data as NDJSON using `StreamingResponse`.
* The backend supports multiple workers and can distribute quiz generation across them.
* SQLite is used as the default local database.
* The backend creates database tables on startup.
* The RAG store is loaded during backend startup.
* ngrok support is optional and useful when connecting local/backend services to Kaggle worker notebooks.

## Suggested Repository Topics

```text
ai
rag
llm
fastapi
nextjs
vietnamese-history
quiz-generator
chatbot
faiss
kaggle
fine-tuning
```

## License

Free

Developed by Vũ Văn Phong.
