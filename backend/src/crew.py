import os
import json
import base64
import tempfile
import requests # Enabled for Nanonets
from typing import Dict, Any, List, Tuple

from PIL import Image  # For image -> PDF conversion

from dotenv import load_dotenv
load_dotenv() # Load .env file (e.g., for GOOGLE_API_KEY, NANONETS_API_KEY)

from crewai import Crew, Process
from crewai.project import CrewBase, agent, crew, before_kickoff
# Update model import to use the renamed field
from src.models import ExtractionInput, TaskResult, ExtractionTask, SchemaField
from src.agents import create_orchestrator_agent, create_schema_analyzer_agent, create_extraction_specialist_agent, create_validation_agent, llm # Import llm from agents
from src.tasks import coordinate_extractions_task

# --- MOCK OCR FLAG ---
USE_MOCK_OCR = False # Set to True to force mock markdown
# ---------------------

@CrewBase
class ExtractionCrew:
    """Document Extraction Crew using CrewAI with Hierarchical Process"""

    def __init__(self):
        self.markdown_content = ""
        self.user_tasks_input: List[Dict] = [] # Store raw task dicts from input

    @before_kickoff
    def prepare_document(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare document and create the input dictionary for the main task."""
        print("🔄 Preparing document...")
        try:
            tasks_data = inputs.get('tasks', [])
            # ... (Keep your existing task validation logic) ...
            if not tasks_data or not isinstance(tasks_data, list): raise ValueError("Input 'tasks' must be a non-empty list.")
            # ...(validation loop)...
            self.user_tasks_input = tasks_data
            print(f"📋 Received {len(self.user_tasks_input)} valid extraction tasks.")

            # Handle OCR
            if USE_MOCK_OCR:
                print(" MOCKING OCR: Using predefined markdown content.")
                self.markdown_content = self._get_mock_markdown()
            else:
                print(" ATTEMPTING REAL OCR...")
                # Call the real Nanonets conversion method
                self.markdown_content = self._convert_to_markdown(
                    inputs.get('file_data'),
                    inputs.get('file_name'),
                    inputs.get('file_type')
                )

            print(f"📄 Document Ready (Markdown Length: {len(self.markdown_content)} chars).")

            # --- Create the dictionary with keys matching ALL task placeholders ---
            tasks_summary_json = json.dumps(
                [{"aim": t.get("aim", "N/A"), "fields": len(t.get("extraction_schema", []))} for t in self.user_tasks_input],
                indent=2
            )
            tasks_full_json = json.dumps(self.user_tasks_input, indent=2)

            # *** Ensure all keys needed by the task description are present ***
            return {
                # These keys MUST match the placeholders {} in the task description
                "user_extraction_tasks_input": self.user_tasks_input, # Passed for context, though maybe not directly in description
                "markdown_content": self.markdown_content,           # Passed for context if needed elsewhere, and for length calculation
                "markdown_length": len(self.markdown_content),       # *** ADDED THIS KEY ***
                "tasks_summary_json": tasks_summary_json,
                "tasks_full_json": tasks_full_json
            }
            # --- End dictionary creation ---

        except Exception as e:
            # ... (Keep error handling) ...
            print(f"❌ Failed during document preparation: {str(e)}")
            import traceback; traceback.print_exc(); raise

    # --- Agent Definitions ---
    @agent
    def orchestrator(self) -> Any:
        return create_orchestrator_agent()

    @agent
    def schema_analyzer(self) -> Any:
        return create_schema_analyzer_agent()

    @agent
    def extraction_specialist(self) -> Any:
        return create_extraction_specialist_agent()

    @agent
    def validation_specialist(self) -> Any:
        return create_validation_agent()

    # --- Crew Definition ---
    # (Note: The user's file had a duplicate @crew definition, I've kept the corrected one)

    @crew
    def build_crew(self) -> Crew:
        """Builds the CrewAI crew with Hierarchical Process."""

        # *** CORRECTED: Call the task function ONLY with the agent ***
        # The description's placeholders {} will be filled automatically by kickoff
        main_task = coordinate_extractions_task(
            agent=self.orchestrator()
            # No other arguments needed here
        )

        return Crew(
            agents=[
                self.orchestrator(),
                self.schema_analyzer(),
                self.extraction_specialist(),
                self.validation_specialist()
            ],
            tasks=[main_task],
            process=Process.hierarchical, # Use hierarchical process
            manager_llm=llm, # Assign Gemini LLM to the manager
            # The orchestrator is automatically the manager
            verbose=True # High verbosity for debugging
        )

    # --- Helper Methods ---
    def _get_mock_markdown(self) -> str:
        """Returns a predefined markdown string for testing."""
        # (Same mock markdown as before)
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

**Agenda:**
1. Review Q3 Goals
2. Plan Q4 Roadmap
3. Budget Allocation

**Decisions:**
- Q4 Budget Approved: $50,000
- Launch date set for Dec 1st, 2025.

**Action Items:**
- Bob: Finalize API documentation by Nov 5, 2025.
- Charlie: Prepare marketing brief by Oct 30, 2025.
        """

    def _convert_to_markdown(self, file_data: str, file_name: str, file_type: str) -> str:
        """Send file to Nanonets FullText OCR. Converts images to PDF before upload.

        - Accepts base64-encoded `file_data` and metadata
        - If input is an image, convert to a temporary PDF for better OCR
        - Uploads via multipart/form-data to FullText endpoint
        - Returns markdown (or plain text wrapped in markdown if markdown not available)
        """
        print(f"Attempting REAL Nanonets OCR for {file_name}...")

        api_key = os.getenv("NANONETS_API_KEY")
        if not api_key:
            raise ValueError("NANONETS_API_KEY is not set. Please add it to your .env file.")

        # Prepare local temp file from base64
        local_path, local_mime = self._write_temp_file_from_base64(file_data, file_name, file_type)
        temp_pdf_path = None
        try:
            # Convert image to PDF if needed
            if local_mime and local_mime.startswith("image/"):
                temp_pdf_path = self._image_to_pdf(local_path)
                upload_path = temp_pdf_path
                upload_mime = "application/pdf"
            else:
                upload_path = local_path
                upload_mime = local_mime or "application/pdf"

            url = "https://app.nanonets.com/api/v2/OCR/FullText"

            files = [
                (
                    'file',
                    (os.path.basename(upload_path), open(upload_path, 'rb'), upload_mime)
                )
            ]
            # You can supply optional payload like {'urls': ['...']} but we're using direct file
            payload = {}

            response = requests.post(
                url,
                headers={},
                data=payload,
                files=files,
                auth=requests.auth.HTTPBasicAuth(api_key, ''),
                timeout=180
            )
            response.raise_for_status()

            data = response.json()
            # Try to extract text in a few likely shapes
            text = self._extract_text_from_fulltext_response(data)
            if not text:
                # Fallback to raw response text
                text = response.text

            # Wrap as simplistic markdown
            markdown = f"# OCR Output for {file_name}\n\n" + text
            print("✅ Nanonets FullText OCR successful.")
            return markdown
        except requests.exceptions.RequestException as e:
            print(f"❌ Nanonets request failed: {e}")
            raise RuntimeError(f"Nanonets OCR failed: {e}") from e
        finally:
            # Cleanup temp files
            try:
                if os.path.exists(local_path):
                    os.remove(local_path)
                if temp_pdf_path and os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)
            except Exception:
                pass

    def _write_temp_file_from_base64(self, file_data_b64: str, file_name: str, file_type: str) -> Tuple[str, str]:
        """Write base64 data to a temporary file and return path and mime type."""
        # Derive extension from file_type if possible
        guessed_ext = None
        if file_type:
            if file_type == 'application/pdf':
                guessed_ext = '.pdf'
            elif file_type.startswith('image/'):
                subtype = file_type.split('/')[-1]
                guessed_ext = f'.{subtype}'
        # Fallback to filename extension
        if not guessed_ext and file_name and '.' in file_name:
            guessed_ext = os.path.splitext(file_name)[1]
        if not guessed_ext:
            guessed_ext = '.pdf'

        fd, temp_path = tempfile.mkstemp(suffix=guessed_ext)
        os.close(fd)
        with open(temp_path, 'wb') as f:
            f.write(base64.b64decode(file_data_b64))
        return temp_path, file_type

    def _image_to_pdf(self, image_path: str) -> str:
        """Convert a single image file to a temporary PDF and return its path."""
        with Image.open(image_path) as img:
            img_converted = img.convert('RGB')
            fd, pdf_path = tempfile.mkstemp(suffix='.pdf')
            os.close(fd)
            img_converted.save(pdf_path, format='PDF')
            return pdf_path

    def _extract_text_from_fulltext_response(self, data: Dict[str, Any]) -> str:
        """Attempt to pull plain text from various possible Nanonets FullText response shapes."""
        try:
            # Common patterns seen in FullText responses
            # 1) { 'results': [ { 'page_data': [ { 'text': '...'}, ... ] } ] }
            if isinstance(data, dict):
                results = data.get('results') or data.get('result')
                if isinstance(results, list) and results:
                    texts: List[str] = []
                    for r in results:
                        page_data = r.get('page_data') or r.get('pages') or []
                        if isinstance(page_data, list):
                            for p in page_data:
                                if isinstance(p, dict) and p.get('text'):
                                    texts.append(p['text'])
                        elif isinstance(page_data, dict) and page_data.get('text'):
                            texts.append(page_data['text'])
                    if texts:
                        return "\n\n".join(texts)
            # 2) Some variants use 'ocr_text' or top-level 'text'
            for key in ('ocr_text', 'text'):
                if key in data and isinstance(data[key], str):
                    return data[key]
        except Exception:
            pass
        return ""


    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main extraction method.
        Expects inputs like {'file_data': (base64_string or None if mock), 'file_name': ..., 'file_type': ..., 'tasks': [ { 'aim': ..., 'extraction_schema': [...] } ]}
        """
        try:
            print(f"🚀 Starting extraction crew...")
            # Log inputs safely
            loggable_inputs = {k: (v[:50] + '...' if isinstance(v, str) and k == 'file_data' and v else v)
                               for k, v in inputs.items()}
            print(f" Inputs (file_data truncated): {loggable_inputs}")

            crew_instance = self.build_crew()

            # Kickoff: @before_kickoff runs first using 'inputs',
            # then its return value is passed as the actual inputs to the crew's tasks.
            final_result = crew_instance.kickoff(inputs=inputs)

            print("✅ Extraction crew finished!")
            print("\n" + "="*20 + " FINAL CREW RESULT " + "="*20)
            # Attempt to pretty-print if it looks like a list/dict, otherwise print raw
            try:
                if isinstance(final_result, (list, dict)):
                    print(json.dumps(final_result, indent=2))
                else:
                    print(final_result)
            except Exception: # Handle cases where final_result might not be JSON serializable
                    print(final_result)
            print("="*50 + "\n")

            return {
                "status": "success",
                "markdown_length": len(self.markdown_content),
                "tasks_processed": len(self.user_tasks_input),
                "results": final_result # This should be the list from Orchestrator
            }

        except Exception as e:
            print(f"❌ Extraction crew failed during run: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e)
            }

# --- Mock Input Data & Example Usage ---
def get_mock_inputs() -> Dict[str, Any]:
    """Generates sample input data matching frontend structure."""
    mock_tasks = [
        {
            "aim": "Extract invoice header details and total amount",
            "extraction_schema": [ # Use renamed field
                {"name": "invoice_id", "type": "string", "description": "The invoice number (e.g., INV-123)", "mandatory": True},
                {"name": "invoice_date", "type": "date", "description": "Date the invoice was issued"},
                {"name": "due_date", "type": "date", "description": "Payment due date"},
                {"name": "total_amount", "type": "number", "description": "The final total amount due", "mandatory": True}
            ]
        },
        {
            "aim": "Extract billing contact information",
            "extraction_schema": [ # Use renamed field
                {"name": "company_name", "type": "string", "description": "Company name being billed"},
                {"name": "contact_person", "type": "string", "description": "Name of the contact person, if available"},
                {"name": "contact_email", "type": "string", "description": "Email of the contact person, if available"}
            ]
        },
        {
            "aim": "List all action items from meeting minutes",
            "extraction_schema": [ # Use renamed field
                {"name": "assignee", "type": "string", "description": "Person assigned the action item"},
                {"name": "action_description", "type": "string", "description": "The task to be done"},
                {"name": "due_date", "type": "date", "description": "Deadline for the action item"}
            ]
            # multi_row hint removed from schema field level, handled by schema structure itself
        }
    ]
    return {
        # File data can be None if USE_MOCK_OCR is True
        "file_data": None, # Set to base64 string if USE_MOCK_OCR = False
        "file_name": "mock_document.pdf",
        "file_type": "application/pdf",
        "tasks": mock_tasks
    }

if __name__ == "__main__":
    print("Setting up and running Extraction Crew...")
    
    # --- To test the REAL OCR ---
    # 1. Set USE_MOCK_OCR = False at the top of the file
    # 2. Add NANONETS_API_KEY and NANONETS_MODEL_ID to your .env file
    # 3. Get a real file's base64 data
    #
    # try:
    #     with open("path/to/your/test.pdf", "rb") as f:
    #         file_bytes = f.read()
    #         file_data_b64 = base64.b64encode(file_bytes).decode('utf-8')
    # except Exception as e:
    #     print(f"Could not load test file: {e}")
    #     file_data_b64 = None

    # inputs = get_mock_inputs()
    # if not USE_MOCK_OCR:
    #     if file_data_b64:
    #         inputs["file_data"] = file_data_b64
    #         inputs["file_name"] = "your_test.pdf"
    #     else:
    #         print("WARNING: Real OCR enabled but no file data loaded. Exiting.")
    #         exit()
    #
    # --- To test with MOCK OCR ---
    # 1. Set USE_MOCK_OCR = True
    print("(Using MOCK OCR and inputs)")
    inputs = get_mock_inputs()

    
    extraction_crew_runner = ExtractionCrew()
    final_output = extraction_crew_runner.run(inputs)

    print("\n--- Main Script Finished ---")
    # No need to print again, already printed in run()
    # print("Final Output:")
    # print(json.dumps(final_output, indent=2))