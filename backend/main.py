from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import traceback
import sys
import json

app = Flask(__name__)
# Switch to LangGraph workflow

from src.lg_workflow import create_extraction_graph


# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# --- Database bootstrap ---
try:
    from src.db import Base, engine, get_db
    from src.db_models import Template, Project, ExtractionTaskORM, SchemaFieldORM, ExtractionResult
    Base.metadata.create_all(bind=engine)
except Exception as e1:
    # Fallback path adjust like lg_workflow import
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.join(current_dir, 'src')
        if src_dir not in sys.path:
            sys.path.append(src_dir)
        from db import Base, engine, get_db  # type: ignore
        from db_models import Template, Project, ExtractionTaskORM, SchemaFieldORM, ExtractionResult  # type: ignore
        Base.metadata.create_all(bind=engine)
    except Exception as e2:
        print("⚠️ Database bootstrap failed. First error:", repr(e1))
        print("⚠️ Database bootstrap fallback import failed. Second error:", repr(e2))
        # DB layer optional for legacy /extract usage
        Base = None  # type: ignore


def serialize_task(task: "ExtractionTaskORM"):
    return {
        "id": task.id,
        "aim": task.aim,
        "multi_row": task.multi_row,
        "template_id": task.template_id,
        "project_id": task.project_id,
        "fields": [
            {
                "id": f.id,
                "name": f.name,
                "type": f.type,
                "description": f.description,
                "mandatory": f.mandatory,
            }
            for f in task.fields
        ],
        "created_at": task.created_at.isoformat(),
    }


def serialize_project(p: "Project"):
    return {
        "id": p.id,
        "name": p.name,
        "file_path": p.file_path,
        "file_type": p.file_type,
        "template_id": p.template_id,
        "created_at": p.created_at.isoformat(),
        "num_tasks": len(p.tasks),
    }


def serialize_template(t: "Template"):
    return {
        "id": t.id,
        "name": t.name,
        "created_at": t.created_at.isoformat(),
        "tasks": [serialize_task(task) for task in t.tasks],
    }


def serialize_result(r: "ExtractionResult"):
    return {
        "id": r.id,
        "project_id": r.project_id,
        "task_id": r.task_id,
        "data": json.loads(r.data) if r.data else None,
        "raw_extracted_json": r.raw_extracted_json,
        "error": r.error,
        "created_at": r.created_at.isoformat(),
    }


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
        project_id = data.get('project_id')  # optional: persist results under a project
        
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

        # Persist results if a project is provided and DB is available
        if project_id and Base is not None:
            try:
                from contextlib import contextmanager
                @contextmanager
                def _db():
                    gen = get_db()
                    db = next(gen)
                    try:
                        yield db
                    finally:
                        try:
                            next(gen)
                        except StopIteration:
                            pass

                with _db() as db:
                    results = final_output.results or []
                    # Map task_aim to a task row within this project if exists
                    tasks_rows = (
                        db.query(ExtractionTaskORM)
                        .filter(ExtractionTaskORM.project_id == project_id)
                        .all()
                    )
                    aim_to_task_id = {t.aim: t.id for t in tasks_rows}
                    for res in results:
                        task_id = aim_to_task_id.get(res.task_aim)
                        db.add(
                            ExtractionResult(
                                project_id=project_id,
                                task_id=task_id if task_id else tasks_rows[0].id if tasks_rows else None,  # best-effort
                                data=json.dumps(res.extracted_data) if res.extracted_data is not None else None,
                                raw_extracted_json=res.raw_extracted_json,
                                error=res.error,
                            )
                        )
                    db.commit()
            except Exception as _e:
                print(f"⚠️ Failed to persist extraction results: {_e}")

        # final_output is Pydantic; return JSON
        return jsonify(final_output.model_dump()), 200
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "error": "Extraction failed",
            "details": str(e)
        }), 500


@app.route('/templates', methods=['POST'])
def create_template():
    if Base is None:
        return jsonify({"error": "DB not initialized"}), 500
    payload = request.get_json() or {}
    name = payload.get("name")
    tasks = payload.get("tasks", [])
    if not name:
        return jsonify({"error": "name is required"}), 400

    from contextlib import contextmanager
    @contextmanager
    def _db():
        gen = get_db()
        db = next(gen)
        try:
            yield db
        finally:
            try:
                next(gen)
            except StopIteration:
                pass

    with _db() as db:
        t = Template(name=name)
        db.add(t)
        db.flush()
        for task in tasks:
            task_orm = ExtractionTaskORM(
                template_id=t.id,
                aim=task.get("aim", ""),
                multi_row=bool(task.get("multi_row", False)),
            )
            db.add(task_orm)
            db.flush()
            for f in task.get("extraction_schema", task.get("schema", [])):
                db.add(
                    SchemaFieldORM(
                        task_id=task_orm.id,
                        name=f.get("name", ""),
                        type=f.get("type", "string"),
                        description=f.get("description"),
                        mandatory=bool(f.get("mandatory", False)),
                    )
                )
        db.commit()
        db.refresh(t)
        return jsonify(serialize_template(t)), 201


@app.route('/templates', methods=['GET'])
def list_templates():
    if Base is None:
        return jsonify({"templates": []})
    from contextlib import contextmanager
    @contextmanager
    def _db():
        gen = get_db()
        db = next(gen)
        try:
            yield db
        finally:
            try:
                next(gen)
            except StopIteration:
                pass
    with _db() as db:
        templates = db.query(Template).all()
        return jsonify([serialize_template(t) for t in templates])


@app.route('/projects', methods=['POST'])
def create_project():
    if Base is None:
        return jsonify({"error": "DB not initialized"}), 500
    payload = request.get_json() or {}
    name = payload.get("name")
    file_path = payload.get("file_path")
    file_type = payload.get("file_type")
    template_id = payload.get("template_id")
    if not name:
        return jsonify({"error": "name is required"}), 400

    from contextlib import contextmanager
    @contextmanager
    def _db():
        gen = get_db()
        db = next(gen)
        try:
            yield db
        finally:
            try:
                next(gen)
            except StopIteration:
                pass
    with _db() as db:
        p = Project(name=name, file_path=file_path, file_type=file_type, template_id=template_id)
        db.add(p)
        db.flush()
        # If template is referenced, clone its tasks into the project (not deep copy of ids)
        if template_id:
            tpl = db.query(Template).filter(Template.id == template_id).first()
            if tpl:
                for tt in tpl.tasks:
                    new_task = ExtractionTaskORM(project_id=p.id, aim=tt.aim, multi_row=tt.multi_row)
                    db.add(new_task)
                    db.flush()
                    for f in tt.fields:
                        db.add(
                            SchemaFieldORM(
                                task_id=new_task.id,
                                name=f.name,
                                type=f.type,
                                description=f.description,
                                mandatory=f.mandatory,
                            )
                        )
        db.commit()
        db.refresh(p)
        return jsonify(serialize_project(p)), 201


@app.route('/projects', methods=['GET'])
def list_projects():
    if Base is None:
        return jsonify([])
    from contextlib import contextmanager
    @contextmanager
    def _db():
        gen = get_db()
        db = next(gen)
        try:
            yield db
        finally:
            try:
                next(gen)
            except StopIteration:
                pass
    with _db() as db:
        projects = db.query(Project).all()
        return jsonify([serialize_project(p) for p in projects])


@app.route('/projects/<int:project_id>/tasks', methods=['GET'])
def list_project_tasks(project_id: int):
    if Base is None:
        return jsonify([])
    from contextlib import contextmanager
    @contextmanager
    def _db():
        gen = get_db()
        db = next(gen)
        try:
            yield db
        finally:
            try:
                next(gen)
            except StopIteration:
                pass
    with _db() as db:
        tasks = db.query(ExtractionTaskORM).filter(ExtractionTaskORM.project_id == project_id).all()
        return jsonify([serialize_task(t) for t in tasks])


@app.route('/projects/<int:project_id>/tasks', methods=['POST'])
def add_project_task(project_id: int):
    if Base is None:
        return jsonify({"error": "DB not initialized"}), 500
    payload = request.get_json() or {}
    aim = payload.get("aim")
    multi_row = bool(payload.get("multi_row", False))
    fields = payload.get("extraction_schema", payload.get("schema", []))
    if not aim:
        return jsonify({"error": "aim is required"}), 400

    from contextlib import contextmanager
    @contextmanager
    def _db():
        gen = get_db()
        db = next(gen)
        try:
            yield db
        finally:
            try:
                next(gen)
            except StopIteration:
                pass
    with _db() as db:
        # Ensure project exists
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            return jsonify({"error": "Project not found"}), 404
        task = ExtractionTaskORM(project_id=project_id, aim=aim, multi_row=multi_row)
        db.add(task)
        db.flush()
        for f in fields:
            db.add(
                SchemaFieldORM(
                    task_id=task.id,
                    name=f.get("name", ""),
                    type=f.get("type", "string"),
                    description=f.get("description"),
                    mandatory=bool(f.get("mandatory", False)),
                )
            )
        db.commit()
        db.refresh(task)
        return jsonify(serialize_task(task)), 201


@app.route('/projects/<int:project_id>/results', methods=['GET'])
def list_project_results(project_id: int):
    if Base is None:
        return jsonify([])
    from contextlib import contextmanager
    @contextmanager
    def _db():
        gen = get_db()
        db = next(gen)
        try:
            yield db
        finally:
            try:
                next(gen)
            except StopIteration:
                pass
    with _db() as db:
        results = db.query(ExtractionResult).filter(ExtractionResult.project_id == project_id).all()
        return jsonify([serialize_result(r) for r in results])


@app.route('/projects/<int:project_id>/results', methods=['POST'])
def save_project_result(project_id: int):
    if Base is None:
        return jsonify({"error": "DB not initialized"}), 500
    payload = request.get_json() or {}
    task_id = payload.get("task_id")
    data = payload.get("data")
    raw_extracted_json = payload.get("raw_extracted_json")
    error = payload.get("error")

    if not task_id:
        return jsonify({"error": "task_id is required"}), 400

    from contextlib import contextmanager
    @contextmanager
    def _db():
        gen = get_db()
        db = next(gen)
        try:
            yield db
        finally:
            try:
                next(gen)
            except StopIteration:
                pass
    with _db() as db:
        # Ensure project and task exist
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            return jsonify({"error": "Project not found"}), 404
        task = db.query(ExtractionTaskORM).filter(ExtractionTaskORM.id == task_id).first()
        if not task or task.project_id != project_id:
            return jsonify({"error": "Task not found in project"}), 404

        r = ExtractionResult(
            project_id=project_id,
            task_id=task_id,
            data=json.dumps(data) if data is not None else None,
            raw_extracted_json=raw_extracted_json,
            error=error,
        )
        db.add(r)
        db.commit()
        db.refresh(r)
        return jsonify(serialize_result(r)), 201


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
    
    app.run(host='0.0.0.0', port=5050, debug=True)
