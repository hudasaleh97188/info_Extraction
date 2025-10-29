import os
from crewai import Agent, LLM
from src.tools import SchemaAnalyzerTool # DataExtractorTool removed for V1
from dotenv import load_dotenv
load_dotenv()

# Get API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- LLM Setup ---
# Initialize Gemini
# Make sure GOOGLE_API_KEY is set in your .env file
llm = LLM(
    model="gemini/gemini-2.5-flash",
    temperature=0,
    api_key=GEMINI_API_KEY
)
# --- End LLM Setup ---

def create_orchestrator_agent():
    """Main coordination agent, also acts as manager"""
    return Agent(
        role='Extraction Orchestrator & Manager', # Role updated
        goal='Coordinate the extraction process for a list of user requests by delegating schema analysis and data extraction tasks, ensuring the overall process completes successfully.', # Goal updated
        backstory="""You are an experienced project manager specializing in document processing.
        You receive a list of extraction tasks, each with an aim and schema.
        For each task, you first delegate to the Schema Analyzer to get the prompt and Pydantic model string.
        Then, you delegate to the Extraction Specialist using the generated prompt/model string and the document content.
        You collect results for all tasks, manage the workflow, and provide a final aggregated list.""",
        llm=llm,
        verbose=True,
        allow_delegation=True # Essential for managing and delegating
    )

def create_schema_analyzer_agent():
    """Schema analysis and prompt engineering agent"""
    return Agent(
        role='Schema Analyzer & Prompt Engineer',
        goal='Analyze a single extraction schema and create an optimal extraction prompt and a Pydantic model definition string.',
        backstory="""You are a technical architect specializing in data modeling and prompt engineering.
        You receive a task aim and schema fields and generate:
        1. A clear, effective prompt for an LLM to extract data matching the schema.
        2. A Python string defining a Pydantic model for validating the extracted data.""",
        llm=llm,
        tools=[SchemaAnalyzerTool()],
        verbose=True,
        allow_delegation=False
    )

def create_extraction_specialist_agent():
    """Data extraction agent"""
    return Agent(
        role='Extraction Specialist',
        goal='Extract structured data from document markdown based on a given prompt and Pydantic model definition string.',
        backstory="""You are a meticulous data extraction expert. You follow instructions precisely.
        You receive document content (markdown), an extraction prompt, and a Pydantic model definition string.
        Your task is to extract the relevant information from the markdown according to the prompt
        and return it as a JSON string that *should* conform to the Pydantic model definition.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

def create_validation_agent():
    """JSON validation and formatting agent"""
    return Agent(
        role='JSON Validation & Formatting Specialist',
        goal='Validate and format extracted JSON data to ensure it meets the required schema and is properly structured.',
        backstory="""You are a data quality specialist with expertise in JSON validation and formatting.
        You receive raw extracted data (which may be malformed JSON, plain text, or other formats)
        and a target schema. Your job is to:
        1. Parse and validate the input data
        2. Ensure it conforms to the expected JSON structure
        3. Fix any formatting issues
        4. Return clean, valid JSON that matches the schema requirements
        5. Handle errors gracefully and provide meaningful error messages when data cannot be extracted.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )