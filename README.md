# Legal Law Chatbot

A legal document chatbot with conversation-specific GraphRAG knowledge bases.


## Features

- **Multi-conversation support**: Each conversation has its own history and knowledge base
- **Document upload**: Upload PDFs/TXT files to build conversation-specific knowledge
- **Smart routing**: AI decides when to search knowledge base vs. answer general questions
- **Local LLM**: Uses Open AI for fast inference
- **GraphRAG**: Microsoft GraphRAG for intelligent document retrieval

## Prerequisites

- Docker & Docker Compose

## Quick Start

### Setup

1. **Create `.env` file**:
   - Copy `backend/.env.example` to `backend/.env`
   - Edit `backend/.env` and add your actual values:
     ```
     OPENAI_API_KEY=sk-your-actual-key-here
     OPENAI_MODEL=gpt-4o
     OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
     DATABASE_URL=postgresql://postgres:postgres@localhost:5432/legal_chatbot
     GRAPHRAG_DATA_DIR=./graphrag_data
     ```

### Run with Docker Compose

2. **Start the application**:
   ```bash
   docker-compose up --build
   ```

3. **Access the chat**: Open `http://localhost:8000`

### Run from Docker Repository

Alternatively, run directly from the Docker Hub repository:

```bash
docker run -d \
  --name legal-chatbot \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sk-your-key \
  -v ./data:/app/graphrag_data \
  aymrick2803/legal-law-chatbot:latest
```

**Note**: Make sure required services are running:
- PostgreSQL on `localhost:5432`

## Project Structure

```
legal-chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Configuration
│   │   ├── database/
│   │   │   ├── connection.py    # DB connection
│   │   │   ├── models.py        # SQLAlchemy models
│   │   │   └── repository.py    # Data access layer
│   │   ├── services/
│   │   │   ├── llm_service.py   # OpenAI integration
│   │   │   ├── chat_service.py  # Chat orchestration
│   │   │   ├── document_service.py
│   │   │   └── graphrag_service.py
│   │   ├── api/routes/
│   │   │       ├── chat.py
│   │   │       ├── conversation.py
│   │   │       └── document.py
│   │   └── utils/
│   │       └── pdf_converter.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── docker-compose.yml
```


## Development

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## License

MIT
