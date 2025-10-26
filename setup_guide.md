# 🎯 Step-by-Step Setup Guide

Follow these exact steps to get your system running in under 10 minutes!

## ⚡ Quick Setup (Recommended)

### 1. Create Project Structure
```bash
# Create main directories
mkdir -p info_Extraction/frontend/public
mkdir -p info_Extraction/backend/src
cd info_Extraction
```

### 2. Copy All Provided Files

**Backend files** (copy from artifacts):
```
backend/
├── requirements.txt          # ✅ Copy content
├── .env.example             # ✅ Copy content
├── main.py                  # ✅ Copy content
└── src/
    ├── __init__.py          # ⚠️ Create EMPTY file
    ├── models.py            # ✅ Copy content
    ├── tools.py             # ✅ Copy content
    ├── agents.py            # ✅ Copy content
    ├── tasks.py             # ✅ Copy content
    └── crew.py              # ✅ Copy content
```

**Frontend files** (copy from artifacts):
```
frontend/
├── package.json             # ✅ Copy content
├── server.js                # ✅ Copy content
└── public/
    └── index.html           # ✅ Copy content
```

**Root files** (copy from artifacts):
```
info_Extraction/
├── README.md                # ✅ Copy content
├── start.sh                 # ✅ Copy content (Linux/Mac)
└── start.bat                # ✅ Copy content (Windows)
```

### 3. Create Empty __init__.py
```bash
# Linux/Mac
touch backend/src/__init__.py

# Windows
type nul > backend\src\__init__.py
```

### 4. Setup Backend
```bash
cd backend

# Copy and configure environment
cp .env.example .env
nano .env  # or use any text editor
```

Add your OpenAI API key to `.env`:
```
OPENAI_API_KEY=sk-proj-your-actual-key-here
NANONETS_API_KEY=  # Leave empty for now (optional)
```

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 5. Setup Frontend
```bash
cd ../frontend

# Install dependencies
npm install
```

### 6. Start the System

**Option A: Using start scripts**
```bash
# Linux/Mac
cd ..
chmod +x start.sh
./start.sh

# Windows
cd ..
start.bat
```

**Option B: Manual (2 terminals)**

Terminal 1:
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python main.py
```

Terminal 2:
```bash
cd frontend
npm start
```

### 7. Test It!
Open browser: **http://localhost:3000**

You should see the beautiful purple extraction UI! 🎨

---

## 🔍 Detailed Setup (If Issues Occur)

### Backend Setup (Detailed)

#### Step 1: Check Python Version
```bash
python --version
# Should be 3.10 or higher
```

If Python is too old:
- **Mac**: `brew install python@3.11`
- **Ubuntu**: `sudo apt install python3.11`
- **Windows**: Download from python.org

#### Step 2: Create Virtual Environment
```bash
cd backend
python -m venv venv
```

If error "venv not found":
```bash
# Ubuntu/Debian
sudo apt install python3-venv

# Mac
# Should work by default

# Windows
# Should work by default
```

#### Step 3: Activate Virtual Environment
```bash
# Linux/Mac
source venv/bin/activate

# Windows CMD
venv\Scripts\activate

# Windows PowerShell
venv\Scripts\Activate.ps1
```

You should see `(venv)` in your prompt.

#### Step 4: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

If CrewAI installation fails:
```bash
pip install crewai==0.86.0 --no-cache-dir
pip install crewai-tools==0.12.1 --no-cache-dir
pip install -r requirements.txt
```

#### Step 5: Configure Environment
```bash
cp .env.example .env
```

Edit `.env` with your favorite editor:
```bash
nano .env
# or
code .env
# or
notepad .env  # Windows
```

**CRITICAL**: Add your OpenAI API key:
```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
```

Get key from: https://platform.openai.com/api-keys

#### Step 6: Create __init__.py
```bash
# From backend directory
touch src/__init__.py
```

This makes `src` a Python package.

#### Step 7: Test Backend
```bash
python main.py
```

Expected output:
```
🚀 Starting Extraction Backend...
📡 Nanonets API: Not configured (using mock)
🔑 OpenAI API: Configured
 * Running on http://0.0.0.0:5000
```

Test health endpoint:
```bash
curl http://localhost:5000/health
```

Should return:
```json
{"status":"ok","service":"extraction-backend","nanonets_configured":false}
```

### Frontend Setup (Detailed)

#### Step 1: Check Node.js Version
```bash
node --version
# Should be 18 or higher
```

If Node.js is too old:
- **Mac**: `brew install node`
- **Ubuntu**: 
  ```bash
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y nodejs
  ```
- **Windows**: Download from nodejs.org

#### Step 2: Install Dependencies
```bash
cd frontend
npm install
```

If errors occur:
```bash
# Clear cache and retry
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

#### Step 3: Test Frontend
```bash
npm start
```

Expected output:
```
🚀 Frontend server running on http://localhost:3000
```

Open browser: **http://localhost:3000**

---

## 🧪 Testing Your Installation

### Test 1: Backend Health Check
```bash
curl http://localhost:5000/health
```

✅ Expected: `{"status":"ok"}`

### Test 2: Frontend Loads
Open: http://localhost:3000

✅ Expected: See upload interface with purple gradient

### Test 3: Mock Extraction

1. Click "Upload PDF or Image" (select any PDF/image)
2. Task aim: "Extract invoice number"
3. Add schema field:
   - Name: `invoice_number`
   - Type: `string`
   - Mandatory: ✓
4. Click "Start Extraction"

✅ Expected: After ~30 seconds, see results JSON with mock invoice data

### Test 4: Check Logs

**Backend terminal should show:**
```
📄 Processing file: document.pdf
📋 Tasks: 1
🔄 Preparing document with OCR...
⚠️ No Nanonets API key found, using mock markdown
✅ Document prepared. Markdown length: 823 chars
🚀 Starting extraction crew...
```

---

## 🐛 Troubleshooting

### Error: "OPENAI_API_KEY not found"
**Cause**: `.env` file missing or key not set

**Fix**:
```bash
cd backend
echo 'OPENAI_API_KEY=sk-your-key-here' > .env
```

### Error: "ModuleNotFoundError: No module named 'crewai'"
**Cause**: Virtual environment not activated or dependencies not installed

**Fix**:
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate
pip install -r requirements.txt
```

### Error: "Port 5000 is already in use"
**Cause**: Another app using port 5000

**Fix**:
```bash
# Linux/Mac
lsof -ti:5000 | xargs kill -9

# Windows
netstat -ano | findstr :5000
# Note the PID, then:
taskkill /PID <PID> /F
```

Or change port in `backend/main.py`:
```python
app.run(host='0.0.0.0', port=5001, debug=True)  # Change to 5001
```

And in `frontend/server.js`:
```javascript
const BACKEND_URL = 'http://localhost:5001';  // Change to 5001
```

### Error: "Cannot find module 'express'"
**Cause**: NPM dependencies not installed

**Fix**:
```bash
cd frontend
npm install
```

### Error: "File upload fails"
**Cause**: File too large or CORS issue

**Fix**: Check `frontend/server.js` file size limit:
```javascript
limits: { fileSize: 10 * 1024 * 1024 } // 10MB, increase if needed
```

### Error: "Extraction takes forever"
**Cause**: Large document or slow API response

**Fix**: This is normal. Wait 1-3 minutes. For very large documents, the LLM may take time.

---

## ✅ Installation Complete!

If you can:
- ✅ Access http://localhost:3000
- ✅ See the UI interface
- ✅ Upload a file
- ✅ Get extraction results (even with mock data)

**Congratulations! Your system is working! 🎉**

---

## 🚀 Next Steps

1. **Get Nanonets API Key** (optional but recommended):
   - Sign up: https://nanonets.com
   - Get API key from dashboard
   - Add to `backend/.env`:
     ```
     NANONETS_API_KEY=your-key-here
     ```

2. **Try Real Extraction**:
   - Upload an invoice PDF
   - Define multiple extraction tasks
   - See it parse real documents!

3. **Customize**:
   - Modify agents in `backend/src/agents.py`
   - Add tools in `backend/src/tools.py`
   - Enhance UI in `frontend/public/index.html`

4. **Learn More**:
   - Read `README.md` for full documentation
   - Check `PROJECT_STRUCTURE.md` for architecture
   - Explore CrewAI docs: https://docs.crewai.com

---

## 📞 Need Help?

Common issues and solutions are in the Troubleshooting section above.

For CrewAI specific issues:
- https://docs.crewai.com
- https://github.com/joaomdmoura/crewAI/issues

Happy extracting! 📄✨