#!/usr/bin/env python3
"""
Quick test script to verify the extraction system works
Run this from the backend directory after setup
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from crew import ExtractionCrew
import json

def test_extraction():
    """Test the extraction crew with mock data"""
    
    print("🧪 Testing Document Extraction System\n")
    
    # Create test data
    test_inputs = {
        'file_data': '',  # Empty - will use mock
        'file_name': 'test_invoice.pdf',
        'file_type': 'application/pdf',
        'tasks': [
            {
                'aim': 'Extract invoice header information',
                'schema': [
                    {
                        'name': 'invoice_number',
                        'type': 'string',
                        'description': 'The invoice number',
                        'mandatory': True,
                        'multi_row': False
                    },
                    {
                        'name': 'invoice_date',
                        'type': 'date',
                        'description': 'Invoice date',
                        'mandatory': True,
                        'multi_row': False
                    },
                    {
                        'name': 'total_amount',
                        'type': 'number',
                        'description': 'Total amount due',
                        'mandatory': True,
                        'multi_row': False
                    }
                ]
            },
            {
                'aim': 'Extract all invoice line items',
                'schema': [
                    {
                        'name': 'item_description',
                        'type': 'string',
                        'description': 'Description of the item',
                        'mandatory': True,
                        'multi_row': True
                    },
                    {
                        'name': 'quantity',
                        'type': 'number',
                        'description': 'Quantity ordered',
                        'mandatory': True,
                        'multi_row': True
                    },
                    {
                        'name': 'unit_price',
                        'type': 'number',
                        'description': 'Price per unit',
                        'mandatory': True,
                        'multi_row': True
                    },
                    {
                        'name': 'total',
                        'type': 'number',
                        'description': 'Line total',
                        'mandatory': True,
                        'multi_row': True
                    }
                ]
            }
        ]
    }
    
    print("📋 Test Configuration:")
    print(f"   - Tasks: {len(test_inputs['tasks'])}")
    print(f"   - Task 1: {test_inputs['tasks'][0]['aim']}")
    print(f"   - Task 2: {test_inputs['tasks'][1]['aim']}")
    print()
    
    try:
        # Initialize crew
        print("🚀 Initializing extraction crew...")
        crew = ExtractionCrew()
        
        # Run extraction
        print("⚙️  Running extraction...\n")
        result = crew.extract(test_inputs)
        
        # Display results
        print("\n" + "="*60)
        print("📊 EXTRACTION RESULTS")
        print("="*60)
        print(json.dumps(result, indent=2))
        print("="*60)
        
        if result['status'] == 'success':
            print("\n✅ TEST PASSED! System is working correctly!")
            return 0
        else:
            print("\n❌ TEST FAILED! Check errors above.")
            return 1
            
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # Check environment
    print("🔍 Checking environment...")
    
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("❌ OPENAI_API_KEY not found!")
        print("   Please set it in .env file or:")
        print("   export OPENAI_API_KEY=your-key-here")
        sys.exit(1)
    
    print(f"✅ OpenAI API Key: {'*' * 20}{openai_key[-4:]}")
    print()
    
    # Run test
    exit_code = test_extraction()
    sys.exit(exit_code)
