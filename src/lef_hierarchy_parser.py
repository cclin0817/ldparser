#!/usr/bin/env python3
"""
LEF Hierarchy Parser - Simplified Interface

This module provides a simple interface to extract the hierarchical structure
from LEF files in the exact format requested by the user.
"""

from typing import Dict, List, Any, Optional
import os

# Handle both relative and absolute imports
try:
    from .lef_parser import LEFParser
except ImportError:
    # If relative import fails, try absolute import
    from lef_parser import LEFParser

class LEFHierarchyParser:
    """
    Simplified parser for extracting hierarchical structure from LEF files.
    
    Provides clean methods to get structures like:
    {
        'INV': {
            'PIN': ['Z', 'A', 'VDD', 'VSS'],
            'TIMING': [...],
            'OBS': [...],
            etc.
        }
    }
    """
    
    def __init__(self, lef_file_path: str):
        """Initialize parser with LEF file path"""
        self.lef_file_path = lef_file_path
        self.parser = LEFParser()
        self._parsed_result = None
        
    def parse(self) -> Dict[str, Any]:
        """Parse the LEF file and cache the result"""
        if self._parsed_result is None:
            self._parsed_result = self.parser.parse_file(self.lef_file_path)
        return self._parsed_result
    
    def get_all_macros_hierarchy(self) -> Dict[str, Dict[str, Any]]:
        """
        Get hierarchical structure for all macros.
        
        Returns:
            Dict with macro names as keys and their hierarchical structure as values
            
        Example:
            {
                'INV': {
                    'PIN': ['Z', 'A', 'VDD', 'VSS'],
                    'TIMING': [timing_data],
                    'OBS': 1,
                    'DENSITY': 1
                },
                'DFF3': {
                    'PIN': ['Q', 'QN', 'D', 'G', 'CD', 'VDD', 'VSS'],
                    'TIMING': [timing_data],
                    'OBS': 1
                }
            }
        """
        result = self.parse()
        hierarchy = {}
        
        # Find all MACRO blocks
        for block_name, block_list in result['blocks'].items():
            if block_name.startswith('MACRO_'):
                for macro_block in block_list:
                    macro_name = macro_block['name']
                    hierarchy[macro_name] = self._extract_macro_structure(macro_block)
        
        return hierarchy
    
    def get_macro_hierarchy(self, macro_name: str) -> Optional[Dict[str, Any]]:
        """
        Get hierarchical structure for a specific macro.
        
        Args:
            macro_name: Name of the macro (e.g., 'INV', 'DFF3')
            
        Returns:
            Dictionary with hierarchical structure or None if macro not found
            
        Example:
            {
                'PIN': ['Z', 'A', 'VDD', 'VSS'],
                'TIMING': [timing_data],
                'OBS': 1,
                'DENSITY': 1
            }
        """
        result = self.parse()
        macro_key = f"MACRO_{macro_name}"
        
        if macro_key in result['blocks']:
            macro_block = result['blocks'][macro_key][0]
            return self._extract_macro_structure(macro_block)
        
        return None
    
    def get_macro_pins(self, macro_name: str) -> Optional[List[str]]:
        """
        Get list of PIN names for a specific macro.
        
        Args:
            macro_name: Name of the macro
            
        Returns:
            List of pin names or None if macro not found
            
        Example:
            ['Z', 'A', 'VDD', 'VSS']
        """
        hierarchy = self.get_macro_hierarchy(macro_name)
        return hierarchy.get('PIN') if hierarchy else None
    
    def get_macro_pin_details(self, macro_name: str) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Get detailed PIN information for a specific macro.
        
        Args:
            macro_name: Name of the macro
            
        Returns:
            Dictionary with pin names as keys and their details as values
            
        Example:
            {
                'Z': {
                    'direction': 'OUTPUT',
                    'use': 'SIGNAL',
                    'capacitance': 0.1,
                    'ports': [...]
                },
                'A': {
                    'direction': 'INPUT',
                    'use': 'ANALOG',
                    'capacitance': 0.08,
                    'ports': [...]
                }
            }
        """
        result = self.parse()
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
                    'ports': []
                }
                
                # Extract PORT information
                if 'sub_blocks' in pin and 'PORT' in pin['sub_blocks']:
                    for port in pin['sub_blocks']['PORT']:
                        port_info = {
                            'layer_info': self._extract_layer_info(port['content_lines']),
                            'rectangles': port['attributes'].get('rectangles', []),
                            'paths': port['attributes'].get('paths', [])
                        }
                        pin_details[pin_name]['ports'].append(port_info)
        
        return pin_details
    
    def get_macro_timing(self, macro_name: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get timing information for a specific macro.
        
        Args:
            macro_name: Name of the macro
            
        Returns:
            List of timing arc information
        """
        result = self.parse()
        macro_key = f"MACRO_{macro_name}"
        
        if macro_key not in result['blocks']:
            return None
        
        macro_block = result['blocks'][macro_key][0]
        
        if 'sub_blocks' in macro_block and 'TIMING' in macro_block['sub_blocks']:
            timing_info = []
            for timing in macro_block['sub_blocks']['TIMING']:
                timing_data = {
                    'frompin': timing['attributes'].get('frompin'),
                    'topin': timing['attributes'].get('topin'),
                    'unateness': timing['attributes'].get('unateness'),
                    'timing_arcs': timing['attributes'].get('timing_arcs', []),
                    'content': timing['content_lines']
                }
                timing_info.append(timing_data)
            return timing_info
        
        return None
    
    def get_available_macros(self) -> List[str]:
        """
        Get list of all available macro names.
        
        Returns:
            List of macro names
        """
        result = self.parse()
        macros = []
        
        for block_name in result['blocks'].keys():
            if block_name.startswith('MACRO_'):
                macro_name = block_name.replace('MACRO_', '')
                macros.append(macro_name)
        
        return macros
    
    def _extract_macro_structure(self, macro_block: Dict[str, Any]) -> Dict[str, Any]:
        """Extract hierarchical structure from a macro block"""
        structure = {}
        
        if 'sub_blocks' in macro_block:
            for sub_type, sub_blocks in macro_block['sub_blocks'].items():
                if sub_type == 'PIN':
                    # Extract PIN names
                    structure['PIN'] = [pin['name'] for pin in sub_blocks]
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
                    structure['TIMING'] = timing_info
                else:
                    # For other sub-blocks, store count or full data
                    structure[sub_type] = len(sub_blocks)
        
        return structure
    
    def _extract_layer_info(self, content_lines: List[str]) -> List[str]:
        """Extract layer information from content lines"""
        layers = []
        for line in content_lines:
            if line.strip().startswith('LAYER '):
                layer_name = line.strip().split()[1].rstrip(' ;')
                layers.append(layer_name)
        return layers

# Convenience function
def extract_lef_hierarchy(lef_file_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Convenience function to extract hierarchical structure from LEF file.
    
    Args:
        lef_file_path: Path to LEF file
        
    Returns:
        Dictionary with hierarchical structure for all macros
    """
    parser = LEFHierarchyParser(lef_file_path)
    return parser.get_all_macros_hierarchy()

# Example usage
if __name__ == "__main__":
    # Determine the correct path to the test data file
    # This works whether running from src/ or from root directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(current_dir) == 'src':
        # Running from src directory
        lef_file = "../test_data/complete.5.8.lef"
    else:
        # Running from root directory
        lef_file = "test_data/complete.5.8.lef"
    
    # Check if file exists, if not try alternative paths
    if not os.path.exists(lef_file):
        alternative_paths = [
            "test_data/complete.5.8.lef",
            "../test_data/complete.5.8.lef",
            "../../test_data/complete.5.8.lef"
        ]
        for alt_path in alternative_paths:
            if os.path.exists(alt_path):
                lef_file = alt_path
                break
        else:
            print("Error: Could not find complete.5.8.lef file")
            print("Please ensure the test data file exists in test_data/complete.5.8.lef")
            exit(1)
    
    # Example usage
    parser = LEFHierarchyParser(lef_file)
    
    # Get all macros
    print("Available macros:", parser.get_available_macros())
    
    # Get hierarchy for specific macro
    inv_structure = parser.get_macro_hierarchy("INV")
    print("\nINV structure:", inv_structure)
    
    # Get just the pins
    inv_pins = parser.get_macro_pins("INV")
    print("\nINV pins:", inv_pins)
    
    # Get detailed pin information
    inv_pin_details = parser.get_macro_pin_details("INV")
    print("\nINV pin details:", inv_pin_details)
    
    # Get timing information
    inv_timing = parser.get_macro_timing("INV")
    print("\nINV timing:", inv_timing) 