import pytest

@pytest.fixture(scope="session")
def mock_markdown_content():
    """Returns a predefined markdown string for testing."""
    return """
# Sample Invoice INV-123
**Invoice Date:** October 26, 2025
**Due Date:** November 10, 2025
**Billed To:**
 Acme Corp
 123 Main St
 Anytown, CA 90210
**Contact:** John Doe (john.doe@acme.com)
---
## Items
| Description        | Quantity | Unit Price | Total |
|--------------------|----------|------------|-------|
| Web Development    | 1        | 1500.00    | 1500.00 |
| Graphic Design     | 5        | 100.00     | 500.00  |
| Cloud Hosting (Yr) | 1        | 300.50     | 300.50  |
---
**Subtotal:** 2300.50
**Tax (10%):** 230.05
**Total Amount Due:** **2530.55**
**Notes:** Payment due within 15 days.
---
# Meeting Minutes - Project Phoenix
**Date:** 2025-10-25
**Attendees:** Alice, Bob, Charlie
**Project Manager:** Alice Smith
**Decisions:**
- Q4 Budget Approved: $50,000
- Launch date set for Dec 1st, 2025.
**Action Items:**
- Bob: Finalize API documentation by Nov 5, 2025.
- Charlie: Prepare marketing brief by Oct 30, 2025.
    """

@pytest.fixture(scope="session")
def mock_extraction_tasks():
    """Provides a list of mock extraction tasks."""
    return [
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
            "aim": "List all action items from meeting minutes",
            "extraction_schema": [
                {"name": "assignee", "type": "string", "description": "Person assigned the action item"},
                {"name": "action_description", "type": "string", "description": "The task to be done"},
                {"name": "due_date", "type": "date", "description": "Deadline for the action item"}
            ],
            "multi_row": True
        }
    ]

@pytest.fixture(scope="session")
def mock_graph_input(mock_extraction_tasks):
    """Provides a mock input for the entire graph."""
    return {
        "original_input": {
            "file_data": None,
            "file_name": "mock_document.pdf",
            "file_type": "application/pdf",
            "tasks": mock_extraction_tasks
        }
    }
