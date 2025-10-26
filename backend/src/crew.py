from crewai import Crew, Process
from crewai.project import CrewBase, agent, crew, before_kickoff
from models import ExtractionInput, TaskResult
from agents import create_orchestrator_agent, create_schema_analyzer_agent, create_extraction_specialist_agent
import json
import requests
import base64
import os
from typing import Dict, Any, List

@CrewBase
class ExtractionCrew:
    """Document Extraction Crew using CrewAI"""
    
    def __init__(self):
        self.markdown_content = ""
        self.extraction_input = None
        self.results = []
    
    @before_kickoff
    def prepare_document(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare document by converting to markdown using Nanonets OCR
        This runs before the crew kicks off
        """
        print("🔄 Preparing document with OCR...")
        
        try:
            # Get file data from inputs
            file_data = inputs.get('file_data')
            file_name = inputs.get('file_name')
            file_type = inputs.get('file_type')
            
            if not file_data:
                raise ValueError("No file data provided")
            
            # Convert to markdown using Nanonets (or mock for testing)
            self.markdown_content = self._convert_to_markdown(file_data, file_name, file_type)
            
            # Store extraction input
            tasks_data = inputs.get('tasks', [])
            from models import ExtractionTask, SchemaField
            
            extraction_tasks = []
            for task_data in tasks_data:
                schema_fields = [SchemaField(**field) for field in task_data['schema']]
                extraction_tasks.append(ExtractionTask(aim=task_data['aim'], schema=schema_fields))
            
            self.extraction_input = ExtractionInput(
                markdown_content=self.markdown_content,
                tasks=extraction_tasks
            )
            
            print(f"✅ Document prepared. Markdown length: {len(self.markdown_content)} chars")
            print(f"✅ Tasks to process: {len(extraction_tasks)}")
            
            # Return modified inputs for the crew
            inputs['markdown_content'] = self.markdown_content
            inputs['extraction_input'] = self.extraction_input
            inputs['task_count'] = len(extraction_tasks)
            
            return inputs
            
        except Exception as e:
            print(f"❌ Error preparing document: {str(e)}")
            raise
    
    def _convert_to_markdown(self, file_data: str, file_name: str, file_type: str) -> str:
        """
        Convert file to markdown using Nanonets OCR API
        Falls back to mock data if API key not available
        """
        api_key = os.getenv('NANONETS_API_KEY')
        
        if api_key:
            try:
                # Decode base64 file data
                file_bytes = base64.b64decode(file_data)
                
                # Call Nanonets OCR API
                url = "https://app.nanonets.com/api/v2/OCR/FullText"
                
                files = {'file': (file_name, file_bytes, file_type)}
                response = requests.post(
                    url,
                    auth=requests.auth.HTTPBasicAuth(api_key, ''),
                    files=files,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Extract text from Nanonets response
                    markdown = self._extract_text_from_nanonets(result)
                    return markdown
                else:
                    print(f"⚠️ Nanonets API error: {response.status_code}")
                    return self._mock_markdown(file_name)
                    
            except Exception as e:
                print(f"⚠️ Nanonets API call failed: {str(e)}")
                return self._mock_markdown(file_name)
        else:
            print("⚠️ No Nanonets API key found, using mock markdown")
            return self._mock_markdown(file_name)
    
    def _extract_text_from_nanonets(self, result: Dict) -> str:
        """Extract and format text from Nanonets OCR result"""
        try:
            # Nanonets returns text in result['results'][0]['page_data'][0]['raw_text']
            pages = result.get('result', [{}])[0].get('page_data', [])
            text_parts = []
            
            for page in pages:
                raw_text = page.get('raw_text', '')
                if raw_text:
                    text_parts.append(raw_text)
            
            return "\n\n".join(text_parts)
        except Exception as e:
            print(f"Error extracting Nanonets text: {e}")
            return "Error processing OCR result"
    
    def _mock_markdown(self, file_name: str) -> str:
        """Generate mock markdown for testing"""
        return f"""# Invoice Document

**Invoice Number:** INV-2024-001
**Date:** October 26, 2025
**Due Date:** November 26, 2025

## Bill To:
Acme Corporation
123 Business St
New York, NY 10001

## Items:

| Item | Description | Quantity | Unit Price | Total |
|------|-------------|----------|------------|-------|
| 1 | Widget Pro | 10 | $50.00 | $500.00 |
| 2 | Gadget Plus | 5 | $120.00 | $600.00 |
| 3 | Service Fee | 1 | $250.00 | $250.00 |

**Subtotal:** $1,350.00
**Tax (10%):** $135.00
**Total Amount Due:** $1,485.00

## Payment Terms:
Net 30 days

## Notes:
Thank you for your business!
"""
    
    @agent
    def orchestrator(self) -> Any:
        return create_orchestrator_agent()
    
    @agent
    def schema_analyzer(self) -> Any:
        return create_schema_analyzer_agent()
    
    @agent
    def extraction_specialist(self) -> Any:
        return create_extraction_specialist_agent()
    
    @crew
    def crew(self) -> Crew:
        """Create the extraction crew with sequential processing"""
        return Crew(
            agents=[
                self.orchestrator(),
                self.schema_analyzer(),
                self.extraction_specialist()
            ],
            tasks=[],  # Tasks will be added dynamically
            process=Process.sequential,
            verbose=True,
            memory=False
        )
    
    def extract(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main extraction method - processes each task sequentially
        """
        try:
            print("🚀 Starting extraction crew...")
            
            results = []
            
            # Process each task sequentially
            for idx, task in enumerate(self.extraction_input.tasks, 1):
                print(f"\n📋 Processing Task {idx}/{len(self.extraction_input.tasks)}: {task.aim}")
                
                try:
                    # Step 1: Schema Analysis
                    schema_json = json.dumps([s.dict() for s in task.schema])
                    print(f"   🔍 Analyzing schema...")
                    
                    from tools import SchemaAnalyzerTool
                    analyzer = SchemaAnalyzerTool()
                    analysis_result = analyzer._run(task.aim, schema_json)
                    analysis_data = json.loads(analysis_result)
                    
                    if 'error' in analysis_data:
                        raise Exception(analysis_data['error'])
                    
                    print(f"   ✅ Prompt and model generated")
                    
                    # Step 2: Data Extraction
                    print(f"   🎯 Extracting data...")
                    
                    extraction_prompt = analysis_data['extraction_prompt']
                    full_prompt = f"""{extraction_prompt}

DOCUMENT CONTENT (Markdown):
{self.markdown_content}

Extract the data and return ONLY valid JSON matching the schema. No additional commentary."""
                    
                    # Use LLM to extract (through CrewAI agent)
                    from crewai import Task as CrewTask
                    extraction_task = CrewTask(
                        description=full_prompt,
                        agent=self.extraction_specialist(),
                        expected_output="Valid JSON data matching the schema"
                    )
                    
                    # Create temporary crew for this extraction
                    temp_crew = Crew(
                        agents=[self.extraction_specialist()],
                        tasks=[extraction_task],
                        process=Process.sequential,
                        verbose=False
                    )
                    
                    extraction_result = temp_crew.kickoff()
                    
                    # Parse the result
                    extracted_data = self._parse_extraction_result(str(extraction_result))
                    
                    print(f"   ✅ Data extracted successfully")
                    
                    results.append({
                        "task_number": idx,
                        "task_aim": task.aim,
                        "status": "success",
                        "data": extracted_data
                    })
                    
                except Exception as e:
                    print(f"   ❌ Task {idx} failed: {str(e)}")
                    results.append({
                        "task_number": idx,
                        "task_aim": task.aim,
                        "status": "error",
                        "error": str(e)
                    })
            
            print("\n✅ All tasks completed!")
            
            return {
                "status": "success",
                "markdown_length": len(self.markdown_content),
                "tasks_processed": len(self.extraction_input.tasks),
                "results": results
            }
            
        except Exception as e:
            print(f"❌ Extraction failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _parse_extraction_result(self, result: str) -> Any:
        """Parse the extraction result into structured format"""
        try:
            # Try to extract JSON from the result
            import re
            
            # Remove markdown code blocks if present
            result = re.sub(r'```json\s*', '', result)
            result = re.sub(r'```\s*', '', result)
            
            # Find JSON in the text
            json_match = re.search(r'\{.*\}|\[.*\]', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            # If no JSON found, try parsing the whole thing
            return json.loads(result)
        except Exception as e:
            print(f"⚠️ Could not parse as JSON: {e}")
            return {"raw_output": result}

                if response.status_code == 200:
                    result = response.json()
                    # Extract text from Nanonets response
                    markdown = self._extract_text_from_nanonets(result)
                    return markdown
                else:
                    print(f"⚠️ Nanonets API error: {response.status_code}")
                    return self._mock_markdown(file_name)
                    
            except Exception as e:
                print(f"⚠️ Nanonets API call failed: {str(e)}")
                return self._mock_markdown(file_name)
        else:
            print("⚠️ No Nanonets API key found, using mock markdown")
            return self._mock_markdown(file_name)
    
    def _extract_text_from_nanonets(self, result: Dict) -> str:
        """Extract and format text from Nanonets OCR result"""
        try:
            # Nanonets returns text in result['results'][0]['page_data'][0]['raw_text']
            pages = result.get('result', [{}])[0].get('page_data', [])
            text_parts = []
            
            for page in pages:
                raw_text = page.get('raw_text', '')
                if raw_text:
                    text_parts.append(raw_text)
            
            return "\n\n".join(text_parts)
        except Exception as e:
            print(f"Error extracting Nanonets text: {e}")
            return "Error processing OCR result"
    
    def _mock_markdown(self, file_name: str) -> str:
        """Generate mock markdown for testing"""
        return f"""# Invoice Document

**Invoice Number:** INV-2024-001
**Date:** October 26, 2025
**Due Date:** November 26, 2025

## Bill To:
Acme Corporation
123 Business St
New York, NY 10001

## Items:

| Item | Description | Quantity | Unit Price | Total |
|------|-------------|----------|------------|-------|
| 1 | Widget Pro | 10 | $50.00 | $500.00 |
| 2 | Gadget Plus | 5 | $120.00 | $600.00 |
| 3 | Service Fee | 1 | $250.00 | $250.00 |

**Subtotal:** $1,350.00
**Tax (10%):** $135.00
**Total Amount Due:** $1,485.00

## Payment Terms:
Net 30 days

## Notes:
Thank you for your business!
"""
    
    @agent
    def orchestrator(self) -> Any:
        return create_orchestrator_agent()
    
    @agent
    def schema_analyzer(self) -> Any:
        return create_schema_analyzer_agent()
    
    @agent
    def extraction_specialist(self) -> Any:
        return create_extraction_specialist_agent()
    
    @task
    def plan_execution(self) -> Any:
        return create_planning_task(self.orchestrator(), self.extraction_input)
    
    @crew
    def crew(self) -> Crew:
        """Create the extraction crew"""
        return Crew(
            agents=[
                self.orchestrator(),
                self.schema_analyzer(),
                self.extraction_specialist()
            ],
            tasks=[self.plan_execution()],
            process=Process.hierarchical,
            manager_agent=self.orchestrator(),
            verbose=True
        )
    
    def extract(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main extraction method
        """
        try:
            print("🚀 Starting extraction crew...")
            
            # Kickoff the crew
            result = self.crew().kickoff(inputs=inputs)
            
            print("✅ Extraction completed!")
            
            # Parse and structure the result
            return {
                "status": "success",
                "markdown_length": len(self.markdown_content),
                "tasks_processed": len(self.extraction_input.tasks),
                "results": self._parse_crew_result(result)
            }
            
        except Exception as e:
            print(f"❌ Extraction failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _parse_crew_result(self, result: Any) -> Any:
        """Parse the crew result into structured format"""
        try:
            # If result is a string, try to parse as JSON
            if isinstance(result, str):
                # Try to extract JSON from the result
                import re
                json_match = re.search(r'\{.*\}|\[.*\]', result, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                return {"raw_output": result}
            return result
        except:
            return {"raw_output": str(result)}
