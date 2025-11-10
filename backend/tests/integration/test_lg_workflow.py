import pytest
from unittest.mock import MagicMock, patch
from src.lg_workflow import create_extraction_graph
from src.models import FinalExtractionOutput

# This is an integration test because it tests the entire graph flow.
@pytest.mark.integration
@patch("src.lg_workflow.perform_mistral_ocr")
@patch("src.lg_workflow.llm")
def test_full_graph_execution_mocked_llm(mock_llm, mock_ocr, mock_graph_input, mock_extraction_tasks, mock_markdown_content):
    """
    Tests the full execution of the extraction graph with mocked LLM and OCR calls.
    It verifies that the graph can run from start to finish and produce
    the expected final output structure.
    """
    # --- Arrange ---
    
    # Mock the OCR function to return predefined markdown content
    mock_ocr.return_value = mock_markdown_content

    # Mock the LLM's `invoke` method.
    # The LLM is called twice per task: once for extraction, once for validation.
    mock_llm.invoke.side_effect = [
        # --- Task 1: Invoice Details ---
        # 1. Extraction response
        MagicMock(content='{"invoice_id": "INV-123", "total_amount": 2530.55}'),
        # 2. Validation response (usually the same if the first one is good)
        MagicMock(content='{"invoice_id": "INV-123", "total_amount": 2530.55}'),
        
        # --- Task 2: Action Items ---
        # 1. Extraction response
        MagicMock(content='{"data": [{"assignee": "Bob", "action_description": "Finalize API docs", "due_date": "Nov 5, 2025"}]}'),
        # 2. Validation response
        MagicMock(content='[{"assignee": "Bob", "action_description": "Finalize API docs", "due_date": "Nov 5, 2025"}]'),
    ]

    # Compile the graph
    app = create_extraction_graph()

    # --- Act ---
    
    # Run the graph with the mock input
    final_state = app.invoke(mock_graph_input)

    # --- Assert ---

    # 1. Check that the mocked OCR function was called
    mock_ocr.assert_called_once()

    # 2. Check that the LLM was called the correct number of times (2 tasks * 2 calls)
    assert mock_llm.invoke.call_count == 4

    # 3. Check the final output state
    assert "final_output" in final_state
    final_output = final_state["final_output"]
    
    assert isinstance(final_output, FinalExtractionOutput)
    assert final_output.status == "success"
    assert final_output.error is None
    assert final_output.tasks_processed == 2
    assert final_output.markdown_length == len(mock_markdown_content)

    # 4. Check the results for each task
    results = final_output.results
    assert len(results) == 2

    # Result for Task 1
    task1_result = results[0]
    assert task1_result.task_aim == mock_extraction_tasks[0]["aim"]
    assert task1_result.error is None
    assert task1_result.extracted_data == {"invoice_id": "INV-123", "total_amount": 2530.55}

    # Result for Task 2
    task2_result = results[1]
    assert task2_result.task_aim == mock_extraction_tasks[1]["aim"]
    assert task2_result.error is None
    assert isinstance(task2_result.extracted_data, list)
    assert task2_result.extracted_data[0]["assignee"] == "Bob"
