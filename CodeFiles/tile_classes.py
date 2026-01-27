import re
import copy


class Tile:
    coordinate_buffer = 6
    expected_payload_size = 1000
    symbol_usage = False

    def __init__(self, tile_string):
        # getting all ITR data as a list, and sorting out NONE to avoid error
        tile_data = re.split(r'\[|\]|\(|\)', tile_string)
        tile_data = list(filter(None, tile_data))
        # storing data as member variables
        self.name = tile_data[0]
        if '-' in tile_data[1]:
            coordinates = tile_data[1].split('-')
            self.coordinate_start = int(coordinates[0])
            self.coordinate_end = int(coordinates[1])
        else:
            self.coordinate_start = int(tile_data[1])
            self.coordinate_end = None
        self.orientation = Tile.reformat_symbol_orientations(tile_data[2])
        self.set_is_full()
    
    # function to make tile counts files with +/- orientations compatable with the subparser, keeps t/f compatability
    def reformat_symbol_orientations(raw_orientation):
        if raw_orientation == '+':
            Tile.symbol_usage = True
            return 't'
        elif raw_orientation == '-':
            Tile.symbol_usage = True
            return 'f'
        else:
            return raw_orientation

    def compare_tiles(self, other):
        left_full = False
        right_full = False

        if Tile.coordinates_are_equal(self.coordinate_start, other.coordinate_start):
            left_full = True
        if Tile.coordinates_are_equal(self.coordinate_end, other.coordinate_end):
            right_full = True
        
        if left_full and right_full:
            return 'full'
        elif left_full:
            return 'right_partial'
        elif right_full:
            return 'left_partial'
        else:
            return 'both_partial'

    # helper to compare two tile coordinates with respect to the coordinate buffer
    def coordinates_are_equal(first_coordinate, second_coordinate):
        if first_coordinate in range(second_coordinate - Tile.coordinate_buffer,
                                second_coordinate + Tile.coordinate_buffer + 1):
            return True
        else:
            return False
    
    def name_matches(self, other):
        return self.name == other.name
    
    def set_is_full(self):
        # Payload sizing
        self.is_full = True
        if 'Payload' in self.name and \
            (not Tile.coordinates_are_equal(self.coordinate_start, 1) or not Tile.coordinates_are_equal(self.coordinate_end, Tile.expected_payload_size)):
            self.is_full = False

    # equality operation used during testing
    def __eq__(self, other):
        if self.name == other.name \
        and Tile.coordinates_are_equal(self.coordinate_start, other.coordinate_start) \
        and Tile.coordinates_are_equal(self.coordinate_end, other.coordinate_end) \
        and self.orientation == other.orientation:
            return True
        else:
            return False
    
    # compatability for +/- orientations, prints +/- patterns into tiling instead of t/f
    def orientation_to_symbol(orientation_bool):
        if not Tile.symbol_usage:
            return orientation_bool
        if orientation_bool == 't':
            return '+'
        elif orientation_bool == 'f':
            return '-'
    
    def __str__(self):  # returns a string; if-else for single-coordinate tiles (see line 35 below)
        as_string = f'{self.name}[{self.coordinate_start}-{self.coordinate_end}]({Tile.orientation_to_symbol(self.orientation)})' if self.coordinate_end \
               else f'{self.name}[{self.coordinate_start}]({Tile.orientation_to_symbol(self.orientation)})'
        return as_string


# input is a single line from the input file as a string. If the input is a list, the overload emulation takes over
# for IsSelfPriming function creating a TileLine with None values for all variables except the tile_list
# expected_tile_line value default is None for creating the expected plasmid object. 
class TileLine:
    def __init__(self, raw_data):
        self.raw_data = raw_data.strip()
        data = raw_data.split()
        self.count = float(data.pop(0))
        self.proportion = 0
        data.pop(0) # not using the old proportion; it is stored in self.raw_data for writing bin files
        self.tile_list = [Tile(tile) for tile in data]
        self.linear_status = self.set_linearity()
        self.category = None
        self.repeat_count = -1
        self.irregular_itrs = False
        self.contains_polymer = False
        self.snapback_pattern_with_same_strand_payloads = False
        self.contains_full_payload = self.check_full_payload()
        self.tokenized = 'not lexed'
    
    def set_linearity(self):
        linear_status = None
        for t in self:
            if t.name == 'ITR-FLIP':
                continue
            elif linear_status is None:
                linear_status = t.orientation
            elif t.orientation != linear_status:
                return 'non_linear'
        if linear_status == 't':
            return 'forward_linear'
        elif linear_status == 'f':
            return 'reverse_linear'
        else:
            return 'itr_only'
    
    # Determines whether there is any full payload within the tile pattern, returns bool
    def check_full_payload(self):
        for tile in self:
            if 'Payload' in tile.name and tile.is_full:
                return True
        else:
            return False
    
    def __len__(self):
        return len(self.tile_list)

    def __getitem__(self, index):
        return self.tile_list[int(index)]
    
    def __iter__(self):
        return iter(self.tile_list)

    # used in testing
    def __eq__(self, other):
        if len(self) != len(other):
            return False
        for i, self_tile in enumerate(self):
            if self_tile.name != other[i].name or self_tile.coordinate_start != other[i].coordinate_start or self_tile.coordinate_end != other[i].coordinate_end or self_tile.orientation != other[i].orientation:
                return False
        else:
            return True
        
    def __str__(self):
        tile_list_string = ' '.join(str(tile) for tile in self.tile_list)
        r_string = f'{self.category}\t{self.count}\t{self.repeat_count}\t{self.proportion}\t{self.linear_status}\t{self.irregular_itrs}\t{self.contains_polymer}\t{self.contains_full_payload}\t{self.tokenized}\t{tile_list_string}'
        return r_string


class TileLineBin:
    def __init__(self, tileline):
            if tileline.category is None:
                raise ValueError('None category tileline added to a bin, miscellaneous cases should be marked as other')
            self.name = tileline.category
            self.sequence_count = tileline.count
            self.proportion = 0
            self.full_proportion = 0
            # don't add one if the tileline has no tiles (it was from untileable_seqeunces)
            self.pattern_count = 1 if tileline.tile_list else 0
            self.tile_line_list = [tileline]

    # input is a TileLine object; adds tileline to bin and increments sequence and pattern counts
    def add_tileline(self, tileline):
        self.sequence_count += tileline.count
        # don't add one if the tileline has no tiles (it was from untileable_seqeunces)
        self.pattern_count =  self.pattern_count + 1 if tileline.tile_list else self.pattern_count
        self.tile_line_list.append(tileline)

    # sort sequences in bin from highest to lowest sequence count
    def sort(self):
        self.tile_line_list.sort(key=lambda x: x.count, reverse=True)

    # calculate proportions of sequences in bins to avoid rounding errors from *.counts file proportions
    def calculate_tileline_proportions(self):
        for tileline in self:
            tileline.proportion = tileline.count / self.sequence_count
    
    def calculate_full_payload_proportions(self):
        full_tilelines = 0
        for tileline in self:
            if tileline.contains_full_payload:
                full_tilelines += tileline.count
        self.full_proportion = full_tilelines / self.sequence_count
    
    def __getitem__(self, index):
        return self.tile_line_list[int(index)]
    
    # output bin object to string for output file
    def __str__(self):
        printed_proportion = str(round(self.proportion, 5))
        r_string = '\t'.join(['Subclassification', 'Sequences', 'Proportion of Sample', 'Tile Patterns', 'Proportion with a Full Payload']) + '\n'
        r_string += '\t'.join([f'{self.name}',f'{self.sequence_count}',f'{printed_proportion}',f'{self.pattern_count}', f'{self.full_proportion}']) + '\n'
        r_string += '\t'.join(['Subclassification','Sequence Count', 'Repeats', f'Proportion of {self.name}', 'Linearity', 'Contains Irregular ITRs', 'Contains Homopolymer', 'Contains a Full Payload', 'Tokenized', 'Tile Pattern']) + '\n' 
        r_string += '\n'.join([str(tileline) for tileline in self.tile_line_list])
        return r_string
