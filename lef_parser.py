#!/usr/bin/env python3
"""
Test script for LEF Parser

This script demonstrates how to use the LEF parser to parse the complete.5.8.lef file
and extract hierarchical information.
"""

import sys
import os
import json
import pickle
from pprint import pprint
import argparse
parser = argparse.ArgumentParser(description='Parse LEF file and extract cell information')
parser.add_argument('--lef_path', type=str, default='test_data/complete.5.8.lef', help='Path to the LEF file')
parser.add_argument('--output_dir', type=str, default='cell_dict.json', help='Path to the output JSON file')
args = parser.parse_args()

lef_path = args.lef_path
output_dir = args.output_dir

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.lef_parser import LEFParser, parse_lef_file

def let2format(result):
    cell_dict = {}
    for block_name, block_list in result['blocks'].items():
        block = block_list[0]

        if block_name.startswith('MACRO_'):
            cell_name = block_name.split('_')[1]
            cell_dict[cell_name] = {'pins': {}}
            if 'sub_blocks' not in block:
                continue
            if 'PIN' not in block['sub_blocks']:
                continue

            for pin_info in block['sub_blocks']['PIN']:
                pin_name = pin_info['name']
                if 'direction' in pin_info['attributes']:
                    direction = pin_info['attributes']['direction']

                    if direction == 'INPUT':
                        cell_dict[cell_name]['pins'][pin_name] = { 'direction': -1}
                    elif direction == 'OUTPUT':
                        cell_dict[cell_name]['pins'][pin_name] = { 'direction': 1}
                    else:
                        cell_dict[cell_name]['pins'][pin_name] = {}
                else:
                    continue
            
    return cell_dict

            

def get_cell_dict(lef_path):
    """Test the LEF parser with the complete.5.8.lef file"""
    
    lef_file = lef_path
    
    if not os.path.exists(lef_file):
        print(f"Error: LEF file {lef_file} not found!")
        return
    
    print("Parsing LEF file...")
    parser = LEFParser()
    result = parser.parse_file(lef_file)
    cell_dict = let2format(result)
    return cell_dict

    # breakpoint()
    # print("\n" + "="*60)
    # print("LEF FILE STRUCTURE ANALYSIS")
    # print("="*60)
    
    # # Print header information
    # print("\nHEADER INFORMATION:")
    # print("-" * 30)
    # for key, value in result['header'].items():
    #     print(f"  {key}: {value}")
    
    # # Print block summary
    # print(f"\nBLOCKS SUMMARY:")
    # print("-" * 30)
    # block_types = {}
    # for block_name, block_list in result['blocks'].items():
    #     block_type = block_list[0]['type']
    #     if block_type not in block_types:
    #         block_types[block_type] = 0
    #     block_types[block_type] += len(block_list)
    #     print(f"  {block_name}: {len(block_list)} instances")
    
    # print(f"\nBLOCK TYPE SUMMARY:")
    # print("-" * 30)
    # for block_type, count in sorted(block_types.items()):
    #     print(f"  {block_type}: {count} instances")
    
    # # Detailed analysis of MACRO blocks
    # print(f"\nMACRO ANALYSIS:")
    # print("-" * 30)
    # macro_blocks = [block for name, blocks in result['blocks'].items() 
    #                if name.startswith('MACRO_') for block in blocks]
    
    # for macro in macro_blocks:
    #     print(f"\nMACRO: {macro['name']}")
    #     print(f"  Class: {macro['attributes'].get('class', 'N/A')}")
    #     print(f"  Size: {macro['attributes'].get('size', 'N/A')}")
    #     print(f"  Symmetry: {macro['attributes'].get('symmetry', 'N/A')}")
        
    #     if 'sub_blocks' in macro:
    #         for sub_type, sub_blocks in macro['sub_blocks'].items():
    #             print(f"  {sub_type}: {len(sub_blocks)} items")
                
    #             if sub_type == 'PIN':
    #                 for pin in sub_blocks:
    #                     pin_name = pin['name']
    #                     direction = pin['attributes'].get('direction', 'N/A')
    #                     use = pin['attributes'].get('use', 'N/A')
    #                     print(f"    - {pin_name}: {direction}, USE: {use}")
                        
    #                     # Show PORT information if available
    #                     if 'sub_blocks' in pin and 'PORT' in pin['sub_blocks']:
    #                         port_count = len(pin['sub_blocks']['PORT'])
    #                         print(f"      Ports: {port_count}")
                
    #             elif sub_type == 'TIMING':
    #                 for timing in sub_blocks:
    #                     print(f"    - Timing arc")
    #                     # You can add more detailed timing analysis here
    
    # # Layer analysis
    # print(f"\nLAYER ANALYSIS:")
    # print("-" * 30)
    # layer_blocks = [block for name, blocks in result['blocks'].items() 
    #                if name.startswith('LAYER_') for block in blocks]
    
    # routing_layers = []
    # cut_layers = []
    # other_layers = []
    
    # for layer in layer_blocks:
    #     layer_type = layer['attributes'].get('type', 'UNKNOWN')
    #     layer_name = layer['name']
        
    #     if layer_type == 'ROUTING':
    #         routing_layers.append(layer_name)
    #     elif layer_type == 'CUT':
    #         cut_layers.append(layer_name)
    #     else:
    #         other_layers.append(layer_name)
    
    # print(f"  Routing Layers ({len(routing_layers)}): {', '.join(routing_layers)}")
    # print(f"  Cut Layers ({len(cut_layers)}): {', '.join(cut_layers)}")
    # print(f"  Other Layers ({len(other_layers)}): {', '.join(other_layers)}")
    
    # # VIA analysis
    # print(f"\nVIA ANALYSIS:")
    # print("-" * 30)
    # via_blocks = [block for name, blocks in result['blocks'].items() 
    #              if name.startswith('VIA_') for block in blocks]
    
    # for via in via_blocks[:5]:  # Show first 5 vias
    #     via_name = via['name']
    #     resistance = via['attributes'].get('resistance', 'N/A')
    #     print(f"  {via_name}: Resistance = {resistance}")
    
    # if len(via_blocks) > 5:
    #     print(f"  ... and {len(via_blocks) - 5} more vias")
    
    # return result

def extract_macro_hierarchy(result):
    """Extract and display the hierarchical structure of a specific MACRO"""
    
    # Find the INV macro for detailed analysis
    inv_macro = None
    for block_name, block_list in result['blocks'].items():
        if block_name == 'MACRO_INV':
            inv_macro = block_list[0]
            break
    
    if not inv_macro:
        print("INV macro not found!")
        return
    
    print(f"\nDETAILED HIERARCHY for MACRO INV:")
    print("="*50)
    
    def print_hierarchy(obj, indent=0):
        """Recursively print hierarchical structure"""
        spaces = "  " * indent
        
        if isinstance(obj, dict):
            if 'name' in obj and 'type' in obj:
                # This is a block
                print(f"{spaces}{obj['type']}: {obj['name']}")
                
                # Print key attributes
                if obj['attributes']:
                    for key, value in obj['attributes'].items():
                        if key in ['class', 'direction', 'use', 'size', 'symmetry']:
                            print(f"{spaces}  {key}: {value}")
                
                # Print sub-blocks
                if 'sub_blocks' in obj:
                    for sub_type, sub_list in obj['sub_blocks'].items():
                        print(f"{spaces}  {sub_type}:")
                        for sub_block in sub_list:
                            print_hierarchy(sub_block, indent + 2)
            else:
                # Generic dict
                for key, value in obj.items():
                    if key not in ['content_lines', 'attributes']:  # Skip verbose content
                        print(f"{spaces}{key}:")
                        print_hierarchy(value, indent + 1)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                print(f"{spaces}[{i}]:")
                print_hierarchy(item, indent + 1)
        else:
            print(f"{spaces}{obj}")
    
    print_hierarchy(inv_macro)

def save_parsed_structure(result, output_file="parsed_lef_structure.json"):
    """Save the parsed structure to a JSON file for further analysis"""
    
    # Create a simplified version for JSON serialization
    simplified_result = {
        'header': result['header'],
        'block_summary': {}
    }
    
    for block_name, block_list in result['blocks'].items():
        simplified_result['block_summary'][block_name] = {
            'count': len(block_list),
            'type': block_list[0]['type'],
            'names': [block['name'] for block in block_list]
        }
    
    with open(output_file, 'w') as f:
        json.dump(simplified_result, f, indent=2)
    
    print(f"\nSimplified structure saved to {output_file}")

if __name__ == "__main__":
    # Test the parser
    cell_dict = get_cell_dict(lef_path)
    lef_output = {'cell_dict': cell_dict}
    
    try:
        with open(output_dir + '/lef_outputs.pkl', 'wb') as f:
            pickle.dump(lef_output, f)
    except Exception as e:
        fb = open(output_dir + '/lef_outputs.pkl', 'wb')
        pickle.dump(lef_output, fb)
        fb.close()
    # if result:
    #     # Show detailed hierarchy for INV macro
    #     extract_macro_hierarchy(result)
        
    #     # Save structure summary
    #     save_parsed_structure(result)
        
    #     print("\n" + "="*60)
    #     print("PARSING COMPLETE")
    #     print("="*60)
    #     print("The LEF file has been successfully parsed into a hierarchical structure.")
    #     print("You can now access:")
    #     print("- result['header'] for header information")
    #     print("- result['blocks'] for all parsed blocks")
    #     print("- Each block contains 'attributes' and 'sub_blocks'")
    #     print("- Use the parser to extract specific information as needed") 