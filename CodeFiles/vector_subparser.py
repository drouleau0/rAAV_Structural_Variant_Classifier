import ply.lex as lex
import ply.yacc as yacc

EXPECTED_SPECIES = ['expected', 'expected_selfprime']
SNAPBACK_SPECIES = ['snapback', 'snapback_selfprime']
TRUNCATED_SNAPBACK_SPECIES = ['truncated_sp_IPP', 'truncated_sp_PPI', 'truncated_snapback_selfprime']


class VectorLexer:
    def __init__(self):
        self.lexer = lex.lex(module=self)

    tokens = (
        'P',
        'AND',
        'I'
    )

    t_P = r'(Payload)'
    t_I = r'(ITR-FLIP)'
    t_AND = r'\s'

    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])

    # returns a list of dictionaries for testing, one dictionary for each token read
    def test(self, data):
        self.lexer.input(data)
        test_list = list()
        for tok in self.lexer:
            test_list.append({'type': tok.type, 'value': tok.value, 'lineno': tok.lineno, 'lexpos': tok.lexpos})
        return test_list


class VectorSubParser:
    precedence = (('right', 'AND'),)
    expected_species_have_only_full_payloads = True

    _end_state = ''
    _repeat_counter = -1

	# initialize the parser with arguments. The lexer is also instantiated
    def __init__(self, lexer, require_full_payloads_in_expected=True):
        self.tokens = lexer.tokens
        # doesn't write the parsetab.py file since the table is small, negligible time is added
        self.parser = yacc.yacc(module=self, debug=False, write_tables=False)
        VectorSubParser.expected_species_have_only_full_payloads = require_full_payloads_in_expected

    # formats input data before running it through parsing. Raises an error for
    # tiles that aren't Payload or ITR. Also allows digits to be in the first two 
    # tiles, since those are the count and proportions in .counts file format.
    # The purpose of this is to allow the parser to accept tileline objects in tileline or raw string format for ease-of-testing
    # Since raw tileline strings contain a count and proportion column, this also checks for and skips those if they are present
    def run(self, tile_line):
        VectorSubParser._end_state = ''
        VectorSubParser._repeat_counter = 0

        data = tile_line.split() if type(tile_line) is str else tile_line.get_condensed()
        formatted_data = ''
        for i, tile in enumerate(data):
            if 'Payload' in tile:
                formatted_data += 'Payload '
            elif 'ITR-FLIP' in tile:
                formatted_data += 'ITR-FLIP '
            elif 'empty' in tile:
                formatted_data += ''
            else: 
                if i > 1 or not str.isdigit(tile): # set the end state to other and exit if anything unexpected is in the input
                    tile_line.category = 'other'
                    return
        self.parser.parse(formatted_data.strip())  # !!this line does the actual parsing
        # if the category is other, try flipping it (to catch missing ITR on right end) (ex: ITR Payload Payload ITR Payload Payload)
        if self._end_state == 'other':
            self.parser.parse(' '.join(formatted_data.strip().split()[::-1]))  # !!this line does the actual parsing on the reverse of the tile pattern
        # do checks on patterns outside of the grammar's scope: full payloads in expecteds and reverse complementary adjacent payloads in snapbacks
        # then finally add the final classification from end_state to the tileline object as its category field along with the repeat_count for differentiation of recursive patterns
        if type(tile_line) is not str:  # if not a test
            self.check_snapback(tile_line)
            self.check_expected(tile_line)
            tile_line.category = self.get_end_state()
            tile_line.repeat_count = self.get_repeat_count()

    def p_end(self, p):
        '''S : payload_only
             | itr_only
             | truncated_right
             | truncated_left
             | doubled_payload
             | expected
             | truncated_sp_IPP
             | truncated_selfprime
             | truncated_sp_PPI
             | snapback
             | extended
             | expected_selfprime
             | truncated_snapback_selfprime
             | snapback_selfprime
             | other'''
        self._end_state = p[1]
    
    def p_other(self, p):
        '''other : error
                 |'''
        p[0] = 'other'
    
    def p_payload_only(self, p):
        'payload_only : P'
        p[0] = 'payload_only'
    
    def p_itr_only(self, p):
        'itr_only : I'
        p[0] = 'itr_only'
        
    def p_doubled_payload(self, p):
        'doubled_payload : P AND P'
        p[0] = 'doubled_payload'
    
    def p_truncated_right(self, p):
        'truncated_right : I AND P'
        p[0] = 'truncated_right'
    
    def p_truncated_left(self, p):
        'truncated_left : P AND I'
        p[0] = 'truncated_left'
        
    def p_truncated_sp_PPI(self, p):
        'truncated_sp_PPI : P AND P AND I'
        p[0] = 'truncated_sp_PPI'
    
    def p_truncated_sp_IPP(self, p):
        'truncated_sp_IPP : I AND P AND P'
        p[0] = 'truncated_sp_IPP'
    
    def p_expected(self, p):
        'expected : I AND truncated_left'
        p[0] = 'expected'
        
    def p_truncated_selfprime(self, p):
        '''truncated_selfprime : truncated_left AND P'''
        p[0] = 'truncated_selfprime'

    def p_extended(self, p):
        '''extended : truncated_sp_PIPI
                         | I AND truncated_selfprime
                         | truncated_left AND truncated_selfprime
                         | truncated_left AND extended'''
        if p[1] != 'truncated_sp_PIPI':
            VectorSubParser._repeat_counter += 1
        p[0] = 'extended'
    
    def p_truncated_sp_PIPI(self, p):
        '''truncated_sp_PIPI : truncated_left AND truncated_left
                             | truncated_left AND truncated_sp_PIPI'''
        VectorSubParser._repeat_counter += 1
        p[0] = 'truncated_sp_PIPI'

    def p_snapback(self, p):
        'snapback : I AND truncated_sp_PPI'
        p[0] = 'snapback'

    def p_expected_selfprime(self, p):
        'expected_selfprime : I AND truncated_sp_PIPI'
        p[0] = 'expected_selfprime'

    def p_truncated_snapback_selfprime(self, p):
        '''truncated_snapback_selfprime : truncated_sp_PPI AND truncated_sp_PPI
                                        | truncated_sp_PPI AND truncated_snapback_selfprime'''
        VectorSubParser._repeat_counter += 1
        p[0] = 'truncated_snapback_selfprime'

    def p_snapback_selfprime(self, p):
        'snapback_selfprime : I AND truncated_snapback_selfprime'
        p[0] = 'snapback_selfprime'

    # Anything passed in that doesn't fit the grammar will be defined as 'other' instead of raising an error by restarting and parsing an empty string
    def p_error(self, _):
        self.parser.restart()
        self.parser.parse('')
    
    # This getter ensures that a previous end_state isn't carried over to a new data input
    def get_end_state(self):
        if not self._end_state:
            raise ValueError('the end_state was empty when it was supposed to have a value')
                # check orientation for snapback categorizations
        return self._end_state
    
    # This getter ensures that a previous end_state isn't carried over to a new data input
    def get_repeat_count(self):
        if VectorSubParser._repeat_counter < 0:
            raise ValueError('the repeat count was -1 when it was retrieved')
        temp = VectorSubParser._repeat_counter
        VectorSubParser._repeat_counter = -1
        return temp

    # helper for run()
    # checks all tilelines with categories within the snapback_species or truncated_snapback_species list, 
    # any such tileline that has adjacent payloads that are NOT opposite orientations has its category changed.
    # If it is within the snapback_species list, its category is changed to "irregular_payload".
    # If it is within the truncated_snapback_species list, its category is changed to "other".
    def check_snapback(self, tile_line):
        if self._end_state not in SNAPBACK_SPECIES and self._end_state not in TRUNCATED_SNAPBACK_SPECIES:
            return
        tile_pattern = tile_line.condensed_pattern
        is_snapbacks = []
        for i in range(len(tile_pattern) - 1):
            if tile_pattern[i].name == 'Payload' and tile_pattern[i + 1].name  == 'Payload':
                if tile_pattern[i].orientation == tile_pattern[i + 1].orientation:
                    is_snapbacks.append(False)
                else:
                    is_snapbacks.append(True)
        if all(is_snapbacks) is True:
            return
        else:
            tile_line.snapback_pattern_with_same_strand_payloads = True
            if self._end_state == 'snapback':
                self._end_state = 'irregular_payload'
            elif self._end_state in TRUNCATED_SNAPBACK_SPECIES:
                self._end_state = 'other'
            elif not any(is_snapbacks) and self._end_state == 'snapback_selfprime':
                self._end_state = 'irregular_payload'
            elif False in is_snapbacks and True in is_snapbacks and self._end_state == 'snapback_selfprime':
                self._end_state = 'other'
                
    # helper for run()
    # checks all tilelines with categories within the expected category for partial payloads.
    # If one is detected, its category is changed to "irregular payload" 
    # Function can be skipped via command line arg
    def check_expected(self, tile_line):
        if self._end_state not in EXPECTED_SPECIES or not VectorSubParser.expected_species_have_only_full_payloads:
            return
        for tile in tile_line:
            if tile.is_full == False:
                self._end_state = 'irregular_payload'
                return


if __name__ == '__main__':  # use this block for debugging the vector subparsing module
    sample = 'Payload ITR-FLIP'
    my_parser = VectorSubParser(VectorLexer())
    my_parser.run(sample)
    print(my_parser.get_end_state())
    print(my_parser.get_repeat_count())
 
