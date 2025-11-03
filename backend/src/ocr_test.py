import os
import base64
from io import BytesIO
from PIL import Image
import requests
from pdf2image import convert_from_path  # Only needed for PDFs
from mistralai import Mistral  # New client per migration guide
from dotenv import load_dotenv

load_dotenv()
# Initialize Mistral client (replace with your API key)
api_key = os.getenv("MISTRAL_API_KEY")  # Or hardcode: "your_api_key_here"
if not api_key:
    raise RuntimeError("MISTRAL_API_KEY not set in environment.")
client = Mistral(api_key=api_key)

def encode_image_to_base64(image_path):
    """Encode image to base64 for API."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_pdf_pages_to_images(pdf_path):
    """Convert PDF pages to list of PIL Images."""
    return convert_from_path(pdf_path)

def ocr_to_markdown(file_path, model="pixtral-12b-2409"):  # Use 'pixtral' for vision OCR
    """Extract text from image/PDF as Markdown using Mistral."""
    if file_path.lower().endswith('.pdf'):
        pages = extract_pdf_pages_to_images(file_path)
        full_markdown = "# Extracted from PDF\n\n"
        for i, page in enumerate(pages):
            # Save temp image for each page
            temp_path = f"temp_page_{i}.png"
            page.save(temp_path, "PNG")
            page_md = process_single_image(temp_path, model)
            full_markdown += f"## Page {i+1}\n\n{page_md}\n\n---\n\n"
            os.remove(temp_path)  # Cleanup
        return full_markdown
    else:
        # Single image
        return process_single_image(file_path, model)

def process_single_image(image_path, model):
    """Process one image to Markdown."""
    base64_image = encode_image_to_base64(image_path)
    
    # Prompt for structured Markdown extraction (inspired by Mistral cookbook)
    prompt = """Extract all text from this image using OCR. Structure the output as clean Markdown:
- Use # for headings based on layout.
- Use bullet points or numbered lists for lists.
- Convert tables to Markdown tables (| Col1 | Col2 |).
- Preserve bold/italics with ** or *.
- Ignore backgrounds/noise; focus on readable text.
Output only the Markdown, no extra explanations."""

    # New SDK call
    resp = client.chat.complete(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64_image}"},
                ],
            }
        ],
    )

    # Robustly extract text across SDK variants
    text = None
    # Preferred: aggregated text
    text = getattr(resp, "output_text", None)
    if not text:
        # Try choices -> message.content (string) or content list
        choices = getattr(resp, "choices", None)
        if choices and len(choices) > 0:
            msg = getattr(choices[0], "message", None)
            if msg is not None:
                content = getattr(msg, "content", None)
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list) and len(content) > 0:
                    # Concatenate any text parts
                    parts = []
                    for part in content:
                        if isinstance(part, dict) and part.get("type") in ("text", "output_text"):
                            parts.append(part.get("text") or part.get("output_text"))
                    if parts:
                        text = "\n".join([p for p in parts if p])
    if not text:
        # Fallback to string conversion
        text = str(resp)

    return text

# Usage
file_path = "C:/Users/HudaGoian/Documents/Finance/info_Extraction/frontend/uploads/1761756260094-BankStatementChequing.png"  # Or .pdf
markdown_output = ocr_to_markdown(file_path)
print(markdown_output)

# Pass to another module, e.g.:
# other_module.process(markdown_output)