from flask import Flask, request, jsonify
from flask_cors import CORS
from crew import ExtractionCrew
from dotenv import load_dotenv
import os
import traceback

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/extract', methods=['POST'])
def extract():
    """
    Main extraction endpoint
    Receives file data and extraction tasks, returns structured results
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        file_data = data.get('file_data')
        file_name = data.get('file_name')
        file_type = data.get('file_type')
        tasks = data.get('tasks')
        
        if not all([file_data, file_name, tasks]):
            return jsonify({"error": "Missing required fields"}), 400
        
        if not tasks or len(tasks) == 0:
            return jsonify({"error": "No extraction tasks provided"}), 400
        
        print(f"📄 Processing file: {file_name}")
        print(f"📋 Tasks: {len(tasks)}")
        
        # Initialize and run extraction crew
        crew = ExtractionCrew()
        
        inputs = {
            'file_data': file_data,
            'file_name': file_name,
            'file_type': file_type,
            'tasks': tasks
        }
        
        result = crew.extract(inputs)
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "error": "Extraction failed",
            "details": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "service": "extraction-backend",
        "nanonets_configured": bool(os.getenv('NANONETS_API_KEY'))
    }), 200

if __name__ == '__main__':
    print("🚀 Starting Extraction Backend...")
    print(f"📡 Nanonets API: {'Configured' if os.getenv('NANONETS_API_KEY') else 'Not configured (using mock)'}")
    print(f"🔑 OpenAI API: {'Configured' if os.getenv('OPENAI_API_KEY') else 'NOT CONFIGURED - REQUIRED!'}")
    
    if not os.getenv('OPENAI_API_KEY'):
        print("\n⚠️  WARNING: OPENAI_API_KEY not found in environment!")
        print("   Set it in .env file or export OPENAI_API_KEY=your_key\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
