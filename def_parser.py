import os
from src.parser.specifig_parser import HeaderParser
from src.parser.specifig_parser import BlockParserNoEnd
from src.parser.specifig_parser import BlockParserWithEnd, MultiLineBlockParserWithEnd

from src._def.transformer.specific import component_block_transformer, enhanced_net_block_transformer
from tqdm import tqdm
from loguru import logger
import pickle
import argparse
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
        

    def parse(self):
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
                    if prefix in self.Header_list:
                        self.block_collector[prefix] = self.header_parser.parse(f, line, prefix)
                    elif prefix in self.NoEndBlockList:
                        if prefix not in self.block_collector:
                            self.block_collector[prefix] = []
                        self.block_collector[prefix].append(self.block_parser_no_end.parse(f, line, prefix))
                    elif prefix in self.WithEndBlockList:
                        # Use enhanced parser for NETS to handle multi-line entries
                        if prefix == "NETS" or prefix == "COMPONENTS":
                            self.block_collector[prefix] = self.multiline_block_parser.parse(f, line, prefix)
                        else:
                            self.block_collector[prefix] = self.block_parser_with_end.parse(f, line, prefix)
                    else:
                        print(f"Unknown prefix: {prefix}")
        
        for prefix in self.used_prefix:
            if prefix in self.block_collector:
                self.used_block_collector[prefix] = self.block_collector[prefix]
        

        component_list = component_block_transformer.transform(self.used_block_collector['COMPONENTS'])
        # Use enhanced transformer for NETS
        net_list = enhanced_net_block_transformer.transform(self.used_block_collector['NETS'])
        return {
            'components': component_list,
            'nets': net_list
        }

parser = argparse.ArgumentParser()
parser.add_argument('--def_path', type=str, default='test_data/complete.5.8.def', help='Path to the DEF file')
parser.add_argument('--output_dir', type=str, default='./tmp', help='Path to the output file')
args = parser.parse_args()
def_path = args.def_path
output_dir = args.output_dir

Header_list = set([
    "VERSION",
    "NAMESCASESENSITIVE",
    "DIVIDERCHAR",
    "BUSBITCHARS",
    "DESIGN",
    "TECHNOLOGY",
    "UNITS DISTANCE MICRONS"
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

used_prefix = ['COMPONENTS', 'NETS']

if __name__ == "__main__":
    logger.info("Start parsing DEF file")
    def_parser =  DefParser(def_path, Header_list, NoEndBlockList, WithEndBlockList, used_prefix) # DefParser("/home/lewis/1project/def_lef_py/test_data/complete.5.8.def", Header_list, NoEndBlockList, WithEndBlockList, used_prefix)
    def_content = def_parser.parse()
    logger.info("Finish parsing DEF file")

    instance2id = { ins_dict['ins_name']: index for index , ins_dict in enumerate(def_content['components'])}
    id2instance_info = {}
    for i, comp in tqdm(enumerate(def_content['components'])):
        if 'placementInfo' in comp:
            id2instance_info[i] = {
                'instance_name': comp['ins_name'],
                'cell_name': comp['cell_name'],
                'placementInfo': comp['placementInfo']
            }
        else:
            id2instance_info[i] = {
                'instance_name': comp['ins_name'],
                'cell_name': comp['cell_name'],
            }
    
    
    net2id = { net_dict['net_name']: index for index, net_dict in enumerate(def_content['nets'])}
    id2net_info = {}
    for i, net in tqdm(enumerate(def_content['nets'])):
        id2net_info[i] = {
            'net_name': net['net_name'],
            'connections': [{'instance_name': ins_pin_dict['ins_name'] , 'pin_name': ins_pin_dict['pin_name'] }
                            for ins_pin_dict in net['connections'] if ins_pin_dict['ins_name'] != 'PIN']
        }
    
    # Delete all cell with only one instance
    seen = set([])
    current_keys = [ele for ele in id2net_info.keys()]
    for key in current_keys:
        if key not in seen:
            seen.add(key)
            if len(id2net_info[key]['connections']) == 1:
                del id2net_info[key]
                current_keys.remove(key)
    
    def_output = {'instance2id': instance2id, 'id2instanceInfo': id2instance_info, 'net2id': net2id, 'id2NetInfo': id2net_info}
    with open(output_dir + '/def_outputs.pkl', 'wb') as f:
        pickle.dump(def_output, f)
    
        