from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class SchemaField(BaseModel):
    """Definition of a single schema field"""
    name: str
    type: str  # string, number, boolean, date
    description: Optional[str] = ""
    mandatory: bool = False
    multi_row: bool = False

class ExtractionTask(BaseModel):
    """User-defined extraction task"""
    aim: str
    schema: List[SchemaField]

class ExtractionInput(BaseModel):
    """Input for the extraction crew"""
    markdown_content: str
    tasks: List[ExtractionTask]

class TaskResult(BaseModel):
    """Result of a single extraction task"""
    task_aim: str
    status: str
    data: Any
    error: Optional[str] = None
