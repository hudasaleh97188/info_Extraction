import os
import json
import base64
import tempfile
import requests
import re
import ast
from typing import List, Dict, Any, Optional, Tuple

from dotenv import load_dotenv
from PIL import Image
from mistralai import Mistral

# Import Pydantic models from your models.py
from src.models import ExtractionTask
from src.utils.logging_config import default_logger


# Load environment variables
load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
_mistral_client = Mistral(api_key=MISTRAL_API_KEY) if MISTRAL_API_KEY else None

# --- MOCK OCR ---

def get_mock_markdown() -> str:
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

# --- Mistral OCR Functions ---

def perform_mistral_ocr(file_data: str, file_name: str, file_type: str) -> str:
    """Extract Markdown via Mistral Vision chat API (pixtral), matching ocr_test approach.

    - Accepts base64 file data; converts PDFs to page images or images directly to base64 URL
    - Sends vision prompt asking for clean Markdown
    - Returns Markdown string
    """
    default_logger.info(f"Attempting Mistral OCR for {file_name} via chat.complete...")
    if _mistral_client is None:
        raise ValueError("MISTRAL_API_KEY is not set. Please add it to your .env file.")

    # Prepare local temp file from base64
    local_path, local_mime = _write_temp_file_from_base64(file_data, file_name, file_type)
    temp_images: List[str] = []
    try:
        image_paths: List[str] = []
        if local_mime == 'application/pdf' or (local_path.lower().endswith('.pdf')):
            # Convert PDF pages to images
            from pdf2image import convert_from_path
            pages = convert_from_path(local_path)
            for i, page in enumerate(pages):
                img_path = f"_mistral_temp_page_{i}.png"
                page.save(img_path, "PNG")
                image_paths.append(img_path)
                temp_images.append(img_path)
        else:
            image_paths.append(local_path)

        prompt = (
            "Extract all text from this document using OCR and return clean Markdown only. "
            "Use headings, lists, and Markdown tables where appropriate."
        )

        markdown_parts: List[str] = []
        for idx, img_path in enumerate(image_paths):
            with open(img_path, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')

            resp = _mistral_client.chat.complete(
                model="pixtral-12b-2409",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": f"data:image/png;base64,{b64}"},
                        ],
                    }
                ],
            )

            # Prefer output_text; fallback to choices/message.content
            page_md = getattr(resp, "output_text", None)
            if not page_md:
                choices = getattr(resp, "choices", None)
                if choices:
                    msg = getattr(choices[0], "message", None)
                    if msg is not None:
                        content = getattr(msg, "content", None)
                        if isinstance(content, str):
                            page_md = content
                        elif isinstance(content, list):
                            texts = [c.get("text") for c in content if isinstance(c, dict) and c.get("type") == "text"]
                            page_md = "\n".join([t for t in texts if t]) if texts else None
            if not page_md:
                page_md = f"(No OCR text returned for page {idx+1})"
            markdown_parts.append(f"## Page {idx+1}\n\n{page_md}")

        md_header = f"# OCR Output for {file_name} (Mistral)\n\n"
        final_md = md_header + "\n\n---\n\n".join(markdown_parts)
        default_logger.info("✅ Mistral OCR successful.")
        return final_md
    finally:
        # Cleanup temp files
        try:
            if os.path.exists(local_path): os.remove(local_path)
            for p in temp_images:
                if os.path.exists(p): os.remove(p)
        except Exception:
            pass

def _write_temp_file_from_base64(file_data_b64: str, file_name: str, file_type: str) -> Tuple[str, str]:
    """Writes base64 data to a temp file and returns its path and mime type."""
    guessed_ext = '.pdf'
    if file_type:
        if file_type == 'application/pdf': guessed_ext = '.pdf'
        elif file_type.startswith('image/'): guessed_ext = f'.{file_type.split("/")[-1]}'
    elif file_name and '.' in file_name:
        guessed_ext = os.path.splitext(file_name)[1]
    
    fd, temp_path = tempfile.mkstemp(suffix=guessed_ext)
    os.close(fd)
    with open(temp_path, 'wb') as f:
        f.write(base64.b64decode(file_data_b64))
    return temp_path, file_type

def _image_to_pdf(image_path: str) -> str:
    """Converts an image file to a temporary PDF."""
    with Image.open(image_path) as img:
        img_converted = img.convert('RGB')
        fd, pdf_path = tempfile.mkstemp(suffix='.pdf')
        os.close(fd)
        img_converted.save(pdf_path, format='PDF')
        return pdf_path

def _extract_text_from_mistral_response(data: Dict[str, Any]) -> str:
    """Extracts plain text from a Mistral OCR response."""
    try:
        if isinstance(data, dict):
            content_blocks = data.get('content', [])
            if isinstance(content_blocks, list):
                texts = [
                    block['text'] 
                    for block in content_blocks 
                    if isinstance(block, dict) and 
                       block.get('type') == 'string' and 
                       block.get('text')
                ]
                if texts:
                    return "\n\n".join(texts)
    except Exception as e:
        default_logger.info(f"Error parsing Mistral response: {e}")
        pass
    return ""

# --- Schema and Parsing Helpers ---

class SchemaAnalyzer:
    """Ported logic from tools.py:SchemaAnalyzerTool."""
    
    def _map_type(self, field_type: str) -> str:
        """Map user types to Python types"""
        type_mapping = {
            'string': 'str',
            'number': 'float',
            'boolean': 'bool',
            'date': 'str'  # Keep as string for simplicity in LLM extraction
        }
        return type_mapping.get(field_type.lower(), 'str')

    def run(self, task_aim: str, schema_fields_raw: List[Dict], multi_row: bool) -> Dict[str, Any]:
        """Generate extraction prompt and Pydantic model string."""
        try:
            fields = schema_fields_raw
            
            model_lines = ["from pydantic import BaseModel, Field", "from typing import Optional, List\n"]
            
            # --- Pydantic Model String Generation ---
            model_lines.append("class ExtractedItem(BaseModel):")
            model_lines.append("    \"\"\"Represents a single extracted item based on the schema\"\"\"")
            
            if not fields:
                 model_lines.append("    pass # No fields defined")

            for field in fields:
                field_name = field['name']
                field_type_mapped = self._map_type(field['type'])
                field_desc = field.get('description', '').replace("'", "\\'") # Escape quotes
                is_mandatory = field.get('mandatory', False)
                
                field_type_final = f"Optional[{field_type_mapped}]" if not is_mandatory else field_type_mapped
                
                if field_desc:
                    model_lines.append(f"    {field_name}: {field_type_final} = Field(description='{field_desc}')")
                else:
                    model_lines.append(f"    {field_name}: {field_type_final}")
            
            model_lines.append("\n")
            
            if multi_row:
                model_lines.append("class ExtractionResult(BaseModel):")
                model_lines.append("    data: List[ExtractedItem]")
                result_class_name = "ExtractionResult"
                output_format_desc = "Return a JSON object with a single key 'data' containing a list/array of items. Each item in the list should match the 'ExtractedItem' schema."
            else:
                model_lines.append("# Not a multi-row task. The root object is 'ExtractedItem'.")
                model_lines.append("class ExtractionResult(ExtractedItem):")
                model_lines.append("    pass # The root model is the item itself")
                result_class_name = "ExtractedItem" # The root model is the item itself
                output_format_desc = "Return a single JSON object matching the 'ExtractedItem' schema."

            pydantic_model_string = "\n".join(model_lines)
            
            # --- Extraction Prompt Generation ---
            prompt = f"**Extraction Task Aim:**\n{task_aim}\n\n"
            prompt += "**Required Schema (as 'ExtractedItem'):**\n"
            
            for field in fields:
                mandatory_label = "MANDATORY" if field.get('mandatory') else "Optional"
                desc = f" - {field.get('description')}" if field.get('description') else ""
                prompt += f"- **{field['name']}** ({field['type']}, {mandatory_label}){desc}\n"
            
            prompt += f"\n**Required Output Format:**\n{output_format_desc}"
            prompt += "\n\n**Instructions:**\n"
            prompt += "1.  Carefully read the document content to find the information.\n"
            prompt += "2.  Extract all information matching the schema.\n"
            prompt += "3.  Format the output *exactly* as requested in the 'Required Output Format' section.\n"
            prompt += "4.  If a mandatory field is not found, set its value to `null`.\n"
            prompt += "5.  If an optional field is not found, omit it or set it to `null`.\n"
            
            result = {
                "pydantic_model_string": pydantic_model_string,
                "extraction_prompt": prompt,
                "result_class_name": result_class_name,
                "is_multi_row": multi_row
            }
            
            return result
            
        except Exception as e:
            default_logger.info(f"[Error] Schema analysis failed: {e}")
            import traceback; traceback.print_exc();
            return {"error": f"Schema analysis failed: {str(e)}"}


def try_parse_json_like_string(s: str) -> Any:
    """Try several strategies to parse a string that might contain JSON/list data."""
    if not isinstance(s, str):
        return s
    try:
        text = s.strip()
        # Strip markdown fences ```json ... ``` or ``` ... ```
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\n?|```$", "", text).strip()
        
        # Try standard JSON parsing first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass # Continue to other methods

        # Try to find a JSON array or object inside the text
        match = re.search(r"(\{.*\})|(\[.*\])", text, re.DOTALL)
        if match:
            candidate = match.group(0)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass # Continue
        
        # Last resort: Python literal eval (handles single quotes, etc.)
        try:
            return ast.literal_eval(text)
        except (ValueError, SyntaxError):
            pass

        # If all parsing fails, return the original (cleaned) string
        return text
    except Exception:
        return s # Return original string if any error occurs