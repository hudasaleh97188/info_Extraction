"""
Prompts for the LangGraph-based extraction workflow.
"""
from typing import Dict, Any
from langchain_core.messages import HumanMessage

def get_extraction_prompt(
    markdown_content: str, 
    analysis_result: Dict[str, Any]
) -> HumanMessage:
    """
    Creates the prompt for the extraction node.
    
    This prompt combines the dynamically generated prompt from the 
    schema analysis with the full markdown content.
    """
    
    # Get the extraction prompt created by the 'analyze_schema_node'
    # This prompt already contains the schema, aim, and output format instructions.
    extraction_instructions = analysis_result.get("extraction_prompt", "Extract data based on the schema.")

    full_prompt = f"""
{extraction_instructions}

DOCUMENT CONTENT (Markdown):
---
{markdown_content}
---

Extract the data from the document content above and return ONLY the valid JSON 
that matches the requested output format. Do not include any other text, 
explanations, or markdown formatting.
"""
    return HumanMessage(content=full_prompt)


def get_validation_prompt(
    raw_json_string: str,
    analysis_result: Dict[str, Any]
) -> HumanMessage:
    """
    Creates the prompt for the validation node.
    
    This prompt instructs the LLM to act as a data quality specialist,
    cleaning and validating the raw output from the extraction node.
    """
    
    # Get the Pydantic model string created by the 'analyze_schema_node'
    pydantic_model_string = analysis_result.get("pydantic_model_string", "No schema provided.")
    
    # Get the target output format (single object or list)
    is_multi_row = analysis_result.get("is_multi_row", False)
    output_format_description = "a JSON array (list) of items" if is_multi_row else "a single JSON object"

    full_prompt = f"""
You are a JSON Validation & Formatting Specialist. Your job is to clean and validate
raw extracted data to ensure it perfectly matches the required schema.

TARGET SCHEMA:
---
{pydantic_model_string}
---

RAW EXTRACTED DATA:
---
{raw_json_string}
---

INSTRUCTIONS:
1.  Analyze the RAW EXTRACTED DATA. It might be malformed, contain extra text, or be missing quotes.
2.  Your goal is to produce a clean, valid JSON string that conforms to the TARGET SCHEMA.
3.  The final output MUST be {output_format_description}.
4.  If the raw data is completely unusable or contains no relevant information, return an empty {output_format_description} (e.g., `{{}}` or `[]`).
5.  Return ONLY the clean, valid JSON. Do not include any other text, explanations, or markdown formatting.
"""
    return HumanMessage(content=full_prompt)
