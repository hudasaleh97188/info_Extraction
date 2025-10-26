from crewai import Task
import json

def create_planning_task(agent, extraction_input):
    """Create task for orchestrator to plan execution"""
    return Task(
        description=f"""Review the extraction request and plan the execution strategy.
        
        You have {len(extraction_input.tasks)} extraction task(s) to complete:
        
        {json.dumps([{"aim": t.aim, "fields": len(t.schema)} for t in extraction_input.tasks], indent=2)}
        
        Your responsibilities:
        1. Review each extraction task aim and schema
        2. Determine if tasks should be executed sequentially or if any can be parallelized
        3. Identify any dependencies between tasks
        4. Create an execution plan
        5. Coordinate with Schema Analyzer to generate prompts
        6. Coordinate with Extraction Specialist to perform extractions
        7. Aggregate all results into a final structured output
        
        Start by delegating the first task to the Schema Analyzer.
        """,
        agent=agent,
        expected_output="A complete extraction plan and coordination strategy"
    )

def create_schema_analysis_task(agent, task_data, task_index):
    """Create task for schema analyzer"""
    schema_json = json.dumps([s.dict() for s in task_data.schema])
    
    return Task(
        description=f"""Analyze the extraction schema and generate prompt + Pydantic model.
        
        TASK #{task_index}
        AIM: {task_data.aim}
        
        SCHEMA FIELDS:
        {schema_json}
        
        Your responsibilities:
        1. Use the Schema Analyzer tool to generate:
           - Extraction prompt with clear instructions
           - Pydantic model for validation
        2. Return the generated prompt and model
        3. Ensure the prompt is clear and unambiguous
        
        Use the Schema Analyzer tool with:
        - task_aim: "{task_data.aim}"
        - schema_fields: '{schema_json}'
        """,
        agent=agent,
        expected_output="Generated extraction prompt and Pydantic model definition"
    )

def create_extraction_task(agent, markdown_content, prompt_and_model):
    """Create task for extraction specialist"""
    return Task(
        description=f"""Extract structured data from the document using the provided prompt and schema.
        
        You have been given:
        1. An extraction prompt with clear instructions
        2. A Pydantic model for validation
        3. The document content in markdown format
        
        Your responsibilities:
        1. Carefully read the extraction prompt
        2. Analyze the markdown document
        3. Extract the requested information
        4. Validate extracted data against the Pydantic model
        5. Return data in valid JSON format
        
        IMPORTANT: Return ONLY the extracted JSON data, no additional text or explanation.
        
        Document content will be provided separately.
        Extraction prompt and schema: {prompt_and_model}
        """,
        agent=agent,
        expected_output="Structured JSON data matching the Pydantic schema",
        context=[markdown_content] if markdown_content else None
    )