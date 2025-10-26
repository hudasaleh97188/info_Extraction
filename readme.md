# 📄 Document Extraction System

A multi-agent document extraction system using CrewAI that allows users to define custom extraction tasks with dynamic schemas.

## 🏗️ Architecture

### Agents
1. **Orchestrator Agent**: Plans and coordinates the extraction workflow
2. **Schema Analyzer Agent**: Generates extraction prompts and Pydantic models from user schemas
3. **Extraction Specialist Agent**: Performs data extraction and validation

### Tech Stack
- **Frontend**: Node.js + Express + Vanilla JavaScript
- **Backend**: Python + CrewAI + Flask
- **OCR**: Nanonets API (with mock fallback)
- **LLM**: OpenAI GPT-4 (via CrewAI)

## 🚀 Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenAI API Key (required)
- Nanonets API Key (optional)

### Backend Setup

1. **Navigate to backend directory**:
```bash
cd backend
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required in `.env`:
```
OPENAI_API_KEY=sk-...
NANONETS_API_KEY=...  # Optional, uses mock data if not provided
```

5. **Start the backend server**:
```bash
python main.py
```

Backend runs on: `http://localhost:5000`

### Frontend Setup

1. **Navigate to frontend directory**:
```bash
cd frontend
```

2. **Install dependencies**:
```bash
npm install
```

3. **Start the frontend server**:
```bash
npm start
```

Frontend runs on: `http://localhost:3000`

## 📖 Usage

1. **Open your browser** to `http://localhost:3000`

2. **Upload a document** (PDF or image)

3. **Define extraction tasks**:
   - Click "Add Task"
   - Enter task aim (e.g., "Extract invoice line items")
   - Define output schema:
     - Column name (e.g., "item_name")
     - Type (string, number, boolean, date)
     - Description (optional)
     - Mark as mandatory if required
     - Mark as multi-row if extracting multiple items

4. **Click "Start Extraction"**

5. **View results** in JSON format

## 🎯 Example Use Cases

### Invoice Extraction
**Task 1**: Extract Header Information
- invoice_number (string, mandatory)
- invoice_date (date, mandatory)
- total_amount (number, mandatory)

**Task 2**: Extract Line Items (multi-row)
- item_name (string, mandatory)
- quantity (number, mandatory)
- unit_price (number, optional)
- total (number, mandatory)

### Resume Parsing
**Task 1**: Extract Personal Info
- name (string, mandatory)
- email (string, mandatory)
- phone (string, optional)

**Task 2**: Extract Work Experience (multi-row)
- company (string, mandatory)
- position (string, mandatory)
- start_date (date, optional)
- end_date (date, optional)

## 🛠️ Development

### Project Structure
```
info-Extraction/
├── frontend/
│   ├── server.js          # Express server
│   ├── public/
│   │   └── index.html     # UI
│   └── package.json
├── backend/
│   ├── src/
│   │   ├── crew.py        # CrewAI crew definition
│   │   ├── agents.py      # Agent definitions
│   │   ├── tasks.py       # Task definitions
│   │   ├── tools.py       # Custom tools
│   │   └── models.py      # Pydantic models
│   ├── main.py            # Flask API
│   └── requirements.txt
└── README.md
```

### Adding Custom Tools

Edit `backend/src/tools.py` to add new tools:

```python
from crewai_tools import BaseTool

class MyCustomTool(BaseTool):
    name: str = "My Tool"
    description: str = "What this tool does"
    
    def _run(self, input: str) -> str:
        # Tool logic here
        return result
```

### Modifying Agents

Edit `backend/src/agents.py` to customize agent behavior:

```python
def create_my_agent():
    return Agent(
        role='My Role',
        goal='My goal',
        backstory='My backstory',
        tools=[MyCustomTool()],
        verbose=True
    )
```

## 🔧 Configuration

### Using Real OCR (Nanonets)

1. Sign up at [Nanonets](https://nanonets.com/)
2. Get your API key
3. Add to `.env`:
```
NANONETS_API_KEY=your_key_here
```

### Changing LLM Model

Edit `.env`:
```
OPENAI_MODEL_NAME=gpt-4
# or
OPENAI_MODEL_NAME=gpt-3.5-turbo
```

## 🐛 Troubleshooting

### Backend won't start
- Check Python version: `python --version` (need 3.10+)
- Check OpenAI API key is set in `.env`
- Check virtual environment is activated

### Frontend won't start
- Check Node.js version: `node --version` (need 18+)
- Delete `node_modules` and run `npm install` again

### Extraction fails
- Check backend logs in terminal
- Verify OpenAI API key is valid
- Check if document is readable (try with mock data first)

### No results returned
- Check browser console for errors
- Verify backend is running on port 5000
- Check CORS is enabled

## 📝 API Documentation

### POST /extract

**Request**:
```json
{
  "file_data": "base64_encoded_file",
  "file_name": "document.pdf",
  "file_type": "application/pdf",
  "tasks": [
    {
      "aim": "Extract invoice items",
      "schema": [
        {
          "name": "item_name",
          "type": "string",
          "description": "Product name",
          "mandatory": true,
          "multi_row": true
        }
      ]
    }
  ]
}
```

**Response**:
```json
{
  "status": "success",
  "markdown_length": 1234,
  "tasks_processed": 2,
  "results": {
    "task_1": {...},
    "task_2": {...}
  }
}
```

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

MIT
