#!/bin/bash

echo "🚀 Starting Document Extraction System..."
echo ""

# Check if .env exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  No .env file found!"
    echo "Creating from template..."
    cp backend/.env.example backend/.env
    echo ""
    echo "📝 Please edit backend/.env and add your API keys:"
    echo "   - OPENAI_API_KEY (required)"
    echo "   - NANONETS_API_KEY (optional)"
    echo ""
    read -p "Press enter after configuring .env file..."
fi

# Start backend
echo "🐍 Starting Python backend..."
cd backend
source venv/bin/activate 2>/dev/null || python -m venv venv && source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Start frontend
echo "🌐 Starting Node.js frontend..."
cd frontend
npm install > /dev/null 2>&1
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ System started!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend:  http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo ''; echo '👋 Shutting down...'; exit" INT
wait
