# ✅ Deployment Checklist

Use this checklist to ensure everything is set up correctly before running the system.

---

## 📁 File Creation Checklist

### Backend Files
- [ ] `backend/requirements.txt` created
- [ ] `backend/main.py` created
- [ ] `backend/.env.example` created
- [ ] `backend/.env` created (from .env.example)
- [ ] `backend/test_extraction.py` created
- [ ] `backend/src/__init__.py` created (EMPTY FILE!)
- [ ] `backend/src/models.py` created
- [ ] `backend/src/tools.py` created
- [ ] `backend/src/agents.py` created
- [ ] `backend/src/tasks.py` created
- [ ] `backend/src/crew.py` created

### Frontend Files
- [ ] `frontend/package.json` created
- [ ] `frontend/server.js` created
- [ ] `frontend/public/index.html` created

### Documentation Files
- [ ] `README.md` created
- [ ] `SETUP_GUIDE.md` created
- [ ] `PROJECT_STRUCTURE.md` created
- [ ] `IMPLEMENTATION_SUMMARY.md` created
- [ ] `start.sh` created (Linux/Mac)
- [ ] `start.bat` created (Windows)

---

## ⚙️ Configuration Checklist

### Backend Configuration
- [ ] Python 3.10+ installed (`python --version`)
- [ ] Virtual environment created (`python -m venv venv`)
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured with OPENAI_API_KEY
- [ ] OPENAI_API_KEY is valid (test at platform.openai.com)
- [ ] (Optional) NANONETS_API_KEY added to `.env`

### Frontend Configuration
- [ ] Node.js 18+ installed (`node --version`)
- [ ] npm is working (`npm --version`)
- [ ] Dependencies installed (`npm install`)
- [ ] No errors in `npm install` output

---

## 🧪 Testing Checklist

### Pre-Start Tests
- [ ] Backend can import CrewAI: `python -c "import crewai; print('OK')"`
- [ ] Backend can import Flask: `python -c "import flask; print('OK')"`
- [ ] Backend .env is loaded: `python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(bool(os.getenv('OPENAI_API_KEY')))"`
- [ ] Frontend node_modules exists
- [ ] No syntax errors in any files

### Start-Up Tests
- [ ] Backend starts without errors: `python main.py`
- [ ] Backend shows: "Starting Extraction Backend..."
- [ ] Backend shows: "OpenAI API: Configured"
- [ ] Backend shows: "Running on http://0.0.0.0:5000"
- [ ] Backend health check works: `curl http://localhost:5000/health`
- [ ] Frontend starts without errors: `npm start`
- [ ] Frontend shows: "Frontend server running on http://localhost:3000"

### UI Tests
- [ ] Can access http://localhost:3000 in browser
- [ ] See purple gradient background
- [ ] See "Document Extraction System" title
- [ ] See file upload button
- [ ] See "Add Task" button
- [ ] Default task is created automatically

### Functionality Tests
- [ ] Can click "Upload PDF or Image"
- [ ] Can select a file
- [ ] File name appears below upload button
- [ ] Can click "Add Task" to add more tasks
- [ ] Can add schema fields (column name, type, etc.)
- [ ] Can check "Mandatory" checkbox
- [ ] Can check "Multi-row" checkbox
- [ ] Can click "Remove" to delete a task
- [ ] "Start Extraction" button is disabled when no file uploaded
- [ ] "Start Extraction" button is enabled when file uploaded

### Extraction Tests
- [ ] Click "Start Extraction" with test file
- [ ] See loading spinner appear
- [ ] Wait 30-60 seconds
- [ ] Loading spinner disappears
- [ ] Results section appears
- [ ] See JSON output in results
- [ ] JSON is valid (copy and check at jsonlint.com)
- [ ] Can see extracted data in results

### Backend Test Script
- [ ] Run: `cd backend && python test_extraction.py`
- [ ] See: "Testing Document Extraction System"
- [ ] See: "Checking environment..."
- [ ] See: "OpenAI API Key: ****..."
- [ ] See: "Starting extraction crew..."
- [ ] Wait for completion (1-2 minutes)
- [ ] See: "TEST PASSED! System is working correctly!"

---

## 🔍 Troubleshooting Checklist

### If Backend Won't Start

- [ ] Check Python version: `python --version` (need 3.10+)
- [ ] Check virtual environment is activated (see `(venv)` in prompt)
- [ ] Check OPENAI_API_KEY is in `.env` file
- [ ] Check `.env` is in `backend/` directory
- [ ] Try: `pip install --upgrade crewai crewai-tools`
- [ ] Try: `pip install --force-reinstall -r requirements.txt`
- [ ] Check port 5000 is not in use: `lsof -i:5000` or `netstat -ano | findstr :5000`

### If Frontend Won't Start

- [ ] Check Node.js version: `node --version` (need 18+)
- [ ] Check npm version: `npm --version`
- [ ] Try: `rm -rf node_modules package-lock.json && npm install`
- [ ] Try: `npm cache clean --force && npm install`
- [ ] Check port 3000 is not in use

### If Extraction Fails

- [ ] Check backend terminal for error messages
- [ ] Check frontend browser console (F12) for errors
- [ ] Verify OPENAI_API_KEY is correct
- [ ] Try smaller file (< 1MB)
- [ ] Try with mock data (no file, system will generate sample)
- [ ] Check CrewAI version: `pip show crewai` (should be 0.86.0)
- [ ] Check task has at least one schema field defined
- [ ] Check schema field names don't have spaces or special characters

### If Results Look Wrong

- [ ] Check if using mock data (normal if no Nanonets key)
- [ ] Verify task aim is clear and specific
- [ ] Check schema field types are correct
- [ ] Try with simpler extraction (fewer fields)
- [ ] Check backend logs for agent outputs
- [ ] Verify document has extractable text (not scanned image without OCR)

---

## 🚀 Pre-Production Checklist

### Security
- [ ] Change default ports if deploying publicly
- [ ] Add API authentication
- [ ] Add rate limiting
- [ ] Validate file types and sizes
- [ ] Sanitize file names
- [ ] Use HTTPS
- [ ] Don't commit `.env` to git
- [ ] Add `.env` to `.gitignore`

### Performance
- [ ] Test with large documents (10+ pages)
- [ ] Test with multiple concurrent users
- [ ] Add request timeout handling
- [ ] Consider adding queue system for long tasks
- [ ] Monitor OpenAI API costs

### Reliability
- [ ] Add error logging
- [ ] Add retry logic for failed extractions
- [ ] Add health check monitoring
- [ ] Set up backup OCR provider
- [ ] Test with various document formats

---

## 📊 Success Criteria

Your system is ready when ALL of these are true:

✅ Both backend and frontend start without errors
✅ UI is accessible at localhost:3000
✅ Health endpoint returns `{"status":"ok"}`
✅ Can upload a file successfully
✅ Can define extraction tasks
✅ Extraction completes in reasonable time (< 2 min)
✅ Results are returned as valid JSON
✅ Multiple tasks work sequentially
✅ test_extraction.py passes
✅ No console errors in browser
✅ No Python tracebacks in terminal

---

## 🎯 Quick Verification Commands

Run these in order to verify everything:

```bash
# 1. Check Python
python --version  # Should be 3.10+

# 2. Check Node
node --version  # Should be 18+

# 3. Check virtual environment
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python -c "import crewai; print('CrewAI OK')"

# 4. Check .env
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API Key:', bool(os.getenv('OPENAI_API_KEY')))"

# 5. Test backend
python test_extraction.py

# 6. Check frontend
cd ../frontend
npm run | grep start  # Should show start script

# 7. Check health (backend must be running)
curl http://localhost:5000/health

# 8. Check UI (in browser)
# Open: http://localhost:3000
```

---

## 📝 Final Pre-Launch Notes

Before considering the system production-ready:

1. **Test thoroughly** with real documents from your use case
2. **Monitor costs** - OpenAI API calls add up
3. **Document edge cases** - what documents work vs don't work
4. **Set expectations** - extraction isn't 100% accurate
5. **Have fallback** - manual review process for critical data
6. **Plan scaling** - what happens with 100 concurrent users?
7. **Backup strategy** - what if OpenAI API is down?

---

## ✨ You're Ready When...

- [ ] All checkboxes above are checked ✅
- [ ] System runs for 1 hour without errors
- [ ] Successfully extracted from 5+ different documents
- [ ] Team members can use it without your help
- [ ] Documentation is clear and up-to-date
- [ ] You understand how to modify agents/tools
- [ ] You have a plan for production deployment

---

**Good luck with your document extraction system! 🚀**
