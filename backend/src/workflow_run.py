import json
from src.lg_workflow import create_extraction_graph
from src.models import FinalExtractionOutput # Import pydantic models
from typing import Dict, Any
from src.utils.logging_config import default_logger
def get_mock_inputs() -> Dict[str, Any]:
    """
    Generates sample input data matching frontend structure.
    """
    mock_tasks = [
        {
            "aim": "Extract invoice header details and total amount",
            "extraction_schema": [
                {"name": "invoice_id", "type": "string", "description": "The invoice number (e.g., INV-123)", "mandatory": True},
                {"name": "invoice_date", "type": "date", "description": "Date the invoice was issued"},
                {"name": "due_date", "type": "date", "description": "Payment due date"},
                {"name": "total_amount", "type": "number", "description": "The final total amount due", "mandatory": True}
            ],
            "multi_row": False
        },
        {
            "aim": "Extract billing contact information",
            "extraction_schema": [
                {"name": "company_name", "type": "string", "description": "Company name being billed"},
                {"name": "contact_person", "type": "string", "description": "Name of the contact person, if available"},
                {"name": "contact_email", "type": "string", "description": "Email of the contact person, if available"}
            ],
            "multi_row": False
        },
        {
            "aim": "List all action items from meeting minutes",
            "extraction_schema": [
                {"name": "assignee", "type": "string", "description": "Person assigned the action item"},
                {"name": "action_description", "type": "string", "description": "The task to be done"},
                {"name": "due_date", "type": "date", "description": "Deadline for the action item"}
            ],
            "multi_row": True
        }
    ]
    return {
        # File data can be None if USE_MOCK_OCR is True (set in langgraph_workflow.py)
        "file_data": None, 
        "file_name": "mock_document.pdf",
        "file_type": "application/pdf",
        "tasks": mock_tasks
    }

if __name__ == "__main__":
    default_logger.info("🚀 Compiling LangGraph extraction workflow...")
    
    # 1. Compile the graph
    app = create_extraction_graph()

    default_logger.info("✅ Graph compiled.")
    default_logger.info("--- Starting workflow run ---")

    # 2. Get inputs
    # We use mock inputs for this test
    inputs = get_mock_inputs()
    
    # This is the dict that your frontend will send
    graph_input = {"original_input": inputs}

    # 3. Run the graph
    # .stream() lets you see the steps as they happen
    # .invoke() just runs it and gives the final state
    
    # Using .invoke() for the final result:
    final_state = app.invoke(graph_input)
    
    default_logger.info("--- Workflow run finished ---")
    
    # 4. Get the final output
    final_output_model: FinalExtractionOutput = final_state.get("final_output")
    
    if final_output_model:
        # .model_dump_json() is the Pydantic v2 way
        default_logger.info(final_output_model.model_dump_json(indent=2))
    else:
        default_logger.info("Error: Graph finished in an unexpected state.")
        default_logger.info(json.dumps(final_state, indent=2, default=str))

