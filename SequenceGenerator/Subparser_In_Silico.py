from sequence_classes import *
import datetime
from multiprocessing import Pool
import time


SEQS_PER_FILE = 10000
INPUT_FILE = 'Inputs/SubparserTable.csv'
OUTPUT_DIR = '../DataFiles/Inputs/InSilicoData/raw/'
MUTATION_RATES = [0.00, 0.001, 0.01, 0.05]
ZMW_ODDS = 0.1
# Incidence rates are from: Inputs/incidence_rates.csv
HOMOPOLYMER_INDEL_INCIDENCE_RATES = {2: 0.00817473470667043, 3: 0.0230712773929415, 4: 0.0430894309673073, 5: 0.0673036084969494, 6: 0.095277307484608, 7: 0.139147756346614, 8: 0.230958686426305, 9: 0.329346243465396, 10: 0.329346243465396, 11: 0.273727450937204, 12: 0.300797778561354, 13: 0.300797778561354, 14: 0.626876002631374, 15: 0.626876002631374, 16: 0.626876002631374, }
HOMOPOLYMER_DIST_FILE = 'Inputs/homopolymer_type_freqs.csv'
SNAPBACK_FREQ_FILE = 'Inputs/snapback_freqs_normalized.csv'
# The payload from the AAV sequence to generate, from file Inputs/InSilicoAAV.fasta
REF_PAYLOAD_SIZE = 2865


# methods guide:
"""
default: modify_sequence(plasmid.function, rate, start, end)
mutation: modify_sequence(plasmid.mutate_sequence, rate (whole sequence), start, end, subs_only (bool), mutaton_rate (base by base))
create_hairpin: default(..., flip)
insert_sequence: modify_sequence(plasmid.insert_sequence, rate, start, sequence_to_insert)
"""


# NOTE: The repeats do NOT include 0. So a doing 'repeatable' on pattern LPR will NOT include LPR
# NOTE: The repeats in repeat_itr DO include 0. This contradiction is so that it is easier to make a file of all 
    # expected and a file of all expected_selfprime without any crossovers
# NOTE: The repeat indices are set like python indices, so the first one is inclusive and second one is exclusive
# methods guide:
"""
default: modify_sequence(plasmid.function, rate, start, end)
mutation: modify_sequence(plasmid.mutate_sequence, rate (whole sequence), start, end, subs_only (bool), mutaton_rate (base by base))
create_hairpin: default(..., flip)
insert_sequence: modify_sequence(plasmid.insert_sequence, rate, start, sequence_to_insert)
"""


# NOTE: The repeats do NOT include 0. So a doing 'repeatable' on pattern LPR will NOT include LPR
# NOTE: The repeats in repeat_itr DO include 0. This contradiction is so that it is easier to make a file of all 
    # expected and a file of all expected_selfprime without any crossovers
# NOTE: The repeat indices are set like python indices, so the first one is inclusive and second one is exclusive


def type_cast_parameters_vector(csv_row):
    return [int(item) if str.isdigit(item) else item for item in csv_row]

# take normalized snapback frequency data, scale all sizes to the reference payload size, keep for use in sequence_classes as a list of tuples:
# [('payload_1_start payload_1_end payload_2_start payload_2_end', frequency), ('payload_1_start payload_1_end payload_2_start payload_2_end', frequency), ...]
def get_snapback_freq_dist(snapback_data_file):
	snapback_frequency_data = []
	with open(snapback_data_file, 'r') as f:
		for line in f:
			line = line.strip()
			if not line:
				continue
			halves = line.split(':')
			rescaled_sized_from_normalized = [str(min(REF_PAYLOAD_SIZE, round(REF_PAYLOAD_SIZE * float(x)))) for x in halves[0].split()]
			snapback_frequency_data.append((' '.join(rescaled_sized_from_normalized), float(halves[1])))
	return snapback_frequency_data


def generate_zmw_mismatch(vector, mismatch_pattern=False):
    new_vector_name = vector.name + '/rev'
    vector.name += '/fwd'
    if mismatch_pattern:  # generates a 'U' pattern (different patterns, different sequences) by reverse complementing all attributes and removing their 1st base
        new_attributes = vector.attributes
        for att, sequence in new_attributes.items():
            new_attributes[att] = str(Seq(sequence).reverse_complement())
            if len(new_attributes[att]) >= 2:
                new_attributes[att] = new_attributes[att][1:]
        return Vector(new_vector_name, new_attributes, vector.pattern)
    else:  # generates a 'x 2' pattern by inserting a random 1-9bp sequence between (or outside) tileable attributes (as a new attribute)
        # copy the old vector's data
        new_pattern = list(vector.pattern)
        new_attributes = vector.attributes
        # add the new insert sequence to the vector's attributes, insert it's key randomly into its pattern
        insert_key : chr = Vector.get_new_pattern_key(vector.pattern)
        new_attributes[insert_key] = Sequence.generate_random_sequence(random.randint(1, 10))  # new attribute is a random sequence from 1-9bps
        new_pattern.insert(random.choice(len(new_pattern) + 1), insert_key)
        return Vector(new_vector_name, new_attributes, ''.join(new_pattern))


def write_file_vector(csv_row, mutation_rate=0, zmw_mismatch_odds=0.1, output_directory=OUTPUT_DIR, seqs_per_file=SEQS_PER_FILE,  homopolymer_indel_rates=HOMOPOLYMER_INDEL_INCIDENCE_RATES, homopolymer_indel_size_dist_table=HOMOPOLYMER_DIST_FILE):
    output_filename = os.path.join(output_directory, csv_row[0].replace(' ', '_') + f'_m_{str(mutation_rate).split(".")[1]}.fasta')
    with open(output_filename, 'w') as fh:
        for i in range(seqs_per_file):
            formatted_time = datetime.datetime.now().strftime("%y%m%d")
            sequence_name = f'{csv_row[0]}_{formatted_time}_{i}/{i}/ccs'
            vectors = [Vector(sequence_name, Vector.attributes_from_file(csv_row[1]), csv_row[2], *csv_row[3:])]
            # randomly decide whether or not to write a zmw mismatch with a rate of <zmw_mismatch_odds>
            if random.binomial(1, zmw_mismatch_odds):
                vectors.append(generate_zmw_mismatch(vectors[0], random.choice([False, True])))
            for vector in vectors:
                if homopolymer_indel_rates:
                    vector.generate_homopolymer_mutations(homopolymer_indel_rates, Sequence.generate_size_distribution_dictionary(homopolymer_indel_size_dist_table))
                if mutation_rate:
                    vector.modify_sequence(vector.mutate_sequence, 1.0, False, mutation_rate)
                print(f'printing {vector.name} with pattern {vector.pattern} and mutation rate {mutation_rate} to {output_filename}')
                vector.write_seq_to_fasta(fh)

# multiprocess initializer to avoid needing to rerun SnapbackAnalysis for each file
# sets the size frequency as a class variable with the cumulative distribution
def set_snapback_frequencies(snapback_frequencies):
    # frequency to cumulative probability distribution: [0.3, 0.3, 0.1, 0.2] -> [0.3, 0.6, 0.7, 1.0]
    snapback_sizes = [val[0] for val in snapback_frequencies]
    snapback_probabilities = [val[1] for val in snapback_frequencies]
    cumulative_probabilities = [sum(snapback_probabilities[:i+1]) for i in range(len(snapback_probabilities))]
    Vector.snapback_frequencies = list(zip(snapback_sizes, cumulative_probabilities))

if __name__ == '__main__':
    # MULTI-PROCESS
    start_time = time.time()
    random.seed(1997)
    snapback_frequencies = get_snapback_freq_dist(SNAPBACK_FREQ_FILE)
    with open(INPUT_FILE, 'r', encoding='utf-8-sig') as table_file:
        table = table_file.readlines()
    all_lines = []
    for line in table:
        line = line.strip().split(',')
        line = type_cast_parameters_vector(line)
        for m in MUTATION_RATES:
            all_lines.append([line, m, ZMW_ODDS])
    with Pool(17, initializer=set_snapback_frequencies, initargs=[snapback_frequencies]) as pool:
        pool.starmap(write_file_vector, all_lines)
    print(f'run time: {time.time() - start_time} seconds')
