# 📄 Document Extraction System

A multi-agent document extraction system using **LangGraph** that allows users to define custom extraction tasks with dynamic schemas.

## 🏗️ Architecture

### Agents
1. **Orchestrator Agent**: Plans and coordinates the extraction workflow.
2. **Schema Analyzer Agent**: Generates extraction prompts and Pydantic models from user schemas.
3. **Extraction Specialist Agent**: Performs data extraction and validation.

### Tech Stack
- **Backend**: Python + Flask + LangGraph + SQLite (SQLAlchemy)
- **Frontend**: Node.js + Express + Vanilla JavaScript (Legacy)
- **OCR**: Nanonets API (with mock fallback)
- **LLM**: Google Gemini via `langchain_google_genai`

## 🚀 Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google API Key (Gemini)
- Nanonets API Key (Optional)

### 1. Backend Setup

Navigate to the backend directory:
```bash
cd backend
```

Create and activate a virtual environment:
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Configure environment variables:
Create a `.env` file in the `backend` directory:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
# Optional:
# DATABASE_URL=sqlite:///./extraction.db
# NANONETS_API_KEY=your_nanonets_key
```

Start the backend:
```bash
python main.py
```
Backend runs on: `http://localhost:5000`

### 2. Frontend Setup (Legacy)

Navigate to the frontend directory:
```bash
cd frontend
```

Install dependencies:
```bash
npm install
```

Start the frontend:
```bash
npm start
```
Frontend runs on: `http://localhost:3000`

## 📖 Usage

1. **Open your browser** to `http://localhost:3000`.
2. **Upload a document** (PDF or image).
3. **Define extraction tasks**:
   - Click "Add Task".
   - Enter task aim (e.g., "Extract invoice line items").
   - Define output schema (Column name, Type, Description, Mandatory, Multi-row).
4. **Click "Start Extraction"**.
5. **View results** in JSON format.

## 🛠️ Development

### Project Structure
```
info-Extraction/
├── backend/               # Python Backend (LangGraph)
│   ├── src/
│   │   ├── lg_workflow.py # LangGraph workflow definition
│   │   ├── agents.py      # Agent definitions
│   │   ├── db_models.py   # SQLAlchemy models
│   │   └── ...
│   ├── main.py            # Flask API
│   └── requirements.txt
├── frontend/              # Legacy Node.js Frontend
│   ├── server.js          # Express server
│   └── public/            # UI
└── README.md
```

## 📝 API Documentation

### Backend Endpoints
- `GET /templates` — List templates
- `POST /templates` — Create template
- `GET /projects` — List projects
- `POST /projects` — Create project
- `POST /extract` — Run extraction

## 📄 License

MIT
