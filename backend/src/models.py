from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class SchemaField(BaseModel):
    """Definition of a single schema field"""
    name: str
    type: str  # e.g., string, number, boolean, date
    description: Optional[str] = ""
    mandatory: bool = False
    # multi_row removed from here - it applies to the task, not the field

class ExtractionTask(BaseModel):
    """User-defined extraction task"""
    aim: str
    extraction_schema: List[SchemaField] # Renamed from 'schema'
    multi_row: bool = Field(default=False, description="Set to true if the aim is to extract a list of items matching the schema, rather than a single item.") # Added multi_row here

class ExtractionInput(BaseModel):
    """Input structure expected by the API/frontend"""
    # file_data, file_name, file_type are handled separately before crew kickoff
    tasks: List[ExtractionTask]

class TaskResult(BaseModel):
    """Result structure for a single extraction task processed by the crew"""
    task_aim: str
    # status: str # Status can be inferred
    extracted_data: Optional[Any] = None # Store validated data eventually
    raw_extracted_json: Optional[str] = None # Store the raw JSON from extractor
    error: Optional[str] = None

# You might add other models here as needed, e.g., for the final aggregated output
class FinalExtractionOutput(BaseModel):
     status: str
     markdown_length: Optional[int] = None
     tasks_processed: Optional[int] = None
     results: Optional[List[TaskResult]] = None
     error: Optional[str] = None