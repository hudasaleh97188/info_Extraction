import pytest
from src.lg_helpers import SchemaAnalyzer, try_parse_json_like_string

@pytest.mark.unit
def test_schema_analyzer_single_row():
    """
    Tests the SchemaAnalyzer with a single-row extraction task.
    """
    analyzer = SchemaAnalyzer()
    task_aim = "Extract invoice details"
    schema_fields = [
        {"name": "invoice_id", "type": "string", "mandatory": True},
        {"name": "total_amount", "type": "number", "description": "The total amount due"},
    ]
    
    result = analyzer.run(task_aim, schema_fields, multi_row=False)

    assert "pydantic_model_string" in result
    assert "extraction_prompt" in result
    assert result["result_class_name"] == "ExtractedItem"
    assert result["is_multi_row"] is False
    
    # Check Pydantic model string
    assert "class ExtractedItem(BaseModel):" in result["pydantic_model_string"]
    assert "invoice_id: str" in result["pydantic_model_string"]
    assert "total_amount: Optional[float] = Field(description='The total amount due')" in result["pydantic_model_string"]
    assert "class ExtractionResult(ExtractedItem):" in result["pydantic_model_string"]

    # Check extraction prompt
    assert task_aim in result["extraction_prompt"]
    assert "invoice_id** (string, MANDATORY)" in result["extraction_prompt"]
    assert "total_amount** (number, Optional) - The total amount due" in result["extraction_prompt"]
    assert "Return a single JSON object" in result["extraction_prompt"]

@pytest.mark.unit
def test_schema_analyzer_multi_row():
    """
    Tests the SchemaAnalyzer with a multi-row extraction task.
    """
    analyzer = SchemaAnalyzer()
    task_aim = "Extract line items"
    schema_fields = [
        {"name": "item_description", "type": "string"},
        {"name": "quantity", "type": "number", "mandatory": True},
    ]

    result = analyzer.run(task_aim, schema_fields, multi_row=True)

    assert result["result_class_name"] == "ExtractionResult"
    assert result["is_multi_row"] is True

    # Check Pydantic model string
    assert "class ExtractionResult(BaseModel):" in result["pydantic_model_string"]
    assert "data: List[ExtractedItem]" in result["pydantic_model_string"]

    # Check extraction prompt
    assert "Return a JSON object with a single key 'data' containing a list/array of items" in result["extraction_prompt"]

@pytest.mark.unit
@pytest.mark.parametrize("input_string, expected_output", [
    ('{"key": "value"}', {"key": "value"}),
    ('[{"key": "value"}]', [{"key": "value"}]),
    ('```json\n{"key": "value"}\n```', {"key": "value"}),
    ("Some text around a json {\"key\": \"value\"} more text", {"key": "value"}),
    ("This is not a json string", "This is not a json string"),
    ("{'key': 'value'}", {"key": "value"}), # Test literal_eval
    ("None", None),
    (None, None)
])
def test_try_parse_json_like_string(input_string, expected_output):
    """
    Tests the try_parse_json_like_string function with various inputs.
    """
    assert try_parse_json_like_string(input_string) == expected_output
