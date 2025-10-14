#!/usr/bin/env python3
"""
Simple Usage Example

This shows exactly how to use the LEF hierarchy parser to get the structure
you requested: {'INV': 'PIN': ['PIN1', 'PIN2'], 'TIMING': [...]}
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Fix import for relative imports
import sys
sys.path.append('../src')
from old_lef_parser import LEFParser

def get_macro_hierarchy(lef_file, macro_name):
    """
    Extract hierarchical structure for a specific macro.
    
    Returns the exact format you requested:
    {
        'PIN': ['pin1', 'pin2', ...],
        'TIMING': [...],
        'OBS': [...],
        etc.
    }
    """
    parser = LEFParser()
    result = parser.parse_file(lef_file)
    
    # Find the macro
    macro_key = f"MACRO_{macro_name}"
    if macro_key not in result['blocks']:
        return None
    
    macro_block = result['blocks'][macro_key][0]
    structure = {}
    
    if 'sub_blocks' in macro_block:
        for sub_type, sub_blocks in macro_block['sub_blocks'].items():
            if sub_type == 'PIN':
                # Get PIN names
                structure['PIN'] = [pin['name'] for pin in sub_blocks]
            elif sub_type == 'TIMING':
                # Get TIMING data
                structure['TIMING'] = []
                for timing in sub_blocks:
                    timing_data = {
                        'frompin': timing['attributes'].get('frompin'),
                        'topin': timing['attributes'].get('topin'),
                        'unateness': timing['attributes'].get('unateness')
                    }
                    structure['TIMING'].append(timing_data)
            else:
                # For other sub-blocks
                structure[sub_type] = len(sub_blocks)
    
    return structure

def main():
    lef_file = "../test_data/complete.5.8.lef"
    
    print("="*60)
    print("SIMPLE HIERARCHICAL PARSING EXAMPLE")
    print("="*60)
    
    # Get the exact structure you requested for INV macro
    inv_structure = get_macro_hierarchy(lef_file, "INV")
    
    print("\nResult for INV macro:")
    print("{'INV': ", end="")
    print(inv_structure, end="")
    print("}")
    
    # Show it's exactly what you asked for
    print(f"\nINV PIN list: {inv_structure['PIN']}")
    print(f"INV TIMING count: {len(inv_structure['TIMING'])}")
    print(f"INV OBS count: {inv_structure['OBS']}")
    print(f"INV DENSITY count: {inv_structure['DENSITY']}")
    
    print("\n" + "-"*50)
    print("OTHER EXAMPLES:")
    print("-"*50)
    
    # Show a few more examples
    examples = ['DFF3', 'BUF1', 'FWHSQCN690V15']
    
    for macro_name in examples:
        structure = get_macro_hierarchy(lef_file, macro_name)
        if structure:
            print(f"\n{macro_name}:")
            for key, value in structure.items():
                if key == 'PIN':
                    print(f"  PIN: {value}")
                else:
                    print(f"  {key}: {value}")
    
    print("\n" + "="*60)
    print("HOW TO USE IN YOUR CODE:")
    print("="*60)
    print("""
# 1. Simple usage
structure = get_macro_hierarchy('my_file.lef', 'INV')
pin_list = structure['PIN']  # ['Z', 'A', 'VDD', 'VSS']
timing_data = structure['TIMING']  # [{...}]

# 2. Get all macros
parser = LEFParser()
result = parser.parse_file('my_file.lef')

all_macros = {}
for block_name, block_list in result['blocks'].items():
    if block_name.startswith('MACRO_'):
        macro_name = block_name.replace('MACRO_', '')
        all_macros[macro_name] = get_macro_hierarchy_from_block(block_list[0])

# 3. Access the hierarchical structure
for macro_name, structure in all_macros.items():
    print(f"Macro {macro_name}:")
    print(f"  Pins: {structure.get('PIN', [])}")
    print(f"  Has timing: {'TIMING' in structure}")
    print(f"  Has blockages: {'OBS' in structure}")
""")

def get_macro_hierarchy_from_block(macro_block):
    """Helper function to extract structure from already parsed block"""
    structure = {}
    
    if 'sub_blocks' in macro_block:
        for sub_type, sub_blocks in macro_block['sub_blocks'].items():
            if sub_type == 'PIN':
                structure['PIN'] = [pin['name'] for pin in sub_blocks]
            elif sub_type == 'TIMING':
                structure['TIMING'] = []
                for timing in sub_blocks:
                    timing_data = {
                        'frompin': timing['attributes'].get('frompin'),
                        'topin': timing['attributes'].get('topin'),
                        'unateness': timing['attributes'].get('unateness')
                    }
                    structure['TIMING'].append(timing_data)
            else:
                structure[sub_type] = len(sub_blocks)
    
    return structure

if __name__ == "__main__":
    main() 