"""
DeepEval evaluation tests for bank statement extraction.

This module contains evaluation tests using DeepEval to assess the quality
of extracted data from bank statement images. Each test case:
1. Loads a bank statement image
2. Runs the extraction workflow
3. Evaluates the extracted results using DeepEval metrics
"""

import os
import json
import base64
import pytest
from pathlib import Path
from typing import Dict, Any, Optional

from deepeval import assert_test
from deepeval.metrics import GEval, AnswerRelevancy, Faithfulness
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from src.lg_workflow import create_extraction_graph
from src.models import FinalExtractionOutput


# Path to the uploads directory containing test images
UPLOADS_DIR = Path(__file__).parent.parent.parent.parent / "frontend" / "uploads"


def load_image_as_base64(image_path: Path) -> str:
    """Load an image file and convert it to base64 string."""
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
        base64_str = base64.b64encode(image_bytes).decode('utf-8')
        return base64_str


def get_bank_statement_extraction_tasks() -> list:
    """Define the extraction schema for bank statements."""
    return [
        {
            "aim": "Extract bank statement header information",
            "extraction_schema": [
                {
                    "name": "account_number",
                    "type": "string",
                    "description": "The bank account number",
                    "mandatory": True
                },
                {
                    "name": "account_holder_name",
                    "type": "string",
                    "description": "Name of the account holder",
                    "mandatory": True
                },
                {
                    "name": "statement_period_start",
                    "type": "date",
                    "description": "Start date of the statement period",
                    "mandatory": True
                },
                {
                    "name": "statement_period_end",
                    "type": "date",
                    "description": "End date of the statement period",
                    "mandatory": True
                },
                {
                    "name": "opening_balance",
                    "type": "number",
                    "description": "Opening balance at the start of the period",
                    "mandatory": True
                },
                {
                    "name": "closing_balance",
                    "type": "number",
                    "description": "Closing balance at the end of the period",
                    "mandatory": True
                }
            ],
            "multi_row": False
        },
        {
            "aim": "Extract all transactions from the bank statement",
            "extraction_schema": [
                {
                    "name": "transaction_date",
                    "type": "date",
                    "description": "Date of the transaction",
                    "mandatory": True
                },
                {
                    "name": "description",
                    "type": "string",
                    "description": "Description or memo of the transaction",
                    "mandatory": True
                },
                {
                    "name": "amount",
                    "type": "number",
                    "description": "Transaction amount (positive for deposits, negative for withdrawals)",
                    "mandatory": True
                },
                {
                    "name": "balance",
                    "type": "number",
                    "description": "Account balance after this transaction",
                    "mandatory": False
                }
            ],
            "multi_row": True
        }
    ]


def run_extraction_workflow(file_data: str, file_name: str, file_type: str) -> FinalExtractionOutput:
    """Run the extraction workflow and return the final output."""
    graph_input = {
        "original_input": {
            'file_data': file_data,
            'file_name': file_name,
            'file_type': file_type,
            'tasks': get_bank_statement_extraction_tasks()
        }
    }
    
    app_graph = create_extraction_graph()
    final_state = app_graph.invoke(graph_input)
    
    final_output = final_state.get("final_output")
    if final_output is None:
        raise ValueError("Graph finished without final_output")
    
    return final_output


def format_extracted_data_as_string(result: Dict[str, Any]) -> str:
    """Format extracted data as a readable string for evaluation."""
    if result is None:
        return "No data extracted"
    
    if isinstance(result, dict):
        return json.dumps(result, indent=2)
    elif isinstance(result, list):
        return json.dumps(result, indent=2)
    else:
        return str(result)


@pytest.mark.evaluation
@pytest.mark.integration
def test_bank_statement_1_deepeval():
    """
    Test Case 1: Evaluate extraction from Bank-Statement-Template-3-TemplateLab-1.jpg
    Uses DeepEval metrics to assess correctness, relevancy, and faithfulness.
    """
    # Load the image
    image_path = UPLOADS_DIR / "Bank-Statement-Template-3-TemplateLab-1.jpg"
    if not image_path.exists():
        pytest.skip(f"Test image not found: {image_path}")
    
    file_data = load_image_as_base64(image_path)
    file_name = image_path.name
    file_type = "image/jpeg"
    
    # Run extraction
    final_output = run_extraction_workflow(file_data, file_name, file_type)
    
    # Verify extraction succeeded
    assert final_output.status == "success", f"Extraction failed: {final_output.error}"
    assert final_output.results is not None, "No results returned"
    assert len(final_output.results) == 2, "Expected 2 task results"
    
    # Get extracted data
    header_result = next((r for r in final_output.results if "header" in r.task_aim.lower()), None)
    transactions_result = next((r for r in final_output.results if "transaction" in r.task_aim.lower()), None)
    
    assert header_result is not None, "Header extraction result not found"
    assert transactions_result is not None, "Transactions extraction result not found"
    
    # Format actual outputs
    header_actual = format_extracted_data_as_string(header_result.extracted_data)
    transactions_actual = format_extracted_data_as_string(transactions_result.extracted_data)
    
    # Expected outputs (based on typical bank statement structure)
    header_expected = """{
  "account_number": "Account number from statement",
  "account_holder_name": "Account holder name from statement",
  "statement_period_start": "Start date from statement",
  "statement_period_end": "End date from statement",
  "opening_balance": "Opening balance amount",
  "closing_balance": "Closing balance amount"
}"""
    
    transactions_expected = """Array of transaction objects with:
- transaction_date: Date of transaction
- description: Transaction description/memo
- amount: Transaction amount
- balance: Account balance after transaction"""
    
    # Define DeepEval metrics
    correctness_metric = GEval(
        name="Correctness",
        criteria="Determine if the extracted bank statement header information is correct. Check that all mandatory fields (account_number, account_holder_name, statement_period_start, statement_period_end, opening_balance, closing_balance) are present and contain valid values.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
        threshold=0.7,
        model="gemini-3-flash-preview"
    )
    
    relevancy_metric = AnswerRelevancy(
        threshold=0.7,
        model="gemini-3-flash-preview"
    )
    
    faithfulness_metric = Faithfulness(
        threshold=0.7,
        model="gemini-3-flash-preview"
    )
    
    # Create test cases
    header_test_case = LLMTestCase(
        input=f"Extract bank statement header information from {file_name}",
        actual_output=header_actual,
        expected_output=header_expected,
        retrieval_context=[final_output.results[0].raw_extracted_json or ""]
    )
    
    transactions_test_case = LLMTestCase(
        input=f"Extract all transactions from {file_name}",
        actual_output=transactions_actual,
        expected_output=transactions_expected,
        retrieval_context=[final_output.results[1].raw_extracted_json or ""]
    )
    
    # Run evaluations
    assert_test(header_test_case, [correctness_metric, relevancy_metric, faithfulness_metric])
    assert_test(transactions_test_case, [correctness_metric, relevancy_metric])


@pytest.mark.evaluation
@pytest.mark.integration
def test_bank_statement_2_deepeval():
    """
    Test Case 2: Evaluate extraction from Screenshot 2025-12-29 171447.png
    Uses DeepEval metrics to assess correctness, relevancy, and faithfulness.
    """
    # Load the image
    image_path = UPLOADS_DIR / "Screenshot 2025-12-29 171447.png"
    if not image_path.exists():
        pytest.skip(f"Test image not found: {image_path}")
    
    file_data = load_image_as_base64(image_path)
    file_name = image_path.name
    file_type = "image/png"
    
    # Run extraction
    final_output = run_extraction_workflow(file_data, file_name, file_type)
    
    # Verify extraction succeeded
    assert final_output.status == "success", f"Extraction failed: {final_output.error}"
    assert final_output.results is not None, "No results returned"
    assert len(final_output.results) == 2, "Expected 2 task results"
    
    # Get extracted data
    header_result = next((r for r in final_output.results if "header" in r.task_aim.lower()), None)
    transactions_result = next((r for r in final_output.results if "transaction" in r.task_aim.lower()), None)
    
    assert header_result is not None, "Header extraction result not found"
    assert transactions_result is not None, "Transactions extraction result not found"
    
    # Format actual outputs
    header_actual = format_extracted_data_as_string(header_result.extracted_data)
    transactions_actual = format_extracted_data_as_string(transactions_result.extracted_data)
    
    # Expected outputs
    header_expected = """Bank statement header with:
- Account number (mandatory)
- Account holder name (mandatory)
- Statement period dates (start and end, mandatory)
- Opening and closing balances (mandatory)"""
    
    transactions_expected = """List of transactions, each containing:
- Transaction date (mandatory)
- Description/memo (mandatory)
- Amount (mandatory, positive for deposits, negative for withdrawals)
- Balance after transaction (optional)"""
    
    # Define DeepEval metrics with stricter criteria
    correctness_metric = GEval(
        name="Correctness",
        criteria="Evaluate if the extracted bank statement data is accurate and complete. For header: verify all mandatory fields are present with correct data types. For transactions: verify each transaction has required fields and amounts are correctly formatted as numbers.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
        threshold=0.75,
        model="gemini-3-flash-preview"
    )
    
    relevancy_metric = AnswerRelevancy(
        threshold=0.75,
        model="gemini-3-flash-preview"
    )
    
    faithfulness_metric = Faithfulness(
        threshold=0.75,
        model="gemini-3-flash-preview"
    )
    
    # Create test cases
    header_test_case = LLMTestCase(
        input=f"Extract bank statement header information from {file_name}",
        actual_output=header_actual,
        expected_output=header_expected,
        retrieval_context=[header_result.raw_extracted_json or ""]
    )
    
    transactions_test_case = LLMTestCase(
        input=f"Extract all transactions from {file_name}",
        actual_output=transactions_actual,
        expected_output=transactions_expected,
        retrieval_context=[transactions_result.raw_extracted_json or ""]
    )
    
    # Run evaluations
    assert_test(header_test_case, [correctness_metric, relevancy_metric, faithfulness_metric])
    assert_test(transactions_test_case, [correctness_metric, relevancy_metric])


@pytest.mark.evaluation
@pytest.mark.integration
def test_bank_statement_3_deepeval():
    """
    Test Case 3: Evaluate extraction from 1761668198294-BankStatementChequing.png
    Uses DeepEval metrics to assess correctness, relevancy, and faithfulness.
    """
    # Load the image
    image_path = UPLOADS_DIR / "1761668198294-BankStatementChequing.png"
    if not image_path.exists():
        pytest.skip(f"Test image not found: {image_path}")
    
    file_data = load_image_as_base64(image_path)
    file_name = image_path.name
    file_type = "image/png"
    
    # Run extraction
    final_output = run_extraction_workflow(file_data, file_name, file_type)
    
    # Verify extraction succeeded
    assert final_output.status == "success", f"Extraction failed: {final_output.error}"
    assert final_output.results is not None, "No results returned"
    assert len(final_output.results) == 2, "Expected 2 task results"
    
    # Get extracted data
    header_result = next((r for r in final_output.results if "header" in r.task_aim.lower()), None)
    transactions_result = next((r for r in final_output.results if "transaction" in r.task_aim.lower()), None)
    
    assert header_result is not None, "Header extraction result not found"
    assert transactions_result is not None, "Transactions extraction result not found"
    
    # Check for errors
    if header_result.error:
        pytest.fail(f"Header extraction error: {header_result.error}")
    if transactions_result.error:
        pytest.fail(f"Transactions extraction error: {transactions_result.error}")
    
    # Format actual outputs
    header_actual = format_extracted_data_as_string(header_result.extracted_data)
    transactions_actual = format_extracted_data_as_string(transactions_result.extracted_data)
    
    # Expected outputs
    header_expected = """Complete bank statement header information including:
- Account number: string value
- Account holder name: string value  
- Statement period start: date value
- Statement period end: date value
- Opening balance: numeric value
- Closing balance: numeric value
All mandatory fields must be present."""
    
    transactions_expected = """Array of transaction objects. Each transaction must have:
- transaction_date: valid date
- description: non-empty string describing the transaction
- amount: numeric value (can be positive or negative)
- balance: numeric value (optional but preferred)
The list should contain all transactions visible in the statement."""
    
    # Define DeepEval metrics
    correctness_metric = GEval(
        name="Correctness",
        criteria="Assess the accuracy and completeness of extracted bank statement data. Verify that: 1) All mandatory fields in the header are present and contain valid values (account_number and account_holder_name as strings, dates in proper format, balances as numbers). 2) Transactions list contains all visible transactions with required fields populated. 3) Data types match the schema (dates are dates, amounts are numbers). 4) No hallucinated or incorrect values.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
        threshold=0.7,
        model="gemini-3-flash-preview"
    )
    
    relevancy_metric = AnswerRelevancy(
        threshold=0.7,
        model="gemini-3-flash-preview"
    )
    
    faithfulness_metric = Faithfulness(
        threshold=0.7,
        model="gemini-3-flash-preview"
    )
    
    # Create test cases
    header_test_case = LLMTestCase(
        input=f"Extract bank statement header information from {file_name}",
        actual_output=header_actual,
        expected_output=header_expected,
        retrieval_context=[header_result.raw_extracted_json or ""]
    )
    
    transactions_test_case = LLMTestCase(
        input=f"Extract all transactions from {file_name}",
        actual_output=transactions_actual,
        expected_output=transactions_expected,
        retrieval_context=[transactions_result.raw_extracted_json or ""]
    )
    
    # Run evaluations
    assert_test(header_test_case, [correctness_metric, relevancy_metric, faithfulness_metric])
    assert_test(transactions_test_case, [correctness_metric, relevancy_metric, faithfulness_metric])

