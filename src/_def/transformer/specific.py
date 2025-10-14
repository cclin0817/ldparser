from .base import LineClearer, LineSeperator, LineFormatter, BlockTransformer, SectionTransformer

#############################################
# Common Line cleaner
#############################################
class CommonLineClearer(LineClearer):
    def __init__(self):
        self.end_sign = ';'

    def clear_line(self, line):
        # Strip whitespace from the line
        cleaned_line = line.strip()
        
        # Remove the end sign if present
        if cleaned_line.endswith(self.end_sign):
            cleaned_line = cleaned_line[:-1].strip()
        
        return cleaned_line

class MultiLineLineClearer(LineClearer):
    """Enhanced cleaner for multi-line content"""
    def __init__(self):
        self.end_sign = ';'

    def clear_line(self, line):
        """For multi-line content, the line is already cleaned by the parser"""
        return line.strip()

class CommonLineSeperator(LineSeperator):

    def seperate(self, line):
        """
        Separate line into tokens following these rules:
        1. + word should be put together as "+ word"
        2. ( ) content should be put together ONLY when standalone (with whitespace before)
        3. " " content should be put together
        4. Words with attached parentheses like "asdf(xxxx)" stay together
        """
        tokens = []
        i = 0
        line = line.strip()
        
        while i < len(line):
            # Skip whitespace
            while i < len(line) and line[i].isspace():
                i += 1
            
            if i >= len(line):
                break
            
            # Rule 1: Handle + followed by word
            if line[i] == '+' and i + 1 < len(line):
                # Find the end of the word after +
                j = i + 1
                # Skip whitespace after +
                while j < len(line) and line[j].isspace():
                    j += 1
                # Find end of word (including parentheses if attached)
                word_start = j
                while j < len(line) and not line[j].isspace() and line[j] != '"':
                    j += 1
                if word_start < j:
                    tokens.append(f"+ {line[word_start:j]}")
                    i = j
                else:
                    tokens.append('+')
                    i += 1
                continue
            
            # Rule 2: Handle standalone parentheses content (only when preceded by whitespace or start of line)
            if line[i] == '(' and (i == 0 or line[i-1].isspace()):
                j = i + 1
                paren_count = 1
                while j < len(line) and paren_count > 0:
                    if line[j] == '(':
                        paren_count += 1
                    elif line[j] == ')':
                        paren_count -= 1
                    j += 1
                tokens.append(line[i:j])
                i = j
                continue
            
            # Rule 3: Handle quoted content
            if line[i] == '"':
                j = i + 1
                while j < len(line) and line[j] != '"':
                    if line[j] == '\\':  # Handle escaped quotes
                        j += 2
                    else:
                        j += 1
                if j < len(line):  # Include closing quote
                    j += 1
                tokens.append(line[i:j])
                i = j
                continue
            
            # Handle regular words (including words with attached parentheses)
            j = i
            while j < len(line) and not line[j].isspace() and line[j] != '"':
                # Special case: if we hit a '(' that's preceded by whitespace, stop here
                if line[j] == '(' and j > i and line[j-1].isspace():
                    break
                j += 1
            
            if j > i:  # Only add non-empty tokens
                tokens.append(line[i:j])
                i = j
            else:
                i += 1  # Skip single character if we couldn't form a token
        
        return tokens

#############################################
# Specific Line formatter
#############################################
class ComponentHeadFormatter(LineFormatter):
    '''
    - compName modelName[netName | *]
    + FEATURE value1 value2 ...
    '''
    
    def format(self, seperate_components):
        if len(seperate_components) < 3:
            return {
                'ins_name': 'UNKNOWN',
                'cell_name': 'UNKNOWN',
                'features': {}
            }
        
        ins_name = seperate_components[1]
        cell_name = seperate_components[2]
        
        # Parse features starting from index 3
        features = {}
        i = 3
        
        while i < len(seperate_components):
            token = seperate_components[i]
            
            # Look for feature tokens that start with "+"
            if token.startswith('+ '):
                feature_name = token[2:]  # Remove "+ " prefix
                feature_values = []
                
                # Collect values until next "+" token or end of list
                i += 1
                while i < len(seperate_components) and not seperate_components[i].startswith('+ '):
                    feature_values.append(seperate_components[i])
                    i += 1
                
                # Store as tuple (single value becomes single-element tuple)
                if len(feature_values) == 1:
                    features[feature_name] = feature_values[0]
                else:
                    features[feature_name] = tuple(feature_values)
            else:
                i += 1
        
        
        # Extract placement info if PLACED feature exists
        placement_info = {}
        if 'PLACED' in features:
            placed_data = features['PLACED']
            if isinstance(placed_data, tuple) and len(placed_data) >= 2:
                coords_str = placed_data[0]  # '( 100 100 )'
                orientation = placed_data[1]  # 'N'
                
                # Parse coordinates from string like '( 100 100 )'
                coords_cleaned = coords_str.strip('() ')
                coord_parts = coords_cleaned.split()
                if len(coord_parts) >= 2:
                    try:
                        x = int(coord_parts[0])
                        y = int(coord_parts[1])
                        placement_info = {
                            'x': x,
                            'y': y,
                            'orientation': orientation
                        }
                    except ValueError:
                        # If conversion fails, store as strings
                        placement_info = {
                            'x': coord_parts[0],
                            'y': coord_parts[1],
                            'orientation': orientation
                        }
            return {
                'ins_name': ins_name,
                'cell_name': cell_name,
                'placementInfo': (placement_info['x'], placement_info['y'], placement_info['orientation']),
                'features': features
            }
        else:
            return {
                'ins_name': ins_name,
                'cell_name': cell_name,
                'features': features
            }

class NetHeadFormatter(LineFormatter):
    '''
    - { netName [( {compName | PIN} pinName 
#           [+ SYNTHESIZED])]
    '''
    
    def format(self, seperate_components):
        net_name = seperate_components[1]

        connections = []
        for ins_pin in seperate_components[2:]:
            # ins_pin = "( ins_name pin_name )"
            # Remove parentheses and split by whitespace
            cleaned = ins_pin.strip('() ')
            parts = cleaned.split()
            if len(parts) >= 2:
                ins_name = parts[0]
                pin_name = parts[1]
                connections.append({
                    'ins_name': ins_name,
                    'pin_name': pin_name
                })
            else:
                breakpoint()
        return {
            'net_name': net_name,
            'connections': connections
        }

class EnhancedNetHeadFormatter(LineFormatter):
    '''
    Enhanced formatter for multi-line NET definitions
    - { netName [( {compName | PIN} pinName [+ SYNTHESIZED])]
    '''
    
    def format(self, seperate_components):
        if len(seperate_components) < 2:
            return {
                'net_name': 'UNKNOWN',
                'connections': [],
                'properties': []
            }
        net_name = seperate_components[1]
        connections = []
        properties = []
        # breakpoint()
        i = 2
        property_start = False
        # Here 
        while i < len(seperate_components):
            token = seperate_components[i]
            # Handle connection entries: ( ins_name pin_name )
            if token.startswith('(') and token.endswith(')') and not property_start:
                cleaned = token.strip('() ')
                parts = cleaned.split()
                if len(parts) >= 2:
                    ins_name = parts[0]
                    pin_name = parts[1]
                    connections.append({
                        'ins_name': ins_name,
                        'pin_name': pin_name
                    })
                i += 1
            
            # Handle properties: + PROPERTY_NAME [value]
            elif token.startswith('+ '):
                property_start = True
                property_name = token[2:]  # Remove "+ "
                property_value = None
                
                # Check if next token is a value (not starting with + or ()
                if (i + 1 < len(seperate_components) and 
                    not seperate_components[i + 1].startswith('+') and 
                    not seperate_components[i + 1].startswith('(')):
                    property_value = seperate_components[i + 1]
                    i += 2
                else:
                    i += 1
                
                properties.append({
                    'name': property_name,
                    'value': property_value
                })
            
            else:
                i += 1
        
        return {
            'net_name': net_name,
            'connections': connections,
            'properties': properties
        }

#############################################
# Specific Section transformer
#############################################

class NoPerpertySectionTransformer(SectionTransformer):
    '''
    Currently, we don't need to parse the properties of the section, so we only need to parse the head line.
    '''
    def __init__(self, line_cleaner, line_seperator, line_formatter):
        self.line_cleaner = line_cleaner
        self.line_seperator = line_seperator
        self.line_formatter = line_formatter

    def transform(self, raw_section : dict):
        '''
        input: {'head_section': , 'property_section':[]}
        '''
        head_line = raw_section['head_section']
        cleaned_head_line = self.line_cleaner.clear_line(head_line)
        seperated_head_line = self.line_seperator.seperate(cleaned_head_line)
        formatted_head_line = self.line_formatter.format(seperated_head_line)
        return formatted_head_line

class EnhancedSectionTransformer(SectionTransformer):
    '''
    Enhanced transformer for multi-line sections
    '''
    def __init__(self, line_cleaner, line_seperator, line_formatter):
        self.line_cleaner = line_cleaner
        self.line_seperator = line_seperator
        self.line_formatter = line_formatter

    def transform(self, raw_section: dict):
        '''
        input: {'head_section': full_content, 'property_section':[], 'raw_content': [lines]}
        '''
        # Use the already cleaned head_section from MultiLineDashParser
        head_line = raw_section['head_section']
        seperated_head_line = self.line_seperator.seperate(head_line)
        formatted_head_line = self.line_formatter.format(seperated_head_line)
        
        # Add raw content for debugging if needed
        if 'raw_content' in raw_section:
            formatted_head_line['raw_lines'] = raw_section['raw_content']
        
        return formatted_head_line

#############################################
# Specific Block transformer
#############################################

class NoPropertyBlockTransformer(BlockTransformer):
    '''
    '''
    def __init__(self, line_cleaner, line_seperator, line_formatter):
        self.section_transformer = NoPerpertySectionTransformer(
            line_cleaner,
            line_seperator,
            line_formatter
        )

    def transform(self, list_of_raw_sections : list[dict]):
        '''
        input: [{'head_section': , 'property_section':[]}]
        '''
        component_list = []
        
        for raw_section in list_of_raw_sections:
            component_section = self.section_transformer.transform(raw_section)
            
            component_list.append(component_section)

        return component_list

class EnhancedBlockTransformer(BlockTransformer):
    '''
    Enhanced transformer for multi-line blocks
    '''
    def __init__(self, line_cleaner, line_seperator, line_formatter):
        self.section_transformer = EnhancedSectionTransformer(
            line_cleaner,
            line_seperator,
            line_formatter
        )

    def transform(self, list_of_raw_sections: list[dict]):
        '''
        input: [{'head_section': full_content, 'property_section':[], 'raw_content': [lines]}]
        '''
        result_list = []
        
        for raw_section in list_of_raw_sections:
            transformed_section = self.section_transformer.transform(raw_section)
            result_list.append(transformed_section)

        return result_list

component_block_transformer = EnhancedBlockTransformer(
    MultiLineLineClearer(),
    CommonLineSeperator(),
    ComponentHeadFormatter()
)

net_block_transformer = NoPropertyBlockTransformer(
    CommonLineClearer(),
    CommonLineSeperator(),
    NetHeadFormatter()
)

# Enhanced NET transformer for multi-line support
enhanced_net_block_transformer = EnhancedBlockTransformer(
    MultiLineLineClearer(),
    CommonLineSeperator(),
    EnhancedNetHeadFormatter()
)