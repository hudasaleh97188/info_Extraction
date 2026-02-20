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
- **LLM**: Google Gemini via Vertex AI (`langchain-google-vertexai`)

## 🚀 Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Cloud Project with Vertex AI enabled
- GCP Application Default Credentials (`gcloud auth application-default login`)
- Nanonets API Key (Optional)
- `uv` (recommended) or `pip`

### 1. Backend Setup

Navigate to the backend directory:
```bash
cd backend
```

**Using uv (Recommended):**
```bash
# Sync dependencies from uv.lock
uv sync
```

**Using pip:**
```bash
# Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

# Install dependencies used in pyproject.toml
pip install -e .[dev]
```

**Configure environment variables:**
Create a `.env` file in the `backend` directory:
```env
GOOGLE_CLOUD_PROJECT=your_gcp_project_id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=True
# Optional:
# DATABASE_URL=sqlite:///./extraction.db
# NANONETS_API_KEY=your_nanonets_key
# MISTRAL_API_KEY=your_mistral_api_key_here (for evaluation tests)
```

Start the backend:
```bash
python main.py
```
Backend runs on: `http://localhost:5050`

### 2. Frontend Setup (Legacy)

Navigate to the frontend directory:
```bash
cd frontend
npm install
npm start
```
Frontend runs on: `http://localhost:4000`

## 📖 Usage

1. Open `http://localhost:4000`.
2. Upload a document (PDF or image).
3. Define extraction tasks (aim, output schema).
4. Click "Start Extraction" and view results.

## 🧪 Testing

The project includes a comprehensive test suite including unit, integration, performance, and evaluation tests.

### Running Tests
Make sure dev dependencies are installed (`uv sync` or `pip install -e .[dev]`).

```bash
# Run all tests
pytest tests/ -v

# Run specific categories
pytest tests/ -v -m unit
pytest tests/ -v -m integration
pytest tests/ -v -m performance
```

### Test Organization
- `tests/unit/`: Individual component tests (models, helpers).
- `tests/integration/`: Workflow execution tests (mocked LLM/OCR).
- `tests/performance/`: Execution time and benchmarking.
- `tests/evaluation/`: Quality assessment using DeepEval.

## 📊 Evaluation (DeepEval)

This project uses **DeepEval** to assess the quality, accuracy, and faithfulness of extracted data on real documents.

**Prerequisites**:
- `GOOGLE_CLOUD_PROJECT` and Vertex AI credentials
- `MISTRAL_API_KEY` (OCR for evaluation)
- Test images in `frontend/uploads/` (e.g., `Bank-Statement-Template-3-TemplateLab-1.jpg`)

**Run Evaluation**:
```bash
pytest tests/evaluation/ -v -m evaluation
```
This evaluates Correctness (GEval), Answer Relevancy, and Faithfulness.

## 🛠️ Development

### Project Structure
```
info-Extraction/
├── backend/               # Python Backend (LangGraph)
│   ├── src/               # Source code (workflows, agents, models)
│   ├── tests/             # Consolidated Test Suite
│   ├── main.py            # Flask API
│   └── pyproject.toml     # Dependencies
├── frontend/              # Node.js Frontend
│   ├── server.js
│   └── public/
└── README.md
```

## 📝 API Documentation
- `POST /extract`: Run extraction
- `GET/POST /templates`: Manage templates
- `GET/POST /projects`: Manage projects

## 📄 License
MIT
