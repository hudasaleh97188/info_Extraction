import pytest
from langchain_core.messages import HumanMessage
from src.prompts_lg import get_extraction_prompt, get_validation_prompt
from src.lg_helpers import SchemaAnalyzer

@pytest.mark.unit
def test_get_extraction_prompt(mock_markdown_content):
    """
    Tests that the extraction prompt is created correctly.
    """
    analyzer = SchemaAnalyzer()
    analysis_result = analyzer.run(
        task_aim="Extract invoice details",
        schema_fields_raw=[{"name": "invoice_id", "type": "string"}],
        multi_row=False
    )

    prompt_message = get_extraction_prompt(mock_markdown_content, analysis_result)

    assert isinstance(prompt_message, HumanMessage)
    content = prompt_message.content
    
    assert "Extract invoice details" in content
    assert "invoice_id** (string, Optional)" in content
    assert "DOCUMENT CONTENT (Markdown):" in content
    assert mock_markdown_content in content
    assert "return ONLY the valid JSON" in content

@pytest.mark.unit
def test_get_validation_prompt():
    """
    Tests that the validation prompt is created correctly.
    """
    raw_json = '{"invoice_id": "INV-123", "total": "2530.55"}'
    analyzer = SchemaAnalyzer()
    analysis_result = analyzer.run(
        task_aim="Extract invoice details",
        schema_fields_raw=[
            {"name": "invoice_id", "type": "string"},
            {"name": "total", "type": "number"}
        ],
        multi_row=False
    )

    prompt_message = get_validation_prompt(raw_json, analysis_result)

    assert isinstance(prompt_message, HumanMessage)
    content = prompt_message.content

    assert "You are a JSON Validation & Formatting Specialist" in content
    assert "TARGET SCHEMA:" in content
    assert "class ExtractedItem(BaseModel):" in content
    assert "invoice_id: Optional[str]" in content
    assert "total: Optional[float]" in content
    assert "RAW EXTRACTED DATA:" in content
    assert raw_json in content
    assert "Return ONLY the clean, valid JSON" in content
