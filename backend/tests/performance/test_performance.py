import pytest
import time
from unittest.mock import MagicMock, patch
from src.lg_workflow import create_extraction_graph
from src.models import FinalExtractionOutput

@pytest.mark.performance
@patch("src.lg_workflow.perform_mistral_ocr")
@patch("src.lg_workflow.llm")
def test_graph_execution_time(mock_llm, mock_ocr, mock_graph_input, mock_markdown_content):
    """
    Measures the execution time of the graph with mocked external calls.
    This test ensures the graph's internal logic runs within an acceptable time frame.
    """
    # --- Arrange ---
    
    # Mock external services to isolate the graph's performance
    mock_ocr.return_value = mock_markdown_content
    mock_llm.invoke.return_value = MagicMock(content='{}') # Return empty JSON for simplicity

    # Compile the graph
    app = create_extraction_graph()
    
    # Define an acceptable time limit (in seconds)
    MAX_EXECUTION_TIME = 2.0 

    # --- Act ---
    
    start_time = time.perf_counter()
    final_state = app.invoke(mock_graph_input)
    end_time = time.perf_counter()
    
    execution_time = end_time - start_time
    print(f"\nGraph execution time: {execution_time:.4f} seconds")

    # --- Assert ---
    
    # Ensure the graph completed successfully
    assert "final_output" in final_state
    final_output = final_state["final_output"]
    assert isinstance(final_output, FinalExtractionOutput)
    assert final_output.status == "success"

    # Assert that the execution time is within the acceptable limit
    assert execution_time < MAX_EXECUTION_TIME
