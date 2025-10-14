#!/usr/bin/env python3
"""
Example: Extract Hierarchical Structure

This example demonstrates how to extract the exact hierarchical structure
the user requested: {'INV': 'PIN': ['PIN1', 'PIN2'], 'TIMING': [...]}
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from old_lef_parser import LEFParser

def extract_macro_hierarchy(lef_file_path):
    """
    Extract hierarchical structure for all MACROs in the format:
    {
        'MACRO_NAME': {
            'PIN': ['pin1', 'pin2', ...],
            'TIMING': [...],
            'OBS': [...],
            etc.
        }
    }
    """
    parser = LEFParser()
    result = parser.parse_file(lef_file_path)
    
    macro_hierarchy = {}
    
    # Extract all MACRO blocks
    for block_name, block_list in result['blocks'].items():
        if block_name.startswith('MACRO_'):
            for macro_block in block_list:
                macro_name = macro_block['name']
                macro_hierarchy[macro_name] = {}
                
                # Extract sub-blocks
                if 'sub_blocks' in macro_block:
                    for sub_type, sub_blocks in macro_block['sub_blocks'].items():
                        if sub_type == 'PIN':
                            # Extract PIN names
                            pin_names = [pin['name'] for pin in sub_blocks]
                            macro_hierarchy[macro_name]['PIN'] = pin_names
                        elif sub_type == 'TIMING':
                            # Extract timing information
                            timing_info = []
                            for timing in sub_blocks:
                                timing_data = {
                                    'frompin': timing['attributes'].get('frompin'),
                                    'topin': timing['attributes'].get('topin'),
                                    'unateness': timing['attributes'].get('unateness'),
                                    'timing_arcs': timing['attributes'].get('timing_arcs', [])
                                }
                                timing_info.append(timing_data)
                            macro_hierarchy[macro_name]['TIMING'] = timing_info
                        else:
                            # For other sub-blocks, just count them
                            macro_hierarchy[macro_name][sub_type] = len(sub_blocks)
                
                # Add macro attributes
                macro_hierarchy[macro_name]['attributes'] = {
                    'class': macro_block['attributes'].get('class'),
                    'size': macro_block['attributes'].get('size'),
                    'symmetry': macro_block['attributes'].get('symmetry'),
                    'source': macro_block['attributes'].get('source'),
                    'power': macro_block['attributes'].get('power')
                }
    
    return macro_hierarchy

def extract_pin_details(lef_file_path, macro_name):
    """
    Extract detailed PIN information for a specific macro
    Returns: {
        'PIN_NAME': {
            'direction': 'INPUT/OUTPUT/INOUT',
            'use': 'SIGNAL/POWER/GROUND',
            'attributes': {...},
            'ports': [...]
        }
    }
    """
    parser = LEFParser()
    result = parser.parse_file(lef_file_path)
    
    # Find the specific macro
    macro_key = f"MACRO_{macro_name}"
    if macro_key not in result['blocks']:
        return None
    
    macro_block = result['blocks'][macro_key][0]
    pin_details = {}
    
    if 'sub_blocks' in macro_block and 'PIN' in macro_block['sub_blocks']:
        for pin in macro_block['sub_blocks']['PIN']:
            pin_name = pin['name']
            pin_details[pin_name] = {
                'direction': pin['attributes'].get('direction'),
                'use': pin['attributes'].get('use'),
                'capacitance': pin['attributes'].get('capacitance'),
                'power': pin['attributes'].get('power'),
                'attributes': pin['attributes'],
                'ports': []
            }
            
            # Extract PORT information
            if 'sub_blocks' in pin and 'PORT' in pin['sub_blocks']:
                for port in pin['sub_blocks']['PORT']:
                    port_info = {
                        'rectangles': port['attributes'].get('rectangles', []),
                        'paths': port['attributes'].get('paths', []),
                        'content': port['content_lines']
                    }
                    pin_details[pin_name]['ports'].append(port_info)
    
    return pin_details

def main():
    lef_file = "../test_data/complete.5.8.lef"
    
    print("=" * 60)
    print("HIERARCHICAL STRUCTURE EXTRACTION EXAMPLE")
    print("=" * 60)
    
    # Extract overall macro hierarchy
    print("\n1. EXTRACTING MACRO HIERARCHY...")
    macro_hierarchy = extract_macro_hierarchy(lef_file)
    
    # Show the exact format requested by user
    print("\nHierarchical Structure (requested format):")
    print("-" * 40)
    
    for macro_name, macro_data in macro_hierarchy.items():
        print(f"\n'{macro_name}': {{")
        for key, value in macro_data.items():
            if key == 'PIN':
                print(f"    'PIN': {value},")
            elif key == 'TIMING':
                print(f"    'TIMING': {len(value)} timing arcs,")
            elif key == 'attributes':
                continue  # Skip attributes for clean display
            else:
                print(f"    '{key}': {value},")
        print("}")
    
    # Show detailed example for INV macro
    print("\n\n2. DETAILED PIN ANALYSIS FOR 'INV' MACRO...")
    inv_pins = extract_pin_details(lef_file, "INV")
    
    if inv_pins:
        print(f"\n'INV' PIN Details:")
        print("-" * 30)
        for pin_name, pin_data in inv_pins.items():
            print(f"\nPIN '{pin_name}':")
            print(f"  Direction: {pin_data['direction']}")
            print(f"  Use: {pin_data['use']}")
            print(f"  Capacitance: {pin_data['capacitance']}")
            print(f"  Ports: {len(pin_data['ports'])}")
            
            # Show port details
            for i, port in enumerate(pin_data['ports']):
                print(f"    Port {i+1}:")
                if port['paths']:
                    print(f"      Paths: {port['paths']}")
                if port['rectangles']:
                    print(f"      Rectangles: {port['rectangles']}")
    
    # Show exact dictionary structure for programming use
    print("\n\n3. EXACT DICTIONARY STRUCTURE FOR PROGRAMMING:")
    print("-" * 50)
    
    # Create the exact format user requested
    programming_structure = {}
    for macro_name, macro_data in macro_hierarchy.items():
        programming_structure[macro_name] = {}
        
        if 'PIN' in macro_data:
            programming_structure[macro_name]['PIN'] = macro_data['PIN']
        
        if 'TIMING' in macro_data:
            programming_structure[macro_name]['TIMING'] = macro_data['TIMING']
        
        # Add other sub-blocks
        for key, value in macro_data.items():
            if key not in ['PIN', 'TIMING', 'attributes']:
                programming_structure[macro_name][key] = value
    
    # Show just the INV macro as example
    if 'INV' in programming_structure:
        print("\nExample - INV macro structure:")
        import json
        print(json.dumps({'INV': programming_structure['INV']}, indent=2))
    
    print("\n\n4. HOW TO USE THIS IN YOUR CODE:")
    print("-" * 40)
    print("""
# Import the parser
from lef_parser import LEFParser

# Parse the LEF file
parser = LEFParser()
result = parser.parse_file('your_file.lef')

# Extract hierarchy for a specific macro
def get_macro_structure(result, macro_name):
    macro_key = f"MACRO_{macro_name}"
    if macro_key in result['blocks']:
        macro = result['blocks'][macro_key][0]
        structure = {}
        
        if 'sub_blocks' in macro:
            for sub_type, sub_blocks in macro['sub_blocks'].items():
                if sub_type == 'PIN':
                    structure['PIN'] = [pin['name'] for pin in sub_blocks]
                elif sub_type == 'TIMING':
                    structure['TIMING'] = sub_blocks  # Full timing data
                else:
                    structure[sub_type] = sub_blocks
        
        return structure
    return None

# Usage:
inv_structure = get_macro_structure(result, 'INV')
# Result: {'PIN': ['Z', 'A', 'VDD', 'VSS'], 'TIMING': [...], 'OBS': [...]}
""")

if __name__ == "__main__":
    main() 