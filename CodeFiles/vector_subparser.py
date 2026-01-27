import ply.lex as lex
import ply.yacc as yacc
from tile_classes import *

EXPECTED_SPECIES = ['expected', 'expected_selfprime']
SNAPBACK_SPECIES = ['snapback', 'snapback_selfprime']
TRUNCATED_SNAPBACK_SPECIES = ['truncated_sp_IPP', 'truncated_sp_PPI', 'truncated_snapback_selfprime']


class VectorLexer:
    def __init__(self):
        self.lexer = lex.lex(module=self)
        self.irregular_itrs = False
    
    # return flag, reset it to false before since same lexer object used for all parsing
    def get_irreg_itr_flag(self):
        flag = self.irregular_itrs
        self.irregular_itrs = False
        return flag

    tokens = (
        'P',
        'AND',
        'I',
    # These tokens are for RepCap Variants
        'repcap_no_rAAV',
        'repcap_with_payload',
        'repcap_with_itr',
        'itr_flanked_repcap'
    )

    t_P = r'(Payload)\S*'
    t_AND = r'\s'
    
    # This token function is an example of how to classify tile patterns before parsing for noncanonical classifications. The same could be replicated for any tile such as Backbone, Helper, etc.
    # By doing this, more classifications can be added without conflicting with the canonical grammar or requiring combinatorial explosion of grammar rules
    # each token maps to a terminal token that goes right to the end state in the parser. 
    # IMPORTANT: For classifications meant to essentially override the CFG, the lex function needs to be over the others as that is how PLY determines lex function priority
    # For example, putting the t_I function above this one would result in itr_flanked_repcap never occurring as ITRs are tokenized already.
    def t_RepCap(self, t):
        r'.*(RepCap).*'
        tilenames = [tile.split('[')[0] for tile in t.value.split()]
        if 'ITR-FLIP' not in tilenames and 'Payload' not in tilenames:
            t.type = 'repcap_no_rAAV'
            t.value = 'repcap_no_rAAV'
        elif 'ITR-FLIP' not in tilenames:
            t.type = 'repcap_with_payload'
            t.value = 'repcap_with_payload'
        else:
            for i, tilename in enumerate(tilenames):
                if tilename == 'RepCap' and 'ITR-FLIP' in tilenames[0:i] and 'ITR-FLIP' in tilenames[i:]:
                    t.type = 'itr_flanked_repcap'
                    t.value = 'itr_flanked_repcap'
                    break
            else:
                t.type = 'repcap_with_itr'
                t.value = 'repcap_with_itr'
        return t
    
    # combine adjacent ITR tiles into one I token, raise irregular_itrs flag
    def t_I(self, t):
        r'(ITR-FLIP\S*)(\s+ITR-FLIP\S*)*'
        if len(t.value.split()) > 1:
            self.irregular_itrs = True
        return t
    
    # leading and trailing numbers are skipped and ignored so that tiling data can be fed into the lexer without needing to remove counts and proportions
    def t_digit(self, t):
        r'^([\d\.]+\s)+|(\s[\d\.]+)+$'
        t.lexer.skip(0)

    # unknown tiles are tokenized as UNKNOWN_TILE, which leads to a parser error and subsequent classification of the tile pattern as 'other'
    def t_error(self, t):
        t.value = t.value.split()[0] # t.value is the rest of the string to be lexed on error
        t.type = 'UNKNOWN_TILE'
        t.lexer.skip(len(t.value)+1)
        return t

    # returns a list of dictionaries for testing, one dictionary for each token read
    def test(self, data):
        self.lexer.input(data)
        test_list = list()
        for tok in self.lexer:
            test_list.append({'type': tok.type, 'value': tok.value, 'lineno': tok.lineno, 'lexpos': tok.lexpos})
        return test_list
    
    # simplifies output of test() to only tokens used to output tokenized versions of tile patterns to the output data file. 
    def tokenize(self, data):
        output_detailed = self.test(data)
        return ' '.join([lex_dictionary['type'] for lex_dictionary in output_detailed]) # if lex_dictionary['type'] != 'AND'])
        


class VectorSubParser:
    precedence = (('right', 'AND'),)
    expected_species_have_only_full_payloads = True

    _end_state = ''
    _repeat_counter = -1

	# initialize the parser with arguments. The lexer is also instantiated
    def __init__(self, lexer, require_full_payloads_in_expected=True, debug=False, parse_homopolymers=False):
        self.tokens = lexer.tokens
        self.lexer = lexer
        # doesn't write the parsetab.py file since the table is small, negligible time is added
        self.parser = yacc.yacc(module=self, debug=debug, write_tables=False)
        VectorSubParser.expected_species_have_only_full_payloads = require_full_payloads_in_expected
        # whether or not to ignore homopolymer tiles, needs to be here instead of in lexer to avoid problems with hompolymer tiles between itr tiles
        self.parse_homopolymers = parse_homopolymers
        # whether or not to print debug output for parsing
        self.debug = debug
        
    # The main function of the subparser
    def run(self, tile_line):
        # initializing data that is separate for each subparser run 
        VectorSubParser._end_state = ''
        VectorSubParser._repeat_counter = 0
        formatted_data = tile_line if type(tile_line) is str else tile_line.raw_data
        # homopolymer tiles removed here instead of in-lexer to homopolymer tiles within ITR tiles preventing ITR regex, 
        # and also to allow for disabling of ignoring homopolymer tiles via command line arg
        if not self.parse_homopolymers:
            if 'poly' in formatted_data: tile_line.contains_polymer = True
            formatted_data = ' '.join([tile for tile in formatted_data.split() if 'poly' not in tile])
        if self.debug: print(f'data input into parser: |{self.lexer.tokenize(formatted_data)}|')
        # running subparser
        self.parser.parse(formatted_data)  # !! this line does the actual parsing
        # if the category is other, try flipping it (to catch missing ITR on right end) (ex: ITR Payload Payload ITR Payload Payload)
        if self._end_state == 'other':
            if self.debug: print(f'parsing failed for pattern:\n{formatted_data.split()}\nparsing the reverse:\n{self.lexer.tokenize(" ".join(formatted_data.strip().split()[::-1]))}')
            VectorSubParser._repeat_counter = 0
            self.parser.parse(' '.join(formatted_data.strip().split()[::-1]))  # !!this line does the actual parsing on the reverse of the tile pattern
        # do checks on patterns outside of the grammar's scope: full payloads in expecteds and reverse complementary adjacent payloads in snapbacks
        # then finally add the final classification from end_state to the tileline object as its category field along with the repeat_count for differentiation of recursive patterns
        if self.debug: print(f'parsing complete; result: {self._end_state}')
        if self.debug: print(f'repeat counter result: {VectorSubParser._repeat_counter}\n\n')
        if type(tile_line) is not str:  # if not a test
            self.check_snapback(tile_line)
            self.check_expected(tile_line)
            tile_line.category = self.get_end_state()
            tile_line.repeat_count = self.get_repeat_count()
            tile_line.tokenized = self.lexer.tokenize(formatted_data)
            tile_line.irregular_itrs = self.lexer.get_irreg_itr_flag()

    # The seperated lower rules are for noncannonical classifications. They map directly to a token from the lexer and override the normal CFG for cannonical classifications
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
             | other
             
             | repcap_no_rAAV
             | repcap_with_payload
             | repcap_with_itr
             | itr_flanked_repcap'''
        self._end_state = p[1]
        if self.debug: self.parsing_debug_message(p, complete=True)
    
    def p_other(self, p):
        '''other : error
                 |'''
        p[0] = 'other'
    
    def p_payload_only(self, p):
        '''payload_only : P'''
        p[0] = 'payload_only'
        if self.debug: self.parsing_debug_message(p)
    
    def p_itr_only(self, p):
        '''itr_only : I'''
        p[0] = 'itr_only'
        if self.debug: self.parsing_debug_message(p)
        
    def p_doubled_payload(self, p):
        '''doubled_payload : P AND P'''
        p[0] = 'doubled_payload'
        if self.debug: self.parsing_debug_message(p)
    
    def p_truncated_right(self, p):
        '''truncated_right : I AND P'''
        p[0] = 'truncated_right'
        if self.debug: self.parsing_debug_message(p)
    
    def p_truncated_left(self, p):
        '''truncated_left : P AND I'''
        p[0] = 'truncated_left'
        if self.debug: self.parsing_debug_message(p)
        
    def p_truncated_sp_PPI(self, p):
        '''truncated_sp_PPI : P AND P AND I'''
        p[0] = 'truncated_sp_PPI'
        if self.debug: self.parsing_debug_message(p)
    
    def p_truncated_sp_IPP(self, p):
        '''truncated_sp_IPP : I AND P AND P'''
        p[0] = 'truncated_sp_IPP'
        if self.debug: self.parsing_debug_message(p)
    
    def p_expected(self, p):
        '''expected : I AND truncated_left'''
        p[0] = 'expected'
        if self.debug: self.parsing_debug_message(p)
        
    def p_truncated_selfprime(self, p):
        '''truncated_selfprime : truncated_left AND P'''
        p[0] = 'truncated_selfprime'
        if self.debug: self.parsing_debug_message(p)

    def p_extended(self, p):
        '''extended : truncated_sp_PIPI
                    | I AND truncated_selfprime
                    | truncated_left AND truncated_selfprime
                    | truncated_left AND extended'''
        if p[1] != 'truncated_sp_PIPI':
            VectorSubParser._repeat_counter += 1
        p[0] = 'extended'
        if self.debug: self.parsing_debug_message(p)
    
    def p_truncated_sp_PIPI(self, p):
        '''truncated_sp_PIPI : truncated_left AND truncated_left
                             | truncated_sp_PIPI AND truncated_left'''
        VectorSubParser._repeat_counter += 1
        p[0] = 'truncated_sp_PIPI'
        if self.debug: self.parsing_debug_message(p)

    def p_snapback(self, p):
        '''snapback : I AND truncated_sp_PPI'''
        p[0] = 'snapback'
        if self.debug: self.parsing_debug_message(p)

    def p_expected_selfprime(self, p):
        '''expected_selfprime : I AND truncated_sp_PIPI'''
        p[0] = 'expected_selfprime'
        if self.debug: self.parsing_debug_message(p)

    def p_truncated_snapback_selfprime(self, p):
        '''truncated_snapback_selfprime : truncated_sp_PPI AND truncated_sp_PPI
                                        | truncated_sp_PPI AND truncated_snapback_selfprime'''
        VectorSubParser._repeat_counter += 1
        p[0] = 'truncated_snapback_selfprime'
        if self.debug: self.parsing_debug_message(p)

    def p_snapback_selfprime(self, p):
        '''snapback_selfprime : I AND truncated_snapback_selfprime'''
        p[0] = 'snapback_selfprime'
        if self.debug: self.parsing_debug_message(p)
    
    # Anything tile pattern that doesn't fit the grammar will be classified as 'other'
    def p_error(self, p):
        if self.debug: self.parsing_debug_message(p, error=True)
        self.parser.restart()
        self.parser.parse('')
    
    # This getter ensures that a previous end_state isn't carried over to a new data input
    def get_end_state(self):
        if not self._end_state:
            raise ValueError('the end_state was empty when it was supposed to have a value')
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
        is_snapbacks = []
        tile_pattern = tile_line.tile_list
        if not self.parse_homopolymers:
            tile_pattern = [tile for tile in tile_pattern if 'poly' not in tile.name]
        for i, tile in enumerate(tile_pattern):
            if i + 1 < len(tile_pattern) and tile_pattern[i].name == 'Payload' and tile_pattern[i + 1].name  == 'Payload':
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
    
    # message printed from parsing steps when debug is set to true
    def parsing_debug_message(self, p, error=False, complete=False):
        if complete:
            print(f'END_STATE <- {p[1:]} repeats: {self._repeat_counter}')
        elif error:
            print(f'error while parsing {p}, setting result to other')
        else:
            p = list(p)
            for i, item in enumerate(p):
                if item == ' ': p[i] = 'AND'
            print(f'{p[0]} <- {p[1:]} repeats: {self._repeat_counter}')

# use this block for debugging the vector subparsing module by setting sample to the desired input
# accepts a list of tile names, a raw tile pattern string or a list of tileline objects
if __name__ == '__main__':
    sample = '108 1 Payload[1-10](t) ITR-FLIP[100-1000](t) Payload[1-10](f)'
    # # Testing the lexer
    my_lex = VectorLexer()
    print(f'testing lexer on input:\n{sample}')
    print(f'lexing result: |{my_lex.tokenize(sample)}|')
    
    # Testing the Parser
    my_parser = VectorSubParser(VectorLexer(), debug=True)
    my_parser.run(sample)

