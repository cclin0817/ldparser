

from src.parser.specifig_parser import HeaderParser
from src.parser.specifig_parser import PBlockParserWithEnd
from src.parser.specifig_parser import PnBlockParserWithEnd

from src._def.transformer.specific import component_block_transformer, net_block_transformer


class LefParser:
    def __init__(self, lef_file_path, Header_list, P_end_block, Pn_end_block, used_prefix):
        self.lef_file_path = lef_file_path
        self.Header_list = Header_list
        self.P_end_block = P_end_block
        self.Pn_end_block = Pn_end_block
        self.used_prefix = used_prefix

        self.header_parser = HeaderParser()
        self.p_block_parser_with_end = PBlockParserWithEnd()
        self.pn_block_parser_with_end = PnBlockParserWithEnd()

        self.block_collector = {}
        self.used_block_collector = {}
        

    def parse(self):
        # Main parse loop: for each line, find the right parser and delegate
        with open(self.lef_file_path, "r", encoding='utf-8', errors='ignore') as f:
            while line := f.readline():
                try:
                    print(line)
                    prefix = line.split()[0]
                    print(prefix)
                except:
                    continue
                if prefix in self.Header_list:
                    self.block_collector[prefix] = self.header_parser.parse(f, line, prefix)
                elif prefix in self.Pn_end_block:
                    pn = line.split()[1]
                    if prefix not in self.block_collector:
                        self.block_collector[prefix] = {}
                    self.block_collector[prefix][pn] = self.pn_block_parser_with_end.parse(f, line, prefix)
                elif prefix in self.P_end_block:
                    self.block_collector[prefix] = self.p_block_parser_with_end.parse(f, line, prefix)
                else:
                    print(f"Unknown prefix: {prefix}")
        
        for prefix in self.used_prefix:
            if prefix in self.block_collector:
                self.used_block_collector[prefix] = self.block_collector[prefix]
        
        breakpoint()
        component_list = component_block_transformer.transform(self.used_block_collector['COMPONENTS'])
        net_list = net_block_transformer.transform(self.used_block_collector['NETS'])
        return {
            'components': component_list,
            'nets': net_list
        }


Header_list = set([
    "VERSION",
    "NAMESCASESENSITIVE",
    "FIXEDMASK",
    "NOWIREEXTENSIONATPIN",
    "BUSBITCHARS",
    "DIVIDERCHAR",
    "USEMINSPACING",
    "USEMINSPACING",
    "CLEARANCEMEASURE",
    "CLEARANCEMEASURE",
])

P_end_block = set([
    "UNITS", "PROPERTYDEFINITIONS", "SPACING", "IRDROP"
])

Pn_end_block = set([
    "LAYER", "VIA", "VIARULE", "NONDEFAULTRULE", "SITE", "MACRO"
])

used_prefix = ['MACRO']

if __name__ == "__main__":
    def_parser = LefParser("/home/lewis/1project/def_lef_py/test_data/complete.5.8.lef", Header_list, P_end_block, Pn_end_block, used_prefix)
    def_parser.parse()
        