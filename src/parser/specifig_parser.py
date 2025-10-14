from src.parser.base import BaseParser

class HeaderParser(BaseParser):
    

    def parse(self, f, first_line, keyward):
        return [first_line]

class BlockParserNoEnd(BaseParser):

    def parse(self, f, first_line, keyward):
        self.record = [first_line]
        if ";" in first_line:
            return self.record
        else:
            while (line := f.readline()) and ";" not in line:
                self.record.append(line)
            self.record.append(line)
        return self.record
    
class BlockParserWithEnd(BaseParser):
    def __init__(self):
        self.dash_parser = DashParser()

    def parse(self, f, first_line, keyward):
        self.record = []
        while line := f.readline():
            if line.strip().startswith("- "):
                self.record.append(self.dash_parser.parse(f, line, keyward) )
            if line == '\n':
                continue
            if line.strip() == f"END {keyward}":
                break
        return self.record

class MultiLineBlockParserWithEnd(BaseParser):
    """Enhanced parser for blocks that can have multi-line entries (like NETS)"""
    def __init__(self):
        self.dash_parser = MultiLineDashParser()

    def parse(self, f, first_line, keyward):
        self.record = []
        while line := f.readline():
            if line.strip().startswith("- "):
                self.record.append(self.dash_parser.parse(f, line, keyward))
            if line == '\n':
                continue
            if line.strip() == f"END {keyward}":
                break
        return self.record

class DashParser(BaseParser):

    def parse(self, f, first_line, keyward):
        self.record = {
            'head_section': first_line,
            'property_section': [],
        }
        if ";" in first_line:
            return self.record
        else:
            while line := f.readline():
                self.record['property_section'].append(line)
                if ";" in line:
                    break
        return self.record

class MultiLineDashParser(BaseParser):
    """Enhanced parser that can handle multi-line dash entries"""
    
    def parse(self, f, first_line, keyward):
        """
        Parse a dash entry that may span multiple lines.
        Collects all content from the dash line until the semicolon.
        """
        # Collect all lines for this dash entry
        all_content = [first_line.strip()]
        
        # If the first line already has a semicolon, we're done
        if ";" in first_line:
            # Remove the semicolon and join everything
            full_content = first_line.strip()
            if full_content.endswith(';'):
                full_content = full_content[:-1].strip()
            
            return {
                'head_section': full_content,
                'property_section': [],
                'raw_content': [first_line.strip()]
            }
        
        # Otherwise, keep reading until we find the semicolon
        while line := f.readline():
            all_content.append(line.strip())
            if ";" in line:
                break
        
        # Join all content and remove the final semicolon
        full_content = ' '.join(all_content)
        if full_content.endswith(';'):
            full_content = full_content[:-1].strip()
        
        return {
            'head_section': full_content,
            'property_section': [],
            'raw_content': all_content
        }

class PBlockParserWithEnd(BaseParser):
    def __init__(self):
        self.dash_parser = DashParser()

    def parse(self, f, first_line, keyward):
        # pn = first_line.split()[1]
        self.record = []
        while line := f.readline():
            if line.strip() == f"END {keyward}":
                break
            else:
                self.record.append(line)
        return self.record

class PnBlockParserWithEnd(BaseParser):
    def __init__(self):
        self.dash_parser = DashParser()

    def parse(self, f, first_line, keyward):
        pn = first_line.split()[1]
        
        self.record = []
        while line := f.readline():
            
            if line.startswith(f"END"):# TODO: 这里需要修改
                break
            else:
                self.record.append(line)
        return self.record
