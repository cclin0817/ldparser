#!/usr/bin/env python3
"""
DEF (Design Exchange Format) Parser

This parser extracts information from DEF files including:
- Header information (VERSION, DESIGN, UNITS, etc.)
- COMPONENTS (instance placements)
- NETS (connectivity information)

The UNITS information is particularly important for coordinate conversions.
"""

import os
from src.parser.specifig_parser import HeaderParser
from src.parser.specifig_parser import BlockParserNoEnd
from src.parser.specifig_parser import BlockParserWithEnd, MultiLineBlockParserWithEnd

from src._def.transformer.specific import component_block_transformer, enhanced_net_block_transformer
from tqdm import tqdm
from loguru import logger
import pickle
import argparse
import re


class DefParser:
    def __init__(self, def_file_path, Header_list, NoEndBlockList, WithEndBlockList, used_prefix):
        self.def_file_path = def_file_path
        self.Header_list = Header_list
        self.NoEndBlockList = NoEndBlockList
        self.WithEndBlockList = WithEndBlockList
        self.used_prefix = used_prefix

        self.header_parser = HeaderParser()
        self.block_parser_no_end = BlockParserNoEnd()
        self.block_parser_with_end = BlockParserWithEnd()
        # Enhanced parser for multi-line blocks like NETS
        self.multiline_block_parser = MultiLineBlockParserWithEnd()

        self.block_collector = {}
        self.used_block_collector = {}
        self.header_info = {}


    def parse(self):
        """
        Main parsing function that processes the DEF file line by line

        Returns:
            dict: Contains 'components', 'nets', and 'header' information
        """
        # Get file size for progress tracking
        file_size = os.path.getsize(self.def_file_path)

        # Main parse loop: for each line, find the right parser and delegate
        with open(self.def_file_path, "r", encoding='utf-8', errors='ignore') as f:
            # Create progress bar
            with tqdm(total=file_size, unit='B', unit_scale=True, desc="Parsing DEF file") as pbar:
                while line := f.readline():
                    # Update progress bar
                    pbar.update(len(line.encode('utf-8')))

                    try:
                        prefix = line.split()[0]
                    except:
                        continue

                    # Skip comment lines starting with #
                    if prefix.startswith('#'):
                        continue

                    if prefix in self.Header_list:
                        self.block_collector[prefix] = self.header_parser.parse(f, line, prefix)
                    elif prefix in self.NoEndBlockList:
                        if prefix not in self.block_collector:
                            self.block_collector[prefix] = []
                        self.block_collector[prefix].append(self.block_parser_no_end.parse(f, line, prefix))
                    elif prefix in self.WithEndBlockList:
                        # Use enhanced parser for NETS and COMPONENTS to handle multi-line entries
                        if prefix == "NETS" or prefix == "COMPONENTS":
                            self.block_collector[prefix] = self.multiline_block_parser.parse(f, line, prefix)
                        else:
                            self.block_collector[prefix] = self.block_parser_with_end.parse(f, line, prefix)
                    else:
                        logger.debug(f"Unknown prefix: {prefix}")

        # Parse header information including UNITS
        self.header_info = self._parse_header_info()

        # Log which sections were found
        logger.info(f"Found DEF sections: {list(self.block_collector.keys())}")
        logger.info(f"Required sections: {self.used_prefix}")

        # Collect only the sections we need
        for prefix in self.used_prefix:
            if prefix in self.block_collector:
                self.used_block_collector[prefix] = self.block_collector[prefix]
                logger.info(f"Successfully loaded {prefix} section with {len(self.block_collector[prefix])} entries")
            else:
                logger.warning(f"Warning: {prefix} section not found in DEF file")

        # Transform COMPONENTS if it exists
        component_list = []
        if 'COMPONENTS' in self.used_block_collector:
            component_list = component_block_transformer.transform(self.used_block_collector['COMPONENTS'])
            logger.info(f"Successfully parsed {len(component_list)} components")
        else:
            logger.warning("No COMPONENTS section found in DEF file")

        # Transform NETS if it exists (may not exist in placement-only DEF files)
        net_list = []
        if 'NETS' in self.used_block_collector:
            net_list = enhanced_net_block_transformer.transform(self.used_block_collector['NETS'])
            logger.info(f"Successfully parsed {len(net_list)} nets")
        else:
            logger.info("No NETS section in DEF file (this is normal for placement-only files)")

        return {
            'components': component_list,
            'nets': net_list,
            'header': self.header_info
        }

    def _parse_header_info(self):
        """
        Parse header information from the DEF file

        Returns:
            dict: Header information including VERSION, DESIGN, UNITS, etc.
        """
        header_info = {}

        # Parse VERSION
        if 'VERSION' in self.block_collector:
            version_line = self.block_collector['VERSION'][0]
            match = re.search(r'VERSION\s+([\d.]+)', version_line)
            if match:
                header_info['version'] = match.group(1)

        # Parse DESIGN name
        if 'DESIGN' in self.block_collector:
            design_line = self.block_collector['DESIGN'][0]
            match = re.search(r'DESIGN\s+(\S+)', design_line)
            if match:
                header_info['design'] = match.group(1)

        # Parse TECHNOLOGY
        if 'TECHNOLOGY' in self.block_collector:
            tech_line = self.block_collector['TECHNOLOGY'][0]
            match = re.search(r'TECHNOLOGY\s+(\S+)', tech_line)
            if match:
                header_info['technology'] = match.group(1)

        # Parse UNITS DISTANCE MICRONS (CRITICAL for coordinate conversion)
        if 'UNITS' in self.block_collector:
            units_line = self.block_collector['UNITS'][0]
            # Format: "UNITS DISTANCE MICRONS 2000 ;"
            match = re.search(r'UNITS\s+DISTANCE\s+MICRONS\s+(\d+)', units_line)
            if match:
                units_value = int(match.group(1))
                header_info['units'] = {
                    'distance': 'MICRONS',
                    'database_units_per_micron': units_value
                }
                logger.info(f"UNITS: {units_value} database units per micron")
            else:
                logger.warning("Failed to parse UNITS DISTANCE MICRONS value")
                header_info['units'] = {
                    'distance': 'MICRONS',
                    'database_units_per_micron': 1000  # Default value
                }
        else:
            logger.warning("No UNITS found in DEF file, using default (1000)")
            header_info['units'] = {
                'distance': 'MICRONS',
                'database_units_per_micron': 1000  # Default value
            }

        # Parse DIVIDERCHAR
        if 'DIVIDERCHAR' in self.block_collector:
            divider_line = self.block_collector['DIVIDERCHAR'][0]
            match = re.search(r'DIVIDERCHAR\s+"(.)"', divider_line)
            if match:
                header_info['dividerchar'] = match.group(1)

        # Parse BUSBITCHARS
        if 'BUSBITCHARS' in self.block_collector:
            busbit_line = self.block_collector['BUSBITCHARS'][0]
            match = re.search(r'BUSBITCHARS\s+"(..)"', busbit_line)
            if match:
                header_info['busbitchars'] = match.group(1)

        return header_info


parser = argparse.ArgumentParser(description='Parse DEF file and extract component/net information')
parser.add_argument('--def_path', type=str, default='test_data/complete.5.8.def',
                    help='Path to the DEF file')
parser.add_argument('--output_dir', type=str, default='temp',
                    help='Path to the output directory')
parser.add_argument('--debug', action='store_true',
                    help='Enable debug output')
args = parser.parse_args()
def_path = args.def_path
output_dir = args.output_dir

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

Header_list = set([
    "VERSION",
    "NAMESCASESENSITIVE",
    "DIVIDERCHAR",
    "BUSBITCHARS",
    "DESIGN",
    "TECHNOLOGY",
    "UNITS"
])

WithEndBlockList = set([
    "PROPERTYDEFINITIONS",
    "VIAS",
    "STYLES",
    "NONDEFAULTRULES",
    "REGIONS",
    "COMPONENTS",
    "PINS",
    "PINPROPERTIES",
    "BLOCKAGES",
    "SPECIALNETS",
    "NETS",
    "SCANCHAINS",
    "GROUPS",
    "SLOTS",
    "FILLS",
    "BEGINEXT"
])

NoEndBlockList = set([
    "DIEAREA",
    "ROW",
    "TRACKS",
    "GCELLGRID",
])

# Parse COMPONENTS section (required)
# Add 'NETS' if your DEF file contains connectivity information
used_prefix = ['COMPONENTS']

if __name__ == "__main__":
    logger.info("Starting DEF file parsing")
    logger.info(f"Input file: {def_path}")
    logger.info(f"Output directory: {output_dir}")

    def_parser = DefParser(def_path, Header_list, NoEndBlockList,
                          WithEndBlockList, used_prefix)
    def_content = def_parser.parse()
    logger.info("Finished DEF file parsing")

    # Log header information
    logger.info("=== DEF Header Information ===")
    for key, value in def_content['header'].items():
        logger.info(f"{key}: {value}")
    logger.info("=" * 50)

    # DEBUG: Check first few components to see placement data
    if args.debug and def_content['components']:
        logger.info("=== DEBUG: First 3 components ===")
        for i, comp in enumerate(def_content['components'][:min(3, len(def_content['components']))]):
            logger.info(f"Component {i}: {comp.get('ins_name', 'UNKNOWN')}")
            if 'placementInfo' in comp:
                logger.info(f"  Has placementInfo: {comp['placementInfo']}")
            else:
                logger.info(f"  NO placementInfo! Features: {comp.get('features', {})}")
        logger.info("=== END DEBUG ===")

    # Process COMPONENTS
    logger.info("Processing COMPONENTS data")
    instance2id = {ins_dict['ins_name']: index
                   for index, ins_dict in enumerate(def_content['components'])}

    id2instance_info = {}
    components_with_placement = 0
    components_without_placement = 0

    for i, comp in tqdm(enumerate(def_content['components']),
                        desc="Processing components",
                        total=len(def_content['components'])):
        if 'placementInfo' in comp:
            id2instance_info[i] = {
                'instance_name': comp['ins_name'],
                'cell_name': comp['cell_name'],
                'placementInfo': comp['placementInfo']
            }
            components_with_placement += 1
        else:
            id2instance_info[i] = {
                'instance_name': comp['ins_name'],
                'cell_name': comp['cell_name'],
            }
            components_without_placement += 1

    logger.info(f"Components with placement: {components_with_placement}")
    logger.info(f"Components without placement: {components_without_placement}")

    # Process NETS (if they exist)
    net2id = {}
    id2net_info = {}

    if def_content['nets'] and len(def_content['nets']) > 0:
        logger.info(f"Processing {len(def_content['nets'])} nets")
        net2id = {net_dict['net_name']: index
                  for index, net_dict in enumerate(def_content['nets'])}

        for i, net in tqdm(enumerate(def_content['nets']),
                          desc="Processing nets",
                          total=len(def_content['nets'])):
            id2net_info[i] = {
                'net_name': net['net_name'],
                'connections': [{'instance_name': ins_pin_dict['ins_name'],
                                'pin_name': ins_pin_dict['pin_name']}
                               for ins_pin_dict in net['connections']
                               if ins_pin_dict['ins_name'] != 'PIN']
            }

        # Delete nets with only one connection (dangling nets)
        seen = set([])
        current_keys = [ele for ele in id2net_info.keys()]
        for key in current_keys:
            if key not in seen:
                seen.add(key)
                if len(id2net_info[key]['connections']) == 1:
                    del id2net_info[key]
                    current_keys.remove(key)

        logger.info(f"After filtering dangling nets, {len(id2net_info)} nets remain")
    else:
        logger.info("No NETS information in DEF file (placement-only DEF)")

    # Prepare output data structure
    def_output = {
        'instance2id': instance2id,
        'id2instanceInfo': id2instance_info,
        'net2id': net2id,
        'id2NetInfo': id2net_info,
        'header': def_content['header']  # Include header with UNITS information
    }

    # Save to pickle file
    output_file = os.path.join(output_dir, 'def_outputs.pkl')
    with open(output_file, 'wb') as f:
        pickle.dump(def_output, f)

    logger.info(f"Successfully saved DEF data to {output_file}")
    logger.info(f"Summary:")
    logger.info(f"  - Components: {len(instance2id)}")
    logger.info(f"  - Nets: {len(id2net_info)}")
    logger.info(f"  - Database units per micron: {def_content['header']['units']['database_units_per_micron']}")
