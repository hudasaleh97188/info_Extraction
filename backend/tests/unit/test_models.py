import pytest
from pydantic import ValidationError
from src.models import SchemaField, ExtractionTask, TaskResult, FinalExtractionOutput

@pytest.mark.unit
def test_schema_field_validation():
    """Tests validation for the SchemaField model."""
    # Valid data
    field = SchemaField(name="test_field", type="string")
    assert field.name == "test_field"
    assert field.type == "string"
    assert field.description == ""
    assert field.mandatory is False

    # Missing required fields
    with pytest.raises(ValidationError):
        SchemaField(type="string") # name is missing
    with pytest.raises(ValidationError):
        SchemaField(name="test_field") # type is missing

@pytest.mark.unit
def test_extraction_task_validation(mock_extraction_tasks):
    """Tests validation for the ExtractionTask model."""
    # Valid data from fixture
    task_data = mock_extraction_tasks[0]
    task = ExtractionTask(**task_data)
    assert task.aim == task_data["aim"]
    assert len(task.extraction_schema) == len(task_data["extraction_schema"])
    assert task.multi_row is False

    # Test default value for multi_row
    simple_task_data = {
        "aim": "Simple task",
        "extraction_schema": [{"name": "field1", "type": "string"}]
    }
    simple_task = ExtractionTask(**simple_task_data)
    assert simple_task.multi_row is False

    # Missing required fields
    with pytest.raises(ValidationError):
        ExtractionTask(extraction_schema=[]) # aim is missing
    with pytest.raises(ValidationError):
        ExtractionTask(aim="test aim") # extraction_schema is missing

@pytest.mark.unit
def test_task_result_model():
    """Tests the TaskResult model."""
    # With data
    result = TaskResult(
        task_aim="Test Aim",
        extracted_data={"key": "value"},
        raw_extracted_json='{"key": "value"}'
    )
    assert result.task_aim == "Test Aim"
    assert result.extracted_data == {"key": "value"}
    assert result.error is None

    # With error
    result_error = TaskResult(
        task_aim="Test Aim with Error",
        error="Something went wrong"
    )
    assert result_error.task_aim == "Test Aim with Error"
    assert result_error.extracted_data is None
    assert result_error.error == "Something went wrong"

@pytest.mark.unit
def test_final_output_model(mock_extraction_tasks):
    """Tests the FinalExtractionOutput model."""
    results = [TaskResult(task_aim=task["aim"]) for task in mock_extraction_tasks]
    
    # Success case
    final_output = FinalExtractionOutput(
        status="success",
        markdown_length=1000,
        tasks_processed=2,
        results=results
    )
    assert final_output.status == "success"
    assert final_output.tasks_processed == 2
    assert len(final_output.results) == 2

    # Error case
    final_output_error = FinalExtractionOutput(
        status="error",
        error="A major failure occurred."
    )
    assert final_output_error.status == "error"
    assert final_output_error.error == "A major failure occurred."
    assert final_output_error.results is None
