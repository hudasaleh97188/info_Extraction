from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import traceback

# Import the crew implementation from src
try:
    from src.crew import ExtractionCrew
except Exception as import_error:
    # Fallback: adjust path if running directly without package context
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(current_dir, 'src')
    if src_dir not in sys.path:
        sys.path.append(src_dir)
    from crew import ExtractionCrew  # type: ignore

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
        
        # Normalize UI tasks: map `schema` -> `extraction_schema` expected by backend crew
        normalized_tasks = []
        for t in tasks:
            if isinstance(t, dict):
                task_copy = dict(t)
                if 'extraction_schema' not in task_copy and 'schema' in task_copy:
                    task_copy['extraction_schema'] = task_copy.get('schema')
                normalized_tasks.append(task_copy)
            else:
                normalized_tasks.append(t)
        
        inputs = {
            'file_data': file_data,
            'file_name': file_name,
            'file_type': file_type,
            'tasks': normalized_tasks
        }
        
        result = crew.run(inputs)
        
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
