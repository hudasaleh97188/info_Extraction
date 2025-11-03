from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import traceback
import sys

# Switch to LangGraph workflow
try:
    from src.lg_workflow import create_extraction_graph
except Exception:
    # Fallback path adjust
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(current_dir, 'src')
    if src_dir not in sys.path:
        sys.path.append(src_dir)
    from lg_workflow import create_extraction_graph  # type: ignore

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
        
        # Normalize UI tasks: map `schema` -> `extraction_schema` expected by backend
        normalized_tasks = []
        for t in tasks:
            if isinstance(t, dict):
                task_copy = dict(t)
                if 'extraction_schema' not in task_copy and 'schema' in task_copy:
                    task_copy['extraction_schema'] = task_copy.get('schema')
                normalized_tasks.append(task_copy)
            else:
                normalized_tasks.append(t)
        
        # Build graph input
        graph_input = {
            "original_input": {
                'file_data': file_data,
                'file_name': file_name,
                'file_type': file_type,
                'tasks': normalized_tasks
            }
        }

        # Compile and run LangGraph once per request (can be optimized if needed)
        app_graph = create_extraction_graph()
        final_state = app_graph.invoke(graph_input)

        final_output = final_state.get("final_output")
        if final_output is None:
            # Fallback: return entire state for debugging
            return jsonify({
                "status": "error",
                "error": "Graph finished without final_output",
                "state": final_state
            }), 500

        # final_output is Pydantic; return JSON
        return jsonify(final_output.model_dump()), 200
        
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
    print("🚀 Starting Extraction Backend (LangGraph)...")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
