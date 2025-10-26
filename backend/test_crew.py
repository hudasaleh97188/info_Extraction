#!/usr/bin/env python3
"""
Simple test script to verify the extraction crew works correctly.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.crew import ExtractionCrew, get_mock_inputs

def test_extraction_crew():
    """Test the extraction crew with mock data."""
    print("🧪 Testing Extraction Crew...")
    
    try:
        # Get mock inputs
        inputs = get_mock_inputs()
        print(f"📋 Mock inputs prepared: {len(inputs['tasks'])} tasks")
        
        # Create and run the crew
        extraction_crew = ExtractionCrew()
        result = extraction_crew.run(inputs)
        
        print("\n" + "="*50)
        print("🎯 EXTRACTION CREW TEST RESULTS")
        print("="*50)
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Tasks Processed: {result.get('tasks_processed', 0)}")
        print(f"Markdown Length: {result.get('markdown_length', 0)}")
        
        if result.get('status') == 'success':
            print("✅ Crew execution completed successfully!")
            if 'results' in result:
                print(f"📊 Results: {len(result['results'])} extraction results")
                for i, task_result in enumerate(result['results']):
                    print(f"  Task {i+1}: {task_result.get('task_aim', 'Unknown')}")
        else:
            print(f"❌ Crew execution failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"💥 Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return result.get('status') == 'success'

if __name__ == "__main__":
    success = test_extraction_crew()
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Tests failed!")
        sys.exit(1)
