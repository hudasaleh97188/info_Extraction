from crewai.tools import BaseTool
from typing import Type, List
from pydantic import BaseModel, Field, create_model
import json
import re

class SchemaAnalyzerInput(BaseModel):
    """Input for Schema Analyzer Tool"""
    task_aim: str = Field(..., description="The aim of the extraction task")
    schema_fields: str = Field(..., description="JSON string of schema fields")

class SchemaAnalyzerTool(BaseTool):
    name: str = "Schema Analyzer"
    description: str = "Analyzes user schema and generates extraction prompt with Pydantic model definition"
    args_schema: Type[BaseModel] = SchemaAnalyzerInput

    def _run(self, task_aim: str, schema_fields: str) -> str:
        """Generate extraction prompt and Pydantic model"""
        try:
            fields = json.loads(schema_fields)
            
            # Build Pydantic model string
            model_lines = ["from pydantic import BaseModel, Field", "from typing import Optional, List\n"]
            model_lines.append("class ExtractedData(BaseModel):")
            
            for field in fields:
                field_name = field['name']
                field_type = self._map_type(field['type'])
                field_desc = field.get('description', '')
                is_mandatory = field.get('mandatory', False)
                
                if not is_mandatory:
                    field_type = f"Optional[{field_type}]"
                
                if field_desc:
                    model_lines.append(f"    {field_name}: {field_type} = Field(description='{field_desc}')")
                else:
                    model_lines.append(f"    {field_name}: {field_type}")
            
            # Check if any field has multi_row
            has_multi_row = any(f.get('multi_row', False) for f in fields)
            
            if has_multi_row:
                model_lines.append("\nclass ExtractionResult(BaseModel):")
                model_lines.append("    data: List[ExtractedData]")
                result_class = "ExtractionResult"
            else:
                result_class = "ExtractedData"
            
            pydantic_model = "\n".join(model_lines)
            
            # Build extraction prompt
            prompt = f"""EXTRACTION TASK: {task_aim}

REQUIRED FIELDS TO EXTRACT:
"""
            for field in fields:
                mandatory_label = "MANDATORY" if field.get('mandatory') else "optional"
                desc = f" - {field.get('description')}" if field.get('description') else ""
                prompt += f"- {field['name']} ({field['type']}, {mandatory_label}){desc}\n"
            
            if has_multi_row:
                prompt += "\nOUTPUT FORMAT: Return a JSON array of items matching the schema.\n"
            else:
                prompt += "\nOUTPUT FORMAT: Return a single JSON object matching the schema.\n"
            
            prompt += "\nINSTRUCTIONS:"
            prompt += "\n1. Extract only the information requested"
            prompt += "\n2. If a mandatory field is missing, mark it as null and note the missing data"
            prompt += "\n3. Be precise and accurate"
            prompt += "\n4. Return valid JSON only, no additional text\n"
            
            result = {
                "pydantic_model": pydantic_model,
                "extraction_prompt": prompt,
                "result_class": result_class,
                "is_multi_row": has_multi_row
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({"error": f"Schema analysis failed: {str(e)}"})
    
    def _map_type(self, field_type: str) -> str:
        """Map user types to Python types"""
        type_mapping = {
            'string': 'str',
            'number': 'float',
            'boolean': 'bool',
            'date': 'str'  # We'll use string for dates
        }
        return type_mapping.get(field_type.lower(), 'str')


class DataExtractorInput(BaseModel):
    """Input for Data Extractor Tool"""
    markdown_content: str = Field(..., description="The markdown content to extract from")
    extraction_prompt: str = Field(..., description="The extraction prompt")
    pydantic_model: str = Field(..., description="The Pydantic model as string")

class DataExtractorTool(BaseTool):
    name: str = "Data Extractor"
    description: str = "Extracts structured data from markdown using LLM and validates against Pydantic model"
    args_schema: Type[BaseModel] = DataExtractorInput

    def _run(self, markdown_content: str, extraction_prompt: str, pydantic_model: str) -> str:
        """
        This tool returns instructions for the LLM agent to extract data.
        The actual extraction happens in the agent's execution.
        """
        full_prompt = f"""{extraction_prompt}

DOCUMENT CONTENT (Markdown):
{markdown_content}

VALIDATION SCHEMA:
{pydantic_model}

Extract the data and return ONLY valid JSON matching the schema. No additional commentary.
"""
        return full_prompt
