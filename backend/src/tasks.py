# src/tasks.py
from crewai import Task
# from models import ExtractionTask # Not strictly needed here anymore
import json

 # --- Main Task for Orchestrator ---
def coordinate_extractions_task(agent): # Removed arguments that are now passed via kickoff inputs
     """
     The primary task for the Orchestrator/Manager agent.
     Description uses CrewAI placeholders {} which are filled during kickoff.
     """
     # The description now uses {placeholders} that CrewAI will fill
     # using the dictionary returned by @before_kickoff
     return Task(
         description="""**Overall Goal:** Manage and execute the extraction process for the user-defined task(s) listed below on the provided document markdown.

         **Document Markdown Length:** {markdown_length} characters (The full markdown content is available in context).

         **User Task Summary:**
         ```json
         {tasks_summary_json}
         ```

         **Full User Task List (Reference this list for each task's details):**
         ```json
         {tasks_full_json}
         ```

         **Your Management Workflow (Execute for EACH task sequentially from the Full User Task List above):**

         **For the CURRENT task you are processing from the list:**
         1.  Identify the task's **index** (starting from 1) and its **aim**.
         2.  **Delegate Schema Analysis:**
             * **Delegate To:** `Schema Analyzer & Prompt Engineer`
             * **Action:** Instruct the delegate to analyze the 'aim' and 'extraction_schema' specific to **this current task** (retrieve these details from the Full User Task List based on the index/aim you identified). The delegate must return a JSON object containing 'extraction_prompt' and 'pydantic_model_string'.
             * **Wait** for the JSON result. Store it as `analysis_result`. Handle errors if the delegate fails.

         3.  **Delegate Data Extraction:**
             * **Delegate To:** `Extraction Specialist`
             * **Action:** Instruct the delegate to extract data from the **full document markdown** (available in context) using the `analysis_result['extraction_prompt']`. Also provide `analysis_result['pydantic_model_string']` for structural reference in the instructions. The delegate must return ONLY the extracted data as a valid JSON string.
             * **Wait** for the JSON string result. Store it as `raw_extracted_json`. Handle errors if the delegate fails.

         4.  **Delegate JSON Validation:**
             * **Delegate To:** `JSON Validation & Formatting Specialist`
             * **Action:** Instruct the delegate to validate and format the `raw_extracted_json` from Step 3. Provide the `analysis_result['pydantic_model_string']` as the target schema. The delegate must return clean, valid JSON that conforms to the schema.
             * **Wait** for the validated JSON result. Store it as `validated_json`. If validation fails, store an error message.

         5.  **Record Result:** Prepare a result dictionary for the current task containing:
             - `task_aim`: The original task 'aim' (retrieved from the Full User Task List)
             - `extracted_data`: The `validated_json` from Step 4
             - `task_index`: The task index (1-based)
             - `multi_row`: The multi_row flag from the task (if present)

         **Final Output Requirement:**
         After processing ALL tasks from the Full User Task List, compile and return ONLY a Python list containing the result dictionaries created in Step 5 for each task. Do NOT include any other text, explanations, or summaries.
         """,
         agent=agent,
         expected_output="""A Python list of dictionaries, one for each input task, like:
         [
           { 
             "task_aim": "Extract invoice details", 
             "extracted_data": {"invoice_id": "123", "total_amount": 99.5},
             "task_index": 1,
             "multi_row": false
           },
           { 
             "task_aim": "Find contact person", 
             "extracted_data": "Error: Schema analysis failed.",
             "task_index": 2,
             "multi_row": false
           },
           { 
             "task_aim": "List all products mentioned", 
             "extracted_data": [{"product_name": "Widget A"}],
             "task_index": 3,
             "multi_row": true
           }
         ]
         """
     )