from vector_subparser import *
from tile_classes import *
import argparse
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


VG_TILES = ['Payload', 'ITR-FLIP', 'poly'] # tiles considered cannonical
NONCANON_ANALYSIS = False # whether or not to do subparsing on noncannonical tiles, i.e. tiles with names not in the VG_TILES list


class FileParser:
    # processes the file, and stores the resulting data as a single list of all the tilelines objects.
    # These are stored as a list so that the categories can be modified using the modify_categories function prior to 
    # storing the TileLine objects into Bin objects, which are made with names based on those categories
    def __init__(self, input_file, require_full_payloads_in_expected=True, raise_error_on_low_fulls=False, debug=False, parse_homopolymers=False):
        self.parser = VectorSubParser(VectorLexer(), require_full_payloads_in_expected=require_full_payloads_in_expected, debug=debug, parse_homopolymers=parse_homopolymers)
        self.bins_list = list()
        self.unbinned_tilelines = list()
        self.raise_error_on_low_fulls = raise_error_on_low_fulls
        if not os.path.isfile(input_file): 
            return
        with open(input_file, 'r') as f:
            while True:
                tile_line = f.readline()

                if not tile_line.strip(): tile_line = f.readline()  # skip blank lines
                if not tile_line: break  # EOF

                if ' U ' in tile_line and ' x 2' in tile_line:
                    raise ValueError(f'a tile line ({tile_line}) had an x_2 and U, this should not happen. Recheck tiling.')
                elif ' U ' in tile_line:
                    [self.unbinned_tilelines.append(line) for line in self.process_U_line(tile_line) if line is not None]
                elif ' x 2' in tile_line:
                    self.unbinned_tilelines.append(self.process_x_2_line(tile_line))
                else:
                    self.unbinned_tilelines.append(self.process_line(tile_line))
                
                # remove the added tileline if it was None
                if len(self.unbinned_tilelines) > 0 and self.unbinned_tilelines[len(self.unbinned_tilelines)-1] is None:
                    del self.unbinned_tilelines[len(self.unbinned_tilelines)-1]
        # raise error if no AAV genome-only tilelines were found in the input file
        if len(self.unbinned_tilelines) == 0:
            raise ValueError(f'no valid vector tile patterns were found in {input_file}; make sure that it is a valid vector counts file\n non-vector counts files (plasmid, etc.) will raise this error')
    
    # formats U lines to be run as two seperate normal lines by the process_line function
    def process_U_line(self, data):
        split_data = data.split(' U ')
        U_left = split_data[0].split()
        U_right = split_data[1].split()
        split_count = str(float(U_left[0]) / 2)
        U_left[0] = split_count  # replace original count with split count for left
        U_right.insert(0, split_count)  # insert split count to right
        U_right.insert(1, '0')
        return [self.process_line(' '.join(U_left)), 
                self.process_line(' '.join(U_right))]

    # formats x 2 lines to be run by the process_line function
    def process_x_2_line(self, data):
        i = data.find(' x 2')
        return self.process_line(data[:i])

    # generates a Tileline object for each line, and categorizes it using a VectorSubParser object
    def process_line(self, line):
        tile_line = TileLine(line)
        # if noncanonnical analysis is disabled skip lines that have any tile that isn't cannonical 
        if not NONCANON_ANALYSIS and any([tile.name.split('_')[0] not in VG_TILES and 'poly' not in tile.name for tile in tile_line]):
                return
        self.parser.run(tile_line)  # !! This is where the vector_subparser module is run
        return tile_line

    def group_categories(self, modification_dictionary):
        if len(self.unbinned_tilelines) == 0:
            raise ValueError('modify_categories must be called before bin_tilelines, otherwise tilelines are already binned')
        for tileline in self.unbinned_tilelines:
            if tileline.category in modification_dictionary.keys():
                tileline.category = modification_dictionary[tileline.category]
            else:  # categories outside of grouping set placed in other
                tileline.category = 'other'
            

    def bin_tilelines(self):
        for i in range(len(self.unbinned_tilelines)-1, -1, -1): # item removal during iteration requires backwards iteration
            for bin in self.bins_list:
                if self.unbinned_tilelines[i].category == bin.name:
                    bin.add_tileline(self.unbinned_tilelines.pop(i))
                    break
            else:
                self.bins_list.append(TileLineBin(self.unbinned_tilelines.pop(i)))
        self.sort()
        self.calculate_bin_proportions()

    def calculate_bin_proportions(self):
        count_sum = sum([bin.sequence_count for bin in self.bins_list])
        for bin in self.bins_list:
            bin.sort()
            bin.calculate_tileline_proportions()
            bin.calculate_full_payload_proportions()
            bin.proportion = bin.sequence_count/count_sum
        if self.raise_error_on_low_fulls:
            self.check_for_low_fulls()

    def sort(self): 
        self.bins_list.sort(key=lambda x: x.sequence_count, reverse=True)

    def check_for_low_fulls(self):
        full_categories = ['full', 'expected_selfprime', 'expected']
        all_fulls_proportion = 0
        for bin in self.bins_list:
            if bin.name in full_categories:
                all_fulls_proportion += bin.proportion
        if all_fulls_proportion < 0.5:
            raise ValueError('\n The amount of full sequences (within the full bin by default; within expected_selfprime and expected bins with "-m all") is below 50%. \
                              \n Double-check that the expected payload size is correct, or silence this error by running this command with the "-silence_raise_error_on_low_fulls" flag')

    def write_to_file(self, output_file):
        with open(output_file, 'w') as f:
            f.write(str(self))

    def __str__(self):
        r_string = ''
        # write summary data, similar to the format of Serena's Vector_Subclassification script
        r_string += 'Bin\tSequences\tProportion\tPatterns\tPercent Full\n'
        for bin in self.bins_list:
            r_string += f'{bin.name}\t{bin.sequence_count}\t{bin.proportion}\t{bin.pattern_count}\t{bin.full_proportion * 100}%\n'
        # write totals
        r_string += f'Totals\t{sum([bin.sequence_count for bin in self.bins_list])}\t{sum([bin.proportion for bin in self.bins_list])}\t{sum([bin.pattern_count for bin in self.bins_list])}\n\n\n'
        # write data content
        r_string += '\n\n\n'.join([str(bin) for bin in self.bins_list])
        return r_string
    
    def write_bin(self, output_file, bin_to_write):
        with open(output_file, 'w') as f:
            for line in bin_to_write.tile_line_list:
                f.write(f'{line.raw_data}\n')


def GetArguments():
    parser = argparse.ArgumentParser(prog='VectorSubparser',
                                    description='Code to group SMRT NGS AAV data from *.tile.counts file(s)',
                                    epilog='contact d.rouleau@oxb.com for more help')
    # Required Arguments
    parser.add_argument('-input_file', required=True, type=str,
                        help='the tile.counts file(s) to be run. These are run individually since the expected payload sizes often vary from file to file')
    parser.add_argument('-output_directory', required=True, type=str,
                        help='the directory to place the output files in')
    parser.add_argument('-payload_size', required=True, type=int,
                        help='the expected size of the payload in the run')
    # Optional Arguments
    parser.add_argument('-group_categories', choices=['five', 'six', 'two'], default=None,
                        help='''Optionally group the vector subparser's 17 initial categories.
                        \n The three options are five, six, and two groups. To use five or six groups, use "five" or "six" respectively following this flag.
                        \n The five groupings are:
                        \n expected, expected_selfprime -> full |
                        \n itr_only, payload_only, truncated_right, truncated_left, truncated_selfprime -> truncated |
                        \n snapback, snapback_selfprime -> snapback |
                        \n truncated_sp_IPP, truncated_sp_PPI, truncated_snapback_selfprime -> truncated_snapback |
                        \n other, truncated_sp_PIPI, truncated_sp_IPIP, irregular_payload, doubled_payload -> other |
                        \n six groups is the same, but expected and expected_selfprime are not grouped |
                        \n To output only two categories, one which contains cannonical VGs and the other containing everything else, follow this flag with "two"
                        ''')
    parser.add_argument('-bin_to_counts_files', default=True, action='store_false',
                        help='these are all output by default. If this flag is raised, no counts files will be generated\n \
                        Using the "modification_dictionary argument will change bin names, so the output here is changed by the -group_categories flag option\n \
                        IMPORTANT: the proportions displayed in the output file for each tile pattern are taken directly from the input file, they are NOT \
                        the recalculated proportions displayed in the *.subparsed.tsv file')
    parser.add_argument('-dont_require_full_payloads', default=True, action='store_false',
                        help='flag to determine whether or not only tile patterns with payloads size +/- the coordinate buffer\n \
                        should be included in the expected and expected self priming sub bins (the full bin using default categories) \
                        The default value is True (full payloads ARE required in the full (expected and expected_selfprime) categories')
    parser.add_argument('-coordinate_buffer', type=int, default=6,
                        help='modify the range coordinates must be relative to the expected payload size when considered as "full". The default is 6')
    parser.add_argument('-raise_error_on_low_fulls', default=False, action='store_true',
                        help='use this flag to raise an error when the proportion of sequences within full species\n bins (full, or expected and expected_selfprime depending on output categories option) is below 0.5')
    parser.add_argument('-untileable_sequences', default=False, action='store_true',
                         help='if this flag is raised, then untileable sequences will be included in the output calculations and graphs. \
                            the count of untileable sequences will be sourced from the summary file with the same root filename.')
    parser.add_argument('-noncannonical_analysis', default=False, action='store_true',
                         help='if this flag is raised, noncanonical tiles will be considered by the subparser. This is to enable extending of the subparser grammar. As of now, all tile patterns with tiles outside of polyX, ITR or Payload will be classified as other')
    parser.add_argument('-debug', default=False, action='store_true',
                         help='if this flag is raised, detailed debug information will be printed to stdout by the vector_subparser module. Additionally, a parser.out file giving CFG information will be placed in the directory of the vector_subparser.py file')
    parser.add_argument('--parse_homopolymers', default=False, action='store_true',
                         help='if this flag is raised, homopolymer tiles will NOT be ignored completely by the subparser. The default is to ignore them')
    return parser


# group initial set of TileLine categories from the subparser into an equal or lesser set of category labels, based on the groups in the category_groups dictionary 
# picked below. The option is set via user arguments, and the default is the five groups resulting from category_group_set == None
def get_category_groups(category_group_set):
    category_groups = dict()
    # five or six category groups, 'five' groups expected and expected_selfprime, 'six' groups does not
    if category_group_set == 'five' or category_group_set == 'six':
        if category_group_set == 'five':
            category_groups.update(dict.fromkeys(['expected', 'expected_selfprime'], 'expected'))
        else:
            category_groups['expected'] = 'expected'
            category_groups['expected_selfprime'] = 'expected_selfprime'
        category_groups.update(dict.fromkeys(['itr_only', 'payload_only', 'truncated_right', 'truncated_left', 'truncated_selfprime'], 'truncated'))
        category_groups.update(dict.fromkeys(['snapback', 'snapback_selfprime'], 'snapback'))
        category_groups.update(dict.fromkeys(['truncated_sp_IPP', 'truncated_sp_PPI', 'truncated_snapback_selfprime'], 'truncated_snapback'))
        category_groups.update(dict.fromkeys(['other', 'extended', 'irregular_payload', 'untileable_sequences', 'doubled_payload'], 'other'))
    # two category groups
    elif category_group_set == 'two':
        category_groups.update(dict.fromkeys(['expected', 'expected_selfprime'], 'expected'))
        category_groups.update(dict.fromkeys(['itr_only', 'payload_only', 'truncated_right', 'truncated_left', 
                                            'truncated_selfprime', 'snapback', 'snapback_selfprime', 
                                            'doubled_payload', 'truncated_sp_IPP', 'truncated_sp_PPI', 'truncated_snapback_selfprime',
                                            'other', 'extended', 'irregular_payload', 'untileable_sequences'], 'other'))
    return category_groups


def add_untileable_sequence_bin(file_parser_obj, input_file):
    # getting summary file
    file_directory = os.path.dirname(input_file)
    for file in os.listdir(file_directory):
        if os.path.basename(input_file).split('.')[0] == file.split('.')[0] and '.summary' in file:
            summary_file = os.path.join(file_directory, file)
            break
    else:
        print(f'Warning: no summary file found for {input_file}; running without adding untileable sequences to counts')
        return
    # getting untileable sequence count from summary file
    with open(summary_file, 'r') as f:
        for line in f:
            if 'Unaccounted sequences number' in line:
                untileable_sequences = float(line.split()[3])
                break
        else:
            print(f'something went wrong when trying to get the untileable sequence count from {summary_file}; running without adding untileable sequences to counts')
            return
    if untileable_sequences == 0:
        print(f'{summary_file} had an untileable sequence count of 0, no untileable sequence bin will be added')
        return
    # adding empty bin to include untileable sequence count to file_parser object
    untileable_sequence_tileline = TileLine(f'{untileable_sequences} 0')
    untileable_sequence_tileline.category = 'untileable_sequences'
    file_parser_obj.unbinned_tilelines.append(untileable_sequence_tileline)


def GraphWriter(output_file):
    # getting values from tsv
    labels, seq_count, seq_proportion, prop_labels = [], [], [], []
    with open(output_file, 'r') as o:
        for line in o:
            line = line.split()
            if line[0] == 'Bin':
                continue
            elif line[0] == 'Totals':
                break
            else:
                labels.append(line[0])
                seq_count.append(float(line[1]))
                seq_proportion.append(float(line[2]))
                prop_labels.append(f'{line[0]}: {round(float(line[2]) * 100, 2)}%')
    graph_data = {"Category": labels, "Count": seq_count, "Proportion": seq_proportion, "Labels": prop_labels}
    graph_frame = pd.DataFrame(graph_data)

    # using output values to create a bar graph and pie chart; making colors constant to categorical label values
    colors = {"expected": "#32d92c", "expected_selfprime": "#1aa72d",
              "truncated_left": "#eacc16", "truncated_right": "#ab950d", "payload_only": "#dbe857", "itr_only": "#a4ad48", "truncated_selfprime": "#e4cc5b", 
              "doubled_payload": "#e3952b", "truncated_sp_IPP": "#d9ac1d", "truncated_sp_PPI": "#d9ac1d", "truncated_snapback_selfprime": "#a48427",
              "snapback": "#e76a22", "snapback_selfprime": "#9b4b1d",
              "other": "#e44529", "extended": "#ab3621", "irregular_payload": "#da6e5b", 

              "full": "#32d92d", "truncated": "#d9c72c", "truncated_snapback": "#d9682c",

              "untileable_sequences": "#f42a06",
    }
    
    pal = [colors[label] if label in colors.keys() else '#000000' for label in labels ]  # unknown categories will be black
    
    sns.set_style("darkgrid", {"axes.facecolor": "0.8"})
    sns.set_palette(pal, 9)

    fig, axs = plt.subplots(figsize=(14.5, 5), nrows=1, ncols=2)
    fig.suptitle(os.path.basename(output_file).split('.')[0], x=0.55)
    axs[0].set_title("Sequence Counts", fontsize=13)
    plot = sns.barplot(ax=axs[0], data=graph_frame, x='Count', y='Category', hue='Category', palette=pal, legend=False)
    for p in plot.patches:
        width = int(p.get_width())
        axs[0].annotate(f'{width:.0f}', (width + plot.patches[0].get_width() * 0.01, p.get_y() + p.get_height() / 2), 
                        ha='left', va='center')

    axs[1].set_title("Sequence Proportions", fontsize=13)
    axs[1].pie(graph_frame['Proportion'], colors=pal)
    axs[1].legend(loc='center right', bbox_to_anchor=(1.6, 0.5), labels=prop_labels, fontsize=10)
    plt.savefig(os.path.splitext(output_file)[0] + '.pdf', dpi=150, bbox_inches='tight')


def main():
	# get user arguments from the command line
    arguments = GetArguments().parse_args()

    # setting argument variables based on user args
    INPUT_FILE = arguments.input_file
    OUTPUT_DIRECTORY = arguments.output_directory
    EXPECTED_PAYLOAD_SIZE = arguments.payload_size
    MOD_DICTIONARY = get_category_groups(arguments.group_categories)
    global NONCANON_ANALYSIS
    NONCANON_ANALYSIS = arguments.noncannonical_analysis

    # setting class variables 
    if arguments.coordinate_buffer < 0: raise ValueError('the coordinate buffer must be greater than 0')
    Tile.coordinate_buffer = arguments.coordinate_buffer
    Tile.expected_payload_size = EXPECTED_PAYLOAD_SIZE

    # checking for valid files and reformatting file names
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f'{INPUT_FILE} does not exist')
    input_file = os.path.basename(INPUT_FILE)
    if '.counts' not in str(input_file):  # only run .counts files
        raise FileNotFoundError(f'the input file {input_file} is not supported. It must be a counts file')
    
    # create output directory if it doesn't already exist
    extensions = -3 if 'zmw' in INPUT_FILE else -2
    output_path = os.path.join(OUTPUT_DIRECTORY, '.'.join(input_file.split('.')[:extensions]))
    if not os.path.exists(output_path):
        os.mkdir(output_path,  mode=0o777)
    output_file = os.path.join(output_path, '.'.join(input_file.split('.')[:extensions])) + '.subparsed.tsv'

    # nearly all of the code is run in this block
    file_parser = FileParser(INPUT_FILE, 
                             require_full_payloads_in_expected=arguments.dont_require_full_payloads, 
                             raise_error_on_low_fulls=arguments.raise_error_on_low_fulls,
                             debug=arguments.debug, 
                             parse_homopolymers = arguments.parse_homopolymers)
    
    # optionally add untileable sequence count as an empty bin
    if arguments.untileable_sequences:
        add_untileable_sequence_bin(file_parser, INPUT_FILE)

	# group categories if that is being done per user arg
    if MOD_DICTIONARY:
        file_parser.group_categories(MOD_DICTIONARY)

	# finalize data by placing all tileline objects with the same category field into separate bin objects then calculate bin-based data and write to file
    TileLine.tokens = file_parser.parser.tokens # makes it so the condensed tilelines written to the output file don't include tokens not in the parser's grammar
    file_parser.bin_tilelines()
    file_parser.write_to_file(output_file)

    # output desired bins to counts file for more analysis ------------------------------------------------------------------- #
    bins_output_path = os.path.join(output_path, 'categories')
    if not os.path.exists(bins_output_path):
        os.mkdir(bins_output_path, mode=0o777)
    if arguments.bin_to_counts_files:
        for bin in file_parser.bins_list:
            file_parser.write_bin(os.path.join(bins_output_path, f'{input_file.split(".")[0]}.{bin.name}.tile.zmw.counts'), bin)

    # graphing
    GraphWriter(output_file)

if __name__ == '__main__':
    main()
