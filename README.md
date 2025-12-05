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

1. From the OpenAI API site, create an OPEN AI KEY and Create a .env environment file to store the following variables: 
- **OPENAI_API_KEY** = .......
- **OPENAI_MODE**L=gpt-4o
- **OPENAI_EMBEDDING_MODEL**=text-embedding-3-small
- **OPENAI_BASE_URL**= https://api.openai.com/v1
- **DATABASE_UR** = postgresql://... |

 
2. **Start the application**:
   ```bash
   docker-compose up -d
   ```

3. **Access the chat**: Open `http://localhost:8000`

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
