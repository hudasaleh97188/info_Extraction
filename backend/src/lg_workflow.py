import os
import json
from typing import List, Dict, Any, Optional, TypedDict

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# LangGraph and LangChain imports
from langgraph.graph import StateGraph, END, MessagesState
from langchain_google_genai import ChatGoogleGenerativeAI

# Import Pydantic models from your models.py

from src.models import TaskResult, FinalExtractionOutput, ExtractionTask

# Import prompts
from src.prompts_lg import get_extraction_prompt, get_validation_prompt

# Import helpers
from src.lg_helpers import (
    get_mock_markdown, 
    perform_mistral_ocr,
    SchemaAnalyzer,
    try_parse_json_like_string
)

# --- Load Environment & LLM ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables.")

# Initialize Gemini 2.5 Flash
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    google_api_key=GEMINI_API_KEY,
    temperature=0,
    generation_config={"response_mime_type": "application/json"},
)

# --- MOCK OCR FLAG ---
USE_MOCK_OCR = False # Set to True to use mock markdown for testing
# ---------------------

# --- State Definition ---

class ExtractionGraphState(TypedDict):
    """Holds the state for the entire extraction process."""
    
    # Input from the user (this will be the input to the graph)
    original_input: Dict[str, Any]
    
    # State for the document
    markdown_content: str
    
    # State for the loop
    tasks_to_process: List[Dict] # A queue of tasks
    current_task: Optional[Dict] # The task currently being processed
    completed_results: List[TaskResult] # An accumulator for results
    
    # Intermediate state for a single task
    current_analysis_result: Optional[Dict] # Output from analyzer
    current_raw_json: Optional[str]         # Output from extractor
    
    # Final output
    final_output: Optional[FinalExtractionOutput]
    
    # We can also add messages to trace the LLM calls
    messages: MessagesState

# --- Graph Nodes ---

def prepare_document_node(state: ExtractionGraphState) -> Dict[str, Any]:
    """
    Node to prepare the document:
    1. Validates input tasks.
    2. Performs OCR (real or mock) to get markdown.
    """
    print("--- (Node) prepare_document ---")
    inputs = state['original_input']
    markdown_content = ""
    tasks_to_process = []
    
    try:
        # 1. Validate Tasks
        tasks_data = inputs.get('tasks', [])
        if not tasks_data or not isinstance(tasks_data, list):
            raise ValueError("Input 'tasks' must be a non-empty list.")
        
        valid_tasks = [ExtractionTask(**task) for task in tasks_data]
        tasks_to_process = [task.model_dump() for task in valid_tasks]
        print(f"✅ Validated {len(tasks_to_process)} tasks.")

        # 2. Perform OCR
        if USE_MOCK_OCR:
            print(" MOCKING OCR: Using predefined markdown content.")
            markdown_content = get_mock_markdown()
        else:
            print(" ATTEMPTING REAL OCR (Mistral)...")
            markdown_content = perform_mistral_ocr(
                inputs.get('file_data'),
                inputs.get('file_name'),
                inputs.get('file_type')
            )
        
        print(f"📄 Document Ready (Markdown Length: {len(markdown_content)} chars).")
        
        return {
            "markdown_content": markdown_content,
            "tasks_to_process": tasks_to_process,
            "completed_results": [], # Initialize empty results list
        }

    except Exception as e:
        print(f"❌ Failed during document preparation: {str(e)}")
        return {
            "final_output": FinalExtractionOutput(
                status="error",
                error=f"Preparation failed: {str(e)}"
            )
        }

def task_dispatcher_node(state: ExtractionGraphState) -> Dict[str, Any]:
    """
    Node to control the loop:
    1. Checks if tasks remain in the `tasks_to_process` queue.
    2. If yes, pops the next task and puts it in `current_task`.
    3. If no, sets `current_task` to None.
    """
    print("--- (Node) task_dispatcher ---")
    tasks_list = state.get("tasks_to_process", [])
    
    if not tasks_list:
        print("✅ All tasks processed.")
        return {"current_task": None}
        
    current_task = tasks_list.pop(0) # Get the next task
    print(f"🔹 Dispatching task: {current_task.get('aim')}")
    
    return {
        "tasks_to_process": tasks_list,
        "current_task": current_task,
        "current_analysis_result": None,
        "current_raw_json": None,
    }

def analyze_schema_node(state: ExtractionGraphState) -> Dict[str, Any]:
    """
    Node to analyze the schema for the current task.
    """
    print("--- (Node) analyze_schema ---")
    task = state.get("current_task")
    if not task:
        return {"error": "analyze_schema_node: No current task found."}

    try:
        analyzer = SchemaAnalyzer()
        analysis_result = analyzer.run(
            task_aim=task['aim'],
            schema_fields_raw=task['extraction_schema'],
            multi_row=task.get('multi_row', False)
        )
        
        if "error" in analysis_result:
            raise ValueError(analysis_result["error"])
            
        print("✅ Schema analysis complete.")
        return {"current_analysis_result": analysis_result}

    except Exception as e:
        print(f"❌ Schema analysis failed: {e}")
        error_result = TaskResult(
            task_aim=task['aim'],
            extracted_data=None,
            error=f"Schema analysis failed: {str(e)}"
        )
        completed_results = state.get("completed_results", []) + [error_result]
        return {
            "completed_results": completed_results,
            "current_task": None 
        }

def extract_data_node(state: ExtractionGraphState) -> Dict[str, Any]:
    """
    Node to perform the actual data extraction using the LLM.
    """
    print("--- (Node) extract_data ---")
    task = state.get("current_task")
    analysis_result = state.get("current_analysis_result")
    markdown = state.get("markdown_content")
    messages = state.get("messages", [])

    if not all([task, analysis_result, markdown is not None]):
        return {"error": "extract_data_node: Missing task, analysis, or markdown."}

    try:
        prompt_message = get_extraction_prompt(markdown, analysis_result)
        print("... Sending extraction prompt to LLM...")

        llm_response = llm.invoke([prompt_message])
        raw_json_output = llm_response.content
        
        print("✅ LLM returned raw extraction.")
        
        return {
            "current_raw_json": raw_json_output,
            "messages": messages + [prompt_message, llm_response]
        }

    except Exception as e:
        print(f"❌ LLM extraction call failed: {e}")
        error_result = TaskResult(
            task_aim=task['aim'],
            extracted_data=None,
            error=f"LLM extraction failed: {str(e)}"
        )
        completed_results = state.get("completed_results", []) + [error_result]
        return {
            "completed_results": completed_results,
            "current_task": None
        }

def validate_data_node(state: ExtractionGraphState) -> Dict[str, Any]:
    """
    Node to validate and clean the raw JSON from the extractor.
    """
    print("--- (Node) validate_data ---")
    task = state.get("current_task")
    raw_json = state.get("current_raw_json")
    analysis_result = state.get("current_analysis_result")
    messages = state.get("messages", [])
    
    if not all([task, analysis_result, raw_json is not None]):
        return {"error": "validate_data_node: Missing task, analysis, or raw_json."}
    
    task_aim = task['aim']
    
    try:
        prompt_message = get_validation_prompt(raw_json, analysis_result)
        print("... Sending validation prompt to LLM...")

        llm_response = llm.invoke([prompt_message])
        validated_json_string = llm_response.content
        
        print("✅ LLM returned cleaned JSON string.")

        parsed_data = try_parse_json_like_string(validated_json_string)
        
        new_result = TaskResult(
            task_aim=task_aim,
            extracted_data=parsed_data,
            raw_extracted_json=raw_json
        )
        
        completed_results = state.get("completed_results", []) + [new_result]
        print(f"✅ Task '{task_aim}' complete.")
        
        return {
            "completed_results": completed_results,
            "messages": messages + [prompt_message, llm_response]
        }

    except Exception as e:
        print(f"❌ LLM validation call failed: {e}")
        error_result = TaskResult(
            task_aim=task_aim,
            raw_extracted_json=raw_json,
            error=f"LLM validation failed: {str(e)}"
        )
        completed_results = state.get("completed_results", []) + [error_result]
        return {
            "completed_results": completed_results
        }

def finalize_graph_node(state: ExtractionGraphState) -> Dict[str, Any]:
    """
    Node to assemble the final output object.
    """
    print("--- (Node) finalize_graph ---")
    
    final_output = FinalExtractionOutput(
        status="success",
        markdown_length=len(state.get("markdown_content", "")),
        tasks_processed=len(state.get("completed_results", [])),
        results=state.get("completed_results", [])
    )
    
    print("✅ Graph run complete.")
    return {"final_output": final_output}


# --- Graph Wiring ---

def should_continue_loop(state: ExtractionGraphState) -> str:
    """Conditional edge: decides whether to loop or end."""
    if state.get("current_task"):
        return "continue"
    else:
        return "end"

def create_extraction_graph() -> StateGraph:
    """
    Creates and wires up the LangGraph workflow.
    """
    workflow = StateGraph(ExtractionGraphState)

    # Add nodes
    workflow.add_node("prepare_document", prepare_document_node)
    workflow.add_node("task_dispatcher", task_dispatcher_node)
    workflow.add_node("analyze_schema", analyze_schema_node)
    workflow.add_node("extract_data", extract_data_node)
    workflow.add_node("validate_data", validate_data_node)
    workflow.add_node("finalize_graph", finalize_graph_node)

    # Set entry point
    workflow.set_entry_point("prepare_document")

    # Add edges
    workflow.add_edge("prepare_document", "task_dispatcher")
    
    workflow.add_conditional_edges(
        "task_dispatcher",
        should_continue_loop,
        {
            "continue": "analyze_schema",
            "end": "finalize_graph"
        }
    )
    
    workflow.add_edge("analyze_schema", "extract_data")
    workflow.add_edge("extract_data", "validate_data")
    workflow.add_edge("validate_data", "task_dispatcher") # Loop back

    workflow.add_edge("finalize_graph", END)
    
    return workflow.compile()