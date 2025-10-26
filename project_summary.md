# 📁 Complete Project Structure

Create this folder structure for your project:

```
extraction-system/
│
├── README.md                      # Main documentation
├── start.sh                       # Quick start (Linux/Mac)
├── start.bat                      # Quick start (Windows)
│
├── frontend/                      # Node.js Frontend
│   ├── package.json              # Dependencies
│   ├── server.js                 # Express server
│   ├── public/
│   │   └── index.html            # UI interface
│   └── uploads/                  # Temp file storage (auto-created)
│
└── backend/                       # Python Backend
    ├── requirements.txt          # Python dependencies
    ├── main.py                   # Flask API server
    ├── .env.example              # Environment template
    ├── .env                      # Your config (create from example)
    │
    └── src/                      # Source code
        ├── __init__.py          # (empty file)
        ├── crew.py              # CrewAI crew with @before_kickoff
        ├── agents.py            # Agent definitions
        ├── tasks.py             # Task definitions
        ├── tools.py             # Custom CrewAI tools
        └── models.py            # Pydantic models
```

## 📝 File Creation Checklist

### Step 1: Create Root Structure
```bash
mkdir -p extraction-system/frontend/public
mkdir -p extraction-system/backend/src
cd extraction-system
```

### Step 2: Create Backend Files

**backend/requirements.txt** ✅ (provided)
**backend/.env.example** ✅ (provided)
**backend/main.py** ✅ (provided)

**backend/src/__init__.py** (create empty file):
```bash
touch backend/src/__init__.py
```

**backend/src/models.py** ✅ (provided)
**backend/src/tools.py** ✅ (provided)
**backend/src/agents.py** ✅ (provided)
**backend/src/tasks.py** ✅ (provided)
**backend/src/crew.py** ✅ (provided)

### Step 3: Create Frontend Files

**frontend/package.json** ✅ (provided)
**frontend/server.js** ✅ (provided)
**frontend/public/index.html** ✅ (provided)

### Step 4: Create Documentation

**README.md** ✅ (provided)
**start.sh** ✅ (provided)
**start.bat** ✅ (provided)

### Step 5: Setup Environment

```bash
# Backend
cd backend
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

## 🎯 Quick Start Commands

### Option 1: Use Start Scripts
```bash
# Linux/Mac
chmod +x start.sh
./start.sh

# Windows
start.bat
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

## 🔑 Required Configuration

### backend/.env (MUST CREATE)
```bash
OPENAI_API_KEY=sk-proj-...        # REQUIRED
NANONETS_API_KEY=...              # OPTIONAL (uses mock if missing)
OPENAI_MODEL_NAME=gpt-4-turbo-preview  # OPTIONAL
```

## 🧪 Testing the System

### 1. Check Backend Health
```bash
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "ok",
  "service": "extraction-backend",
  "nanonets_configured": false
}
```

### 2. Check Frontend
Open browser: `http://localhost:3000`

### 3. Test Extraction

1. Upload a PDF or image
2. Add a task:
   - Aim: "Extract invoice number"
   - Schema: 
     - name: invoice_number
     - type: string
     - mandatory: true
3. Click "Start Extraction"

## 📦 Dependencies Overview

### Python (backend)
- `crewai` - Multi-agent framework
- `flask` - API server
- `pydantic` - Data validation
- `requests` - HTTP client for Nanonets

### Node.js (frontend)
- `express` - Web server
- `multer` - File upload handling
- `axios` - HTTP client
- `cors` - Cross-origin requests

## 🔧 Customization Points

### Add New Agent
Edit `backend/src/agents.py`:
```python
def create_my_agent():
    return Agent(
        role='My Role',
        goal='My goal',
        backstory='...',
        tools=[...],
        verbose=True
    )
```

### Add New Tool
Edit `backend/src/tools.py`:
```python
class MyTool(BaseTool):
    name: str = "My Tool"
    description: str = "..."
    
    def _run(self, input: str) -> str:
        return result
```

### Modify UI
Edit `frontend/public/index.html` - all HTML, CSS, and JavaScript in one file.

### Change OCR Provider
Edit `backend/src/crew.py` → `_convert_to_markdown()` method

## 📊 Data Flow

```
User (UI)
  ↓ upload file + tasks
Frontend (Express)
  ↓ base64 + JSON
Backend (Flask API)
  ↓ 
ExtractionCrew
  ↓ @before_kickoff
Nanonets OCR → Markdown
  ↓
Orchestrator Agent
  ↓ delegates
Schema Analyzer Agent
  ↓ generates prompt + Pydantic model
Extraction Specialist Agent
  ↓ extracts data
Results (JSON)
  ↓
Frontend → Display
```

## 🐛 Common Issues & Solutions

### Issue: "OPENAI_API_KEY not found"
**Solution:** Create `backend/.env` and add your key:
```bash
cd backend
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

### Issue: Port already in use
**Solution:** Kill existing processes:
```bash
# Linux/Mac
lsof -ti:5000 | xargs kill -9
lsof -ti:3000 | xargs kill -9

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Issue: CrewAI import errors
**Solution:** Reinstall in virtual environment:
```bash
cd backend
source venv/bin/activate
pip uninstall crewai crewai-tools -y
pip install crewai==0.86.0 crewai-tools==0.12.1
```

### Issue: Frontend can't connect to backend
**Solution:** Check CORS and backend URL in `frontend/server.js`:
```javascript
const BACKEND_URL = 'http://localhost:5000';
```

### Issue: Mock data not working
**Solution:** This is normal when Nanonets API key is missing. The system will use sample invoice data for testing.

## 🎨 UI Features

### Current Features
- ✅ File upload (PDF/Image)
- ✅ Dynamic task definition
- ✅ Dynamic schema builder
- ✅ Multi-row support
- ✅ Mandatory field marking
- ✅ Real-time results display
- ✅ Loading indicators

### Potential Enhancements
- 📊 Add result visualization
- 💾 Download results as JSON/CSV
- 📝 Save task templates
- 🔄 Batch processing
- 📈 Progress tracking per task
- ✏️ Edit results before export

## 🚀 Deployment Options

### Local Development
Already configured! Use start scripts.

### Docker (Future)
Create `Dockerfile` for each service and `docker-compose.yml`:
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

### Cloud Deployment
- **Backend**: Deploy to Heroku, Railway, or AWS Lambda
- **Frontend**: Deploy to Vercel, Netlify, or Cloudflare Pages

## 📈 Performance Tips

### For Large Documents
1. Increase timeout in `frontend/server.js`:
```javascript
timeout: 600000 // 10 minutes
```

2. Add chunking in `backend/src/crew.py`:
```python
def chunk_markdown(content, chunk_size=2000):
    # Split into manageable chunks
    pass
```

### For Multiple Tasks
Consider parallel execution in orchestrator agent (future enhancement).

## 🔒 Security Considerations

### Current Setup (Development)
- ⚠️ No authentication
- ⚠️ No file validation
- ⚠️ No rate limiting

### Production Recommendations
- ✅ Add API authentication (JWT)
- ✅ Validate file types and sizes
- ✅ Add rate limiting (Flask-Limiter)
- ✅ Sanitize file names
- ✅ Use environment-based configs
- ✅ Add HTTPS
- ✅ Implement CSRF protection

## 📚 Additional Resources

### CrewAI Documentation
- [Official Docs](https://docs.crewai.com/)
- [GitHub](https://github.com/joaomdmoura/crewAI)

### Nanonets OCR
- [API Docs](https://nanonets.com/documentation/)
- [Dashboard](https://app.nanonets.com/)

### OpenAI API
- [API Reference](https://platform.openai.com/docs/api-reference)
- [Pricing](https://openai.com/pricing)

## 🎓 Learning Path

1. **Understand the Flow**: Follow one extraction request through all agents
2. **Modify Tools**: Add a simple validation tool
3. **Customize Agents**: Change agent personalities/goals
4. **Add Features**: Implement result export
5. **Optimize**: Add caching, parallel processing

## 💡 Extension Ideas

### Business Logic
- Add validation rules engine
- Support for extraction templates
- Historical data comparison
- Confidence scoring

### Technical
- WebSocket for real-time updates
- Background job queue (Celery)
- Result caching (Redis)
- Database storage (PostgreSQL)

### UI/UX
- Drag-and-drop upload
- Preview extracted data
- Edit mode for corrections
- Export to multiple formats

---

## ✅ Verification Checklist

Before running, ensure:

- [ ] All files created in correct locations
- [ ] `backend/.env` configured with OPENAI_API_KEY
- [ ] Python virtual environment created
- [ ] Python dependencies installed
- [ ] Node.js dependencies installed
- [ ] Backend starts on port 5000
- [ ] Frontend starts on port 3000
- [ ] Can access UI at localhost:3000
- [ ] Health endpoint returns OK

---

**You're all set! 🎉**

Run `./start.sh` (Linux/Mac) or `start.bat` (Windows) to begin!