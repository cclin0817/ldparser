#!/usr/bin/env python3
"""
LEF (Library Exchange Format) Hierarchical Parser

This module provides a comprehensive parser for LEF files that can handle
the hierarchical structure of LEF blocks like MACRO, PIN, TIMING, etc.
"""

import re
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

class BlockType(Enum):
    """Enumeration of LEF block types"""
    # Blocks with END <name> pattern
    UNITS = "UNITS"
    PROPERTYDEFINITIONS = "PROPERTYDEFINITIONS" 
    SPACING = "SPACING"
    IRDROP = "IRDROP"
    NOISETABLE = "NOISETABLE"
    
    # Blocks with <type> <name> ... END <name> pattern
    LAYER = "LAYER"
    VIA = "VIA" 
    VIARULE = "VIARULE"
    NONDEFAULTRULE = "NONDEFAULTRULE"
    SITE = "SITE"
    ARRAY = "ARRAY"
    MACRO = "MACRO"
    
    # Sub-blocks within MACRO
    PIN = "PIN"
    TIMING = "TIMING"
    OBS = "OBS"
    DENSITY = "DENSITY"
    PORT = "PORT"
    
    # Floorplan sub-blocks
    FLOORPLAN = "FLOORPLAN"

@dataclass
class LEFBlock:
    """Represents a hierarchical LEF block"""
    block_type: BlockType
    name: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    sub_blocks: Dict[str, List['LEFBlock']] = field(default_factory=dict)
    content_lines: List[str] = field(default_factory=list)

class LEFParser:
    """Hierarchical parser for LEF files"""
    
    def __init__(self):
        self.reset()
        
    def reset(self):
        """Reset parser state"""
        self.blocks = {}
        self.current_line_number = 0
        self.lines = []
        
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a LEF file and return hierarchical structure"""
        with open(file_path, 'r') as f:
            content = f.read()
        return self.parse_content(content)
        
    def parse_content(self, content: str) -> Dict[str, Any]:
        """Parse LEF content string"""
        self.reset()
        
        # Clean and split content into lines
        self.lines = [line.strip() for line in content.split('\n')]
        self.lines = [line for line in self.lines if line and not line.startswith('#')]
        
        result = {
            'header': self._parse_header(),
            'blocks': {}
        }
        
        # Parse main blocks
        i = 0
        while i < len(self.lines):
            i = self._skip_empty_lines(i)
            if i >= len(self.lines):
                break
                
            block, next_i = self._parse_block(i)
            if block:
                block_key = f"{block.block_type.value}"
                if block.name:
                    block_key += f"_{block.name}"
                    
                if block_key not in result['blocks']:
                    result['blocks'][block_key] = []
                result['blocks'][block_key].append(self._block_to_dict(block))
                
            i = next_i if next_i > i else i + 1
            
        return result
    
    def _parse_header(self) -> Dict[str, Any]:
        """Parse header information (before first major block)"""
        header = {}
        i = 0
        
        while i < len(self.lines):
            line = self.lines[i].strip()
            if not line:
                i += 1
                continue
                
            # Check if we've reached a major block
            if self._is_block_start(line):
                break
                
            # Parse header statements
            if line.startswith('VERSION'):
                header['version'] = self._extract_value(line)
            elif line.startswith('NAMESCASESENSITIVE'):
                header['names_case_sensitive'] = self._extract_value(line)
            elif line.startswith('BUSBITCHARS'):
                header['bus_bit_chars'] = self._extract_quoted_value(line)
            elif line.startswith('DIVIDERCHAR'):
                header['divider_char'] = self._extract_quoted_value(line)
            elif line.startswith('MANUFACTURINGGRID'):
                header['manufacturing_grid'] = float(self._extract_value(line))
            elif line.startswith('&defines'):
                if 'defines' not in header:
                    header['defines'] = []
                header['defines'].append(line)
            elif line.startswith('FIXEDMASK'):
                header['fixed_mask'] = True
            elif line.startswith('NOWIREEXTENSIONATPIN'):
                header['no_wire_extension_at_pin'] = self._extract_value(line)
            elif line.startswith('USEMINSPACING'):
                if 'use_min_spacing' not in header:
                    header['use_min_spacing'] = []
                header['use_min_spacing'].append(line)
            elif line.startswith('CLEARANCEMEASURE'):
                if 'clearance_measure' not in header:
                    header['clearance_measure'] = []
                header['clearance_measure'].append(self._extract_value(line))
                
            i += 1
            
        return header
    
    def _parse_block(self, start_idx: int) -> tuple[Optional[LEFBlock], int]:
        """Parse a single block starting at start_idx"""
        if start_idx >= len(self.lines):
            return None, start_idx
            
        line = self.lines[start_idx].strip()
        if not self._is_block_start(line):
            return None, start_idx + 1
            
        # Determine block type and name
        block_type, block_name = self._identify_block(line)
        if not block_type:
            return None, start_idx + 1
            
        block = LEFBlock(block_type=block_type, name=block_name)
        
        # Parse any additional attributes on the same line as the block declaration
        self._parse_block_declaration_attributes(block, line)
        
        # Parse block content
        i = start_idx + 1
        while i < len(self.lines):
            current_line = self.lines[i].strip()
            
            if not current_line:
                i += 1
                continue
                
            # Check for end of block
            if self._is_block_end(current_line, block_type, block_name):
                return block, i + 1
                
            # Check for sub-block
            if self._is_sub_block_start(current_line, block_type):
                sub_block, next_i = self._parse_block(i)
                if sub_block:
                    sub_type = sub_block.block_type.value
                    if sub_type not in block.sub_blocks:
                        block.sub_blocks[sub_type] = []
                    block.sub_blocks[sub_type].append(sub_block)
                i = next_i
            else:
                # Parse attributes and content
                self._parse_block_content(block, current_line)
                i += 1
                
        return block, len(self.lines)
    
    def _parse_block_declaration_attributes(self, block: LEFBlock, line: str):
        """Parse attributes that appear on the same line as block declaration"""
        line = line.strip()
        
        # For different block types, handle inline attributes differently
        if block.block_type == BlockType.PIN:
            # For PIN blocks: "PIN name DIRECTION direction [USE use] [CAPACITANCE cap] ;"
            self._parse_pin_declaration_attributes(block, line)
        elif block.block_type == BlockType.LAYER:
            # For LAYER blocks: "LAYER name [TYPE type] ;"
            self._parse_layer_declaration_attributes(block, line)
        elif block.block_type == BlockType.VIA:
            # For VIA blocks: "VIA name [DEFAULT] ;"
            self._parse_via_declaration_attributes(block, line)
        # Add more block types as needed
    
    def _parse_pin_declaration_attributes(self, block: LEFBlock, line: str):
        """Parse attributes in PIN declaration line"""
        # Pattern: PIN name [DIRECTION direction] [USE use] [CAPACITANCE cap] [POWER power] ;
        
        # Remove the PIN and name parts to get remaining attributes
        parts = line.split()
        if len(parts) < 2:
            return
            
        # Skip "PIN" and the pin name
        remaining_parts = parts[2:]
        
        i = 0
        while i < len(remaining_parts):
            part = remaining_parts[i].upper()
            
            if part == 'DIRECTION' and i + 1 < len(remaining_parts):
                direction = remaining_parts[i + 1].rstrip(' ;')
                block.attributes['direction'] = direction
                i += 2
            elif part == 'USE' and i + 1 < len(remaining_parts):
                use = remaining_parts[i + 1].rstrip(' ;')
                block.attributes['use'] = use
                i += 2
            elif part == 'CAPACITANCE' and i + 1 < len(remaining_parts):
                cap_val = remaining_parts[i + 1].rstrip(' ;')
                try:
                    block.attributes['capacitance'] = float(cap_val)
                except ValueError:
                    block.attributes['capacitance'] = cap_val
                i += 2
            elif part == 'POWER' and i + 1 < len(remaining_parts):
                power_val = remaining_parts[i + 1].rstrip(' ;')
                try:
                    block.attributes['power'] = float(power_val)
                except ValueError:
                    block.attributes['power'] = power_val
                i += 2
            else:
                # Skip unknown attributes
                i += 1
    
    def _parse_layer_declaration_attributes(self, block: LEFBlock, line: str):
        """Parse attributes in LAYER declaration line"""
        # Pattern: LAYER name [TYPE type] ;
        
        parts = line.split()
        if len(parts) < 2:
            return
            
        # Skip "LAYER" and the layer name
        remaining_parts = parts[2:]
        
        i = 0
        while i < len(remaining_parts):
            part = remaining_parts[i].upper()
            
            if part == 'TYPE' and i + 1 < len(remaining_parts):
                layer_type = remaining_parts[i + 1].rstrip(' ;')
                block.attributes['type'] = layer_type
                i += 2
            else:
                i += 1
    
    def _parse_via_declaration_attributes(self, block: LEFBlock, line: str):
        """Parse attributes in VIA declaration line"""
        # Pattern: VIA name [DEFAULT] ;
        
        if 'DEFAULT' in line.upper():
            block.attributes['default'] = True
    
    def _identify_block(self, line: str) -> tuple[Optional[BlockType], Optional[str]]:
        """Identify block type and name from opening line"""
        line = line.strip()
        
        # Simple blocks (TYPE name ...)
        patterns = {
            r'^LAYER\s+(\S+)': BlockType.LAYER,
            r'^VIA\s+(\S+)': BlockType.VIA,
            r'^VIARULE\s+(\S+)': BlockType.VIARULE,
            r'^NONDEFAULTRULE\s+(\S+)': BlockType.NONDEFAULTRULE,
            r'^SITE\s+(\S+)': BlockType.SITE,
            r'^ARRAY\s+(\S+)': BlockType.ARRAY,
            r'^MACRO\s+(\S+)': BlockType.MACRO,
            r'^PIN\s+(\S+)': BlockType.PIN,
            r'^FLOORPLAN\s+(\S+)': BlockType.FLOORPLAN,
        }
        
        for pattern, block_type in patterns.items():
            match = re.match(pattern, line)
            if match:
                return block_type, match.group(1)
                
        # Blocks without names
        if line.startswith('UNITS'):
            return BlockType.UNITS, None
        elif line.startswith('PROPERTYDEFINITIONS'):
            return BlockType.PROPERTYDEFINITIONS, None
        elif line.startswith('SPACING'):
            return BlockType.SPACING, None
        elif line.startswith('IRDROP'):
            return BlockType.IRDROP, None
        elif line.startswith('NOISETABLE'):
            return BlockType.NOISETABLE, None
        elif line.startswith('TIMING'):
            return BlockType.TIMING, None
        elif line.startswith('OBS'):
            return BlockType.OBS, None
        elif line.startswith('DENSITY'):
            return BlockType.DENSITY, None
        elif line.startswith('PORT'):
            return BlockType.PORT, None
            
        return None, None
    
    def _is_block_start(self, line: str) -> bool:
        """Check if line starts a block"""
        block_starters = [
            'UNITS', 'PROPERTYDEFINITIONS', 'SPACING', 'IRDROP', 'NOISETABLE',
            'LAYER', 'VIA', 'VIARULE', 'NONDEFAULTRULE', 'SITE', 'ARRAY', 
            'MACRO', 'PIN', 'TIMING', 'OBS', 'DENSITY', 'PORT', 'FLOORPLAN'
        ]
        
        for starter in block_starters:
            if line.startswith(starter + ' ') or line == starter:
                return True
        return False
    
    def _is_sub_block_start(self, line: str, parent_type: BlockType) -> bool:
        """Check if line starts a sub-block within parent block type"""
        if parent_type == BlockType.MACRO:
            return line.startswith(('PIN ', 'TIMING', 'OBS', 'DENSITY'))
        elif parent_type == BlockType.PIN:
            return line.startswith('PORT')
        elif parent_type == BlockType.ARRAY:
            return line.startswith('FLOORPLAN ')
        return False
    
    def _is_block_end(self, line: str, block_type: BlockType, block_name: Optional[str]) -> bool:
        """Check if line ends the current block"""
        if block_name:
            return line == f"END {block_name}" or line == f"END"
        else:
            return line == f"END {block_type.value}" or line == "END"
    
    def _parse_block_content(self, block: LEFBlock, line: str):
        """Parse content line and extract attributes"""
        line = line.strip()
        if not line or line.startswith('#'):
            return
            
        # Store raw content
        block.content_lines.append(line)
        
        # Parse common attributes
        if line.startswith('CLASS '):
            block.attributes['class'] = self._extract_value(line)
        elif line.startswith('SOURCE '):
            block.attributes['source'] = self._extract_value(line)
        elif line.startswith('SIZE '):
            size_match = re.search(r'SIZE\s+([\d.]+)\s+BY\s+([\d.]+)', line)
            if size_match:
                block.attributes['size'] = {
                    'width': float(size_match.group(1)),
                    'height': float(size_match.group(2))
                }
        elif line.startswith('DIRECTION '):
            block.attributes['direction'] = self._extract_value(line)
        elif line.startswith('USE '):
            block.attributes['use'] = self._extract_value(line)
        elif line.startswith('SYMMETRY '):
            symmetries = line.split()[1:]
            block.attributes['symmetry'] = [s.rstrip(' ;') for s in symmetries]
        elif line.startswith('TYPE '):
            block.attributes['type'] = self._extract_value(line)
        elif line.startswith('PITCH '):
            values = self._extract_numeric_values(line)
            block.attributes['pitch'] = values[0] if len(values) == 1 else values
        elif line.startswith('WIDTH '):
            # Handle both "WIDTH 1.0" and "WIDTH 1.0 ;"
            try:
                width_val = self._extract_value(line)
                block.attributes['width'] = float(width_val)
            except ValueError:
                # If conversion fails, store as string
                block.attributes['width'] = width_val
        elif line.startswith('SPACING '):
            if 'spacing' not in block.attributes:
                block.attributes['spacing'] = []
            block.attributes['spacing'].append(line)
        elif line.startswith('RESISTANCE '):
            resistance_val = self._extract_value(line)
            try:
                # Try to parse as float if it's a simple number
                block.attributes['resistance'] = float(resistance_val)
            except ValueError:
                # Store as string if it's complex (e.g., "RPERSQ 0.103")
                block.attributes['resistance'] = resistance_val
        elif line.startswith('CAPACITANCE '):
            # Handle different capacitance formats
            if 'PICOFARADS' in line or 'FEMTOFARADS' in line:
                # This is a units declaration like "CAPACITANCE PICOFARADS 10"
                parts = line.split()
                if len(parts) >= 3:
                    block.attributes['capacitance_units'] = {
                        'unit': parts[1],
                        'multiplier': parts[2].rstrip(' ;')
                    }
                else:
                    block.attributes['capacitance_units'] = line
            else:
                # This is a simple capacitance value like "CAPACITANCE 0.1"
                cap_val = self._extract_value(line)
                try:
                    block.attributes['capacitance'] = float(cap_val)
                except ValueError:
                    block.attributes['capacitance'] = cap_val
        elif line.startswith('POWER '):
            # Handle different power formats
            if 'MILLIWATTS' in line or 'WATTS' in line:
                # This is a units declaration
                parts = line.split()
                if len(parts) >= 3:
                    block.attributes['power_units'] = {
                        'unit': parts[1],
                        'multiplier': parts[2].rstrip(' ;')
                    }
                else:
                    block.attributes['power_units'] = line
            else:
                # Simple power value
                power_val = self._extract_value(line)
                try:
                    block.attributes['power'] = float(power_val)
                except ValueError:
                    block.attributes['power'] = power_val
        elif line.startswith('FOREIGN '):
            block.attributes['foreign'] = self._extract_value(line)
        elif line.startswith('RECT '):
            if 'rectangles' not in block.attributes:
                block.attributes['rectangles'] = []
            rect_coords = self._extract_numeric_values(line)
            if len(rect_coords) >= 4:
                rect_info = {
                    'x1': rect_coords[0], 'y1': rect_coords[1],
                    'x2': rect_coords[2], 'y2': rect_coords[3]
                }
                # Check for MASK information
                if 'MASK' in line:
                    mask_match = re.search(r'MASK\s+(\d+)', line)
                    if mask_match:
                        rect_info['mask'] = int(mask_match.group(1))
                block.attributes['rectangles'].append(rect_info)
        elif line.startswith('PATH '):
            if 'paths' not in block.attributes:
                block.attributes['paths'] = []
            path_coords = self._extract_numeric_values(line)
            path_info = {'coordinates': path_coords}
            # Check for MASK information
            if 'MASK' in line:
                mask_match = re.search(r'MASK\s+(\d+)', line)
                if mask_match:
                    path_info['mask'] = int(mask_match.group(1))
            block.attributes['paths'].append(path_info)
        elif line.startswith('DATABASE '):
            # Handle "DATABASE MICRONS 20000"
            parts = line.split()
            if len(parts) >= 3:
                block.attributes['database_units'] = {
                    'unit': parts[1],
                    'multiplier': parts[2].rstrip(' ;')
                }
        elif line.startswith('TIME '):
            # Handle "TIME NANOSECONDS 100"
            parts = line.split()
            if len(parts) >= 3:
                block.attributes['time_units'] = {
                    'unit': parts[1],
                    'multiplier': parts[2].rstrip(' ;')
                }
        elif line.startswith('CURRENT '):
            # Handle "CURRENT MILLIAMPS 10000"
            parts = line.split()
            if len(parts) >= 3:
                block.attributes['current_units'] = {
                    'unit': parts[1],
                    'multiplier': parts[2].rstrip(' ;')
                }
        elif line.startswith('VOLTAGE '):
            # Handle "VOLTAGE VOLTS 1000"
            parts = line.split()
            if len(parts) >= 3:
                block.attributes['voltage_units'] = {
                    'unit': parts[1],
                    'multiplier': parts[2].rstrip(' ;')
                }
        elif line.startswith('FREQUENCY '):
            # Handle "FREQUENCY MEGAHERTZ 10"
            parts = line.split()
            if len(parts) >= 3:
                block.attributes['frequency_units'] = {
                    'unit': parts[1],
                    'multiplier': parts[2].rstrip(' ;')
                }
        elif line.startswith('FROMPIN '):
            block.attributes['frompin'] = self._extract_value(line)
        elif line.startswith('TOPIN '):
            block.attributes['topin'] = self._extract_value(line)
        elif line.startswith('RISE ') or line.startswith('FALL '):
            # Handle timing arcs
            if 'timing_arcs' not in block.attributes:
                block.attributes['timing_arcs'] = []
            block.attributes['timing_arcs'].append(line)
        elif line.startswith('UNATENESS '):
            block.attributes['unateness'] = self._extract_value(line)
        elif line.startswith('VIA '):
            # Handle VIA statements in OBS
            if 'vias' not in block.attributes:
                block.attributes['vias'] = []
            via_coords = self._extract_numeric_values(line)
            via_info = {'coordinates': via_coords}
            # Extract via name
            via_match = re.search(r'VIA\s+(?:MASK\s+\d+\s+)?(?:ITERATE\s+)?(?:MASK\s+\d+\s+)?([\d.]+\s+[\d.]+)\s+(\w+)', line)
            if via_match:
                via_info['name'] = via_match.group(2)
            # Check for MASK information
            if 'MASK' in line:
                mask_match = re.search(r'MASK\s+(\d+)', line)
                if mask_match:
                    via_info['mask'] = int(mask_match.group(1))
            block.attributes['vias'].append(via_info)
        # Add more attribute parsing as needed for other LEF constructs
    
    def _extract_value(self, line: str) -> str:
        """Extract value after keyword"""
        parts = line.split()
        if len(parts) > 1:
            return parts[1].rstrip(' ;')
        return ""
    
    def _extract_quoted_value(self, line: str) -> str:
        """Extract quoted value"""
        match = re.search(r'"([^"]*)"', line)
        return match.group(1) if match else ""
    
    def _extract_numeric_values(self, line: str) -> List[float]:
        """Extract all numeric values from line"""
        numbers = re.findall(r'-?[\d.]+', line)
        return [float(n) for n in numbers]
    
    def _skip_empty_lines(self, start_idx: int) -> int:
        """Skip empty lines and comments"""
        i = start_idx
        while i < len(self.lines):
            line = self.lines[i].strip()
            if line and not line.startswith('#'):
                break
            i += 1
        return i
    
    def _block_to_dict(self, block: LEFBlock) -> Dict[str, Any]:
        """Convert LEFBlock to dictionary representation"""
        result = {
            'type': block.block_type.value,
            'name': block.name,
            'attributes': block.attributes.copy(),
            'content_lines': block.content_lines.copy()
        }
        
        # Convert sub-blocks
        if block.sub_blocks:
            result['sub_blocks'] = {}
            for sub_type, sub_block_list in block.sub_blocks.items():
                result['sub_blocks'][sub_type] = [
                    self._block_to_dict(sub_block) for sub_block in sub_block_list
                ]
        
        return result

# Convenience functions
def parse_lef_file(file_path: str) -> Dict[str, Any]:
    """Parse LEF file and return hierarchical structure"""
    parser = LEFParser()
    return parser.parse_file(file_path)

def parse_lef_content(content: str) -> Dict[str, Any]:
    """Parse LEF content string and return hierarchical structure"""
    parser = LEFParser()
    return parser.parse_content(content)

# Example usage
if __name__ == "__main__":
    # Example of how to use the parser
    sample_lef = """
    VERSION 5.8 ;
    NAMESCASESENSITIVE ON ;
    
    MACRO INV
       CLASS CORE ;
       SIZE 67.2 BY 24 ;
       SYMMETRY X Y R90 ;
       
       PIN Z DIRECTION OUTPUT ;
          USE SIGNAL ;
          CAPACITANCE 0.1 ;
          PORT
             LAYER M2 ;
                PATH 30.8 9 42 9 ;
          END
       END Z
       
       PIN A DIRECTION INPUT ;
          USE ANALOG ;
          CAPACITANCE 0.08 ;
          PORT
             LAYER M1 ;
                PATH 25.2 15 ;
          END
       END A
       
       TIMING
          FROMPIN A ;
          TOPIN Z ;
          RISE INTRINSIC .39 .41 1.2 ;
          UNATENESS INVERT ;
       END TIMING
       
    END INV
    """
    
    result = parse_lef_content(sample_lef)
    
    # Print structure
    print("LEF Structure:")
    for block_name, block_data in result['blocks'].items():
        print(f"  {block_name}:")
        for block in block_data:
            print(f"    Name: {block['name']}")
            print(f"    Attributes: {block['attributes']}")
            if 'sub_blocks' in block:
                for sub_type, sub_blocks in block['sub_blocks'].items():
                    print(f"    {sub_type}: {len(sub_blocks)} items")
                    for sub_block in sub_blocks:
                        print(f"      - {sub_block['name']}: {sub_block['attributes']}") 