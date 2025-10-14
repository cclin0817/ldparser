'''
Here we define 
1. Block: NETS -> END NETS;
2. Section: "- N1" -> ";"
3. LINE: single line

NETS 6 ;
- SCAN ( scancell1 PA10 + SYNTHESIZED ) ( scancell2 PA2 + SYNTHESIZED )
  + SOURCE TEST ;
- N1 ( I1 A ) ( PIN P0 )
  + SHIELDNET SN1 ;
- N2 ( I3 A ) ( PIN P2 )
  + FIXED
    M2 ( 14000 341440 ) ( 9600 * ) ( * 282400 ) M1_M2 ( 2400 * )
    NEW M1 TAPERRULE RULE1 ( 2400 282400 ) ( 240 * )
  + SOURCE DIST
  + PATTERN BALANCED
  + WEIGHT 500 ;
- N3 ( I4 A ) ( PIN P3 )
  + COVER
    M2 ( 14000 341440 ) ( 9600 * ) ( * 282400 ) M1_M2 ( 2400 * ) VIAGEN12_0 N
    NEW M1 ( 2400 282400 ) ( 240 * ) ;

'''


class LineClearer:
    '''
    This is the base class for all the line cleaners.
    The input line will be "raw" line.
    return the "cleaned" line.
    '''
    def clear_line(self, line):
        pass

class LineSeperator:
    '''
    This is the base class for all the line seperators.
    The input line will be "cleaned" line.
    return the "seperated" line.
    '''
    def seperate(self, line):
        pass

class LineFormatter:
    '''
    Given separated line with n components, 
    return a dict which assign each component as key or values.
    '''
    def format(self, line):
        pass

class LineTransformer:
    '''
    This is the base class for all the line transformers.

    The structure of each line will be formated as:
    <sign (optional)> <key1> <key2> <value>
    '''
    def __init__(self, clean_class, seperator_class, formatter_class):
        self.cleaner = clean_class()
        self.seperator = seperator_class()
        self.formatter = formatter_class()
    
    
    def transform(self, line):
        cleaned_line = self.cleaner.clear_line(line)
        seperated_line = self.seperator.seperator(cleaned_line)
        formatted_line = self.formatter.formater(seperated_line)
        return formatted_line

class SectionTransformer:
    '''
    This is the base class for all the block transformers.
    '''
    def __init__(self):
        pass


class BlockTransformer:
    '''
    This is the base class for all the block transformers.
    '''
    def __init__(self):
        pass
