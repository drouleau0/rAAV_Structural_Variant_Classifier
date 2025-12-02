from Bio import SeqIO
from Bio import Restriction
from Bio.Seq import Seq
from numpy import random
from copy import deepcopy
import string
import os
import csv


BASES_DEL = 'ACGT-'
BASES = 'ACGT'


class Sequence:
    def __init__(self, name, sequence):
        self.name = name
        self.sequence = sequence
    
    def __str__(self):
        return f'{self.name}: {self.sequence}'

    def __len__(self):
        return len(self.sequence)

    def __getitem__(self, index):
        return self.sequence[index]

    def from_file(fasta_file):
        record = SeqIO.read(fasta_file, 'fasta')
        return Sequence(record.id, str(record.seq))

    def modify_sequence(self, function, rate=1.0, *args):
        if type(rate) != float or rate > 1 or rate == 0:
            raise ValueError(f"the first value after the function must ALWAYS be the rate (a float in range [0,1]), it was {type(rate)}")
        if len(args) >= 2 and type(args[0]) == int and type(args[1]) == int and args[0] > args[1]:
            raise ValueError(f'coordinate 1 ({args[0]}) must be less than coordinate 2 ({args[1]}) for {function.__name__}')
        if len(args) == 0 or not any([int == type(c) for c in args][:1]):
            args = (0, len(self.sequence), *args)
        if rate < 1 and not random.binomial(1, rate):
            return
        function(*args)
    
    # inserts sequence after the start coordinate
    def insert_sequence(self, insert_coord, insert_sequence):
        self.sequence = self.sequence[:insert_coord + 1] + insert_sequence + self.sequence[insert_coord + 1:]
    
    def delete_sequence(self, start_coord, end_coord):
        self.sequence = self.sequence[:start_coord] + self.sequence[end_coord:]
    
    # Helper for AddMutations, allows for small InDel mutations
    def pick_random_mutation(base_character):
        new_character = BASES_DEL[random.choice(len(BASES_DEL))]
        if new_character == base_character.upper():
            return base_character.upper() * 2
        elif new_character == '-':
            return ''
        else:
            return new_character

    # Helper for AddMutations, only does substitutions
    def pick_random_substitution(base_character):
        return BASES.replace(base_character.upper(), '')[random.choice(len(BASES) - 1)]
    
    # For a subsequence, based on a binomial distribution, randomly decide whether to mutate each base.
    # To do this, check each base from "start" to "end", and decide whether or not to add it to "new sequence" randomly.
    # If so, mutate according to the subs_only parameter (if true then only substitutions, otherwise indels also)
    # If not, add the character as it was to new_sequence.
    # Insert the result (a mix of old and new characters) into the location between "start" and "end" after deleting the 
    # original sequence that was there
    def mutate_sequence(self, start, end, subs_only, mutation_rate):
        new_sequence = list()
        for character in list(self.sequence[start:end]):
            if random.binomial(1, mutation_rate):
                if subs_only:
                    new_sequence.append(Sequence.pick_random_substitution(character))
                else:
                    new_sequence.append(Sequence.pick_random_mutation(character))
            else:
                new_sequence.append(character)
        new_sequence = ''.join(new_sequence)
        self.delete_sequence(start, end)
        self.insert_sequence(start-1, new_sequence)

    def reverse_complement(self, start, end):
        insert_seq = str(Seq(self.sequence[start:end]).reverse_complement())
        self.delete_sequence(start, end)
        self.insert_sequence(start-1, insert_seq)

    def flip_sequence(self, start, end):
        flipped_sequence = self.sequence[start : end][::-1]
        self.delete_sequence(start, end)
        self.insert_sequence(start-1, flipped_sequence)

    def duplicate_sequence(self, start, end):
        region_to_insert = self.sequence[start : end]
        self.insert_sequence(start-1, region_to_insert)

    def create_hairpin(self, start, end, flip):
        if flip:
            self.reverse_complement(start, end)
        insert_seq = str(Seq(self.sequence[start:end]).reverse_complement())
        self.insert_sequence(end-1, insert_seq)
    
    def write_seq_to_fasta(self, output_file_handle):
        if len(self.sequence) == 0:
            return
        output_file_handle.write(f'>{self.name}\n{self.sequence}\n')
    
    def write_seq_to_fastq(self, output_file_handle):
        # generate a score based on poisson distribution with mean 30 (based on PacBio data)
        if len(self.sequence) == 0:
            return
        scores = []
        for _ in range(len(self.sequence)):
            score = 1000
            while score > 42 or score < 20:
                score = random.poisson(30, 1)[0]
            scores.append(score)
        phred33 = [chr(score + 33) for score in scores]
        quality = (''.join(phred33))
        output_file_handle.write(f'@{self.name}\n{self.sequence}\n+\n{quality}\n')

    # Helper for generate_homopolymer_mutations, uses size distribution as weighted roulette wheel to determine which indel
    # to do, uses a cumulative probability list and rng to simulate weighted probabilities
    # returns the InDel type (Insertion or Deletion) from set [+, -] and size
    def random_indel(size_distribution):
        if round(sum(size_distribution.values()), 3) != 1:
            raise ValueError(f'The sum of probabilities for size distribution {size_distribution} was not nearly 1\n It was: {sum(size_distribution.values())}')

        # probability to cumulative probability: [0.3, 0.3, 0.1, 0.2] -> [0.3, 0.6, 0.7, 1.0]
        indels = list(size_distribution.keys())
        probabilities = list(size_distribution.values())
        cumulative_probabilities = [sum(probabilities[:i+1]) for i in range(len(probabilities))]

        random_value = random.uniform(0, max(cumulative_probabilities))  # easiest way to account for slight rounding error from proportions
        for i, cumulative_probability in enumerate(cumulative_probabilities):
            if random_value < cumulative_probability:
                indel = indels[i]
                break
        
        return indel[0], int(indel[1:])
    
    # iterates through the current sequence, generating a new sequence via a concatenation method
    # if a base is not at the start of a homopolymer, it is added to the new string.
    # If a base is at the start of a homopolymer, then it may be randomly modified at a chance given by the homopolymer size
        # and the occurance distribution
    # Modified homopolymers are given an InDel at rates determined by the homopolymer size and the size distributions
        # special consideration needed to be given for deletions that are less than or greater than the initial homopolymer size
    def generate_homopolymer_mutations(self, occurance_distribution, size_distributions):
        new_sequence = ""

        # iterate through sequence, skip iterator forward on homopolymers, calculate homopolymer length and presence
        seqeunce_iterator = iter(range(len(self)))
        for i in seqeunce_iterator:
            j = i + 1
            while j < len(self) and self[i] == self[j]:
                j += 1
                next(seqeunce_iterator, None)
            h = j - i

            # not a homopolymer
            if h == 1:
                new_sequence += self[i]
                continue

            # Generate InDels on homopolymers; grab max key if current h_mer length not in dict
            # i.e: if InSilico data has a homopolymer length greater than what is seen from real data, grab the max from real data
            if h not in occurance_distribution.keys():
                h = max(occurance_distribution.keys())
            if random.random() < occurance_distribution[h]:
                indel_type, indel_size = Sequence.random_indel(size_distributions[h])
                if indel_type == '+':
                    new_sequence += self[i] * (h + indel_size)
                elif indel_type == '-':
                    if indel_size < h:
                        new_sequence += self[i] * (h - indel_size)
                    elif indel_size >= h:
                        for _ in range(indel_size - h):
                            next(seqeunce_iterator, None)
            else:
                new_sequence += self[i] * h
        
        self.sequence = new_sequence
        
    def generate_random_sequence(length):
        sequence = []
        [sequence.append(BASES[random.choice(len(BASES))]) for _ in range(length)]
        return ''.join(sequence)

    # takes a csv file containing size distribution data for homopolymer indels, returns it in dictionary format for use in generate_homopolymer_mutations
    # csv line format: [Indel Size, Indel type and length (ex: -10, 4, etc), Proportion for size]
    def generate_size_distribution_dictionary(csv_file):
        homopolymer_size_dists_dict = {}
        with open(csv_file, 'r', encoding='utf-8-sig') as file:
            file = csv.reader(file)
            for line in file:
                homopolymer_size = int(line[0])
                if homopolymer_size not in homopolymer_size_dists_dict.keys():
                    homopolymer_size_dists_dict[homopolymer_size] = {}
                if float(line[2]) > 0:
                    indel_type = '+' + str(line[1].strip()) if '-' not in line[1] else line[1].strip()
                    homopolymer_size_dists_dict[homopolymer_size][indel_type] = float(line[2])
    
        # Fill empty dictionary keys with the closest higher value up to the max from the file (16 as of 13Sep24)
        max_homopolymer_length = max(homopolymer_size_dists_dict.keys())
        for i in range(2, max_homopolymer_length):
            if i not in homopolymer_size_dists_dict.keys():
                j = i
                while j not in homopolymer_size_dists_dict.keys():
                    j += 1
                homopolymer_size_dists_dict[i] = homopolymer_size_dists_dict[j]

        return homopolymer_size_dists_dict


class Plasmid(Sequence):
    def __init__(self, name, sequence, restriction_enzyme):
        super().__init__(name, sequence)
        self.re = getattr(Restriction, restriction_enzyme) if restriction_enzyme else None
    
    def __str__(self):
        return f'{self.name}: {self.sequence[:100]}; re: {self.re}'
    
    def from_file(fasta_file, restriction_enzyme):
        if not os.path.isfile(fasta_file):
            raise ValueError(f'{fasta_file} (from the input file) does not exist; double check the path and spelling')
        record = SeqIO.read(fasta_file, 'fasta')
        return Plasmid(record.id, str(record.seq), restriction_enzyme)

    def linearize(self):
        restriction_site = self.re.search(Seq(self.sequence, ))
        if len(restriction_site) < 1:
            raise ValueError(f'No restriction site for {self.re} found in {self.sequence}')
        elif len(restriction_site) > 1:
            raise ValueError(f'{len(restriction_site)} sites found for {self.re} found in {self.sequence}\nthere should only be one')
        else:
            restriction_site = restriction_site[0]
            # print(f'name: {self.name}\trestriction enzyme: {self.re}\tsite:{restriction_site}')
            self.sequence = self.sequence[restriction_site - 1:] + self.sequence[:restriction_site - 1]


class Vector(Sequence):
    snapback_frequencies = []

    def __init__(self, name, attributes, pattern, *args):
        self.name = name
        self.pattern = pattern
        self.attributes = deepcopy(attributes)
        if 'repeatable' in args:
            repeat_arg_index = args.index('repeatable')
             # locate the start index of repeat in base pattern (raise an error if it doesn't exist)
            if len(args) < repeat_arg_index + 2 or \
                (type(args[repeat_arg_index + 1]) is not int and not str.isdigit(args[repeat_arg_index + 1])):
                raise ValueError('the argument after "repeatable" must contain the index of the attribute to repeat')
            # locate the end index of repeat in base pattern (if it exists)
            elif len(args) >= repeat_arg_index + 3 and \
                (type(args[repeat_arg_index + 2]) is int or str.isdigit(args[repeat_arg_index + 2])):
                self.generate_repeats(args[repeat_arg_index + 1], repeat_attribute_end=args[repeat_arg_index + 2])
            else:
                self.generate_repeats(args[repeat_arg_index + 1])
        if 'snapback' in args:
            self.generate_snapback()
        if 'repeat_itrs' in args:
            self.generate_extra_itr()
        if 'irregular_payload' in args:
            self.generate_irregular_payloads()
        self.sequence = ''.join([self.attributes[c] for c in self.pattern])
    
    def attributes_from_file(fasta_file):
        if not os.path.isfile(fasta_file):
            raise ValueError(f'{fasta_file} (from the input file) does not exist; double check the path and spelling')
        attributes = {}
        for record in SeqIO.parse(fasta_file, 'fasta'):
            attributes[record.id] = str(record.seq)
        return attributes
    
    def __str__(self):
        return f'{self.name}: {self.sequence}\n{self.pattern}: {self.attributes}'
        
    def generate_extra_itr(self):
        itr_keys = ['R', 'L', 'C']
        pattern = list(self.pattern)
        for i, c in enumerate(pattern):
            if c in itr_keys:
                pattern[i] = c * random.randint(1, 3)
        self.pattern = ''.join(pattern)

    def get_random_snapback_sizes():
        # getting random snapback size set based on cumulative distribution
        random_value = random.uniform(0, Vector.snapback_frequencies[-1][1])  # easiest way to account for slight rounding error from proportions
        for snapback_size_set, cumulative_probability in Vector.snapback_frequencies:
            if random_value < cumulative_probability:
                snapback_sizes_to_use = snapback_size_set
                break
        return [int(val) for val in snapback_sizes_to_use.split()]

    def generate_snapback(self):
        # converting all payloads in pattern to snapbacks
        pattern = list(self.pattern)
        for i, c in enumerate(pattern):
            if c == 'P':
                snapback_sizes_to_use = Vector.get_random_snapback_sizes()
                ref_payload_size = len(self.attributes['P'])
                ref_payload = self.attributes['P']
                # avoiding coordinate overlaps (unlikely in large seqs)
                if snapback_sizes_to_use[0] == snapback_sizes_to_use[1]:
                    if snapback_sizes_to_use[1] == ref_payload_size:
                        snapback_sizes_to_use[0] -= 1
                    else:
                        snapback_sizes_to_use[1] += 1
                if snapback_sizes_to_use[2] == snapback_sizes_to_use[3]:
                    if snapback_sizes_to_use[3] == ref_payload_size:
                        snapback_sizes_to_use[2] -= 1
                    else:
                        snapback_sizes_to_use[3] += 1
                # bp in this context is "breakpoint"
                snapback_sequence_pre_bp = ref_payload[snapback_sizes_to_use[0] : snapback_sizes_to_use[1]]
                snapback_sequence_post_bp = ref_payload[snapback_sizes_to_use[2] : snapback_sizes_to_use[3]]
                if abs(1-snapback_sizes_to_use[0]) <= abs(ref_payload_size -snapback_sizes_to_use[1]):
                    s_temp = Seq(snapback_sequence_post_bp).reverse_complement()
                    snapback_sequence_post_bp = str(s_temp)
                else:
                    s_temp = Seq(snapback_sequence_pre_bp).reverse_complement()
                    snapback_sequence_pre_bp = str(s_temp)
                snapback_sequence_full = snapback_sequence_pre_bp + snapback_sequence_post_bp
                # create new key for the new snapback tile, based (arbitrarily) on the current pattern index
                new_char = Vector.get_new_pattern_key(pattern)
                # save the resulting sequence into the Vector object's attribute dictionary, and replace the P in the pattern with that attribute key
                # Example: LPRPLP would turn into: LbRdLf
                self.attributes[new_char] = snapback_sequence_full
                pattern[i] = new_char
        self.pattern = ''.join(pattern)
    
    def generate_repeats(self, repeat_attribute_start, repeat_attribute_end=None):
        if repeat_attribute_end is None:
            repeat_attribute_end = len(self.pattern)
        repeat_attribute_start = int(repeat_attribute_start)
        if repeat_attribute_start > len(self.pattern):
            raise ValueError(f"can't start repeats at index {repeat_attribute_start}; the pattern for {self.name} is only {len(self.pattern)}")
        repeat_count = round(random.uniform(1, 5))
        self.pattern = self.pattern[:repeat_attribute_start] + (self.pattern[repeat_attribute_start:repeat_attribute_end] * (repeat_count)) + self.pattern[repeat_attribute_end:]
    
    def generate_irregular_payloads(self):
        new_pattern = list(self.pattern)
        for i, c in enumerate(self.pattern):
            if c == 'P':
                new_key = Vector.get_new_pattern_key(new_pattern)
                self.attributes[new_key] = self.attributes['P'] + self.attributes['P']
                new_pattern[i] = new_key
        self.pattern = ''.join(new_pattern)
    
    # Helper to get a new unused key to add to the pattern
    def get_new_pattern_key(pattern):
        new_char = string.ascii_lowercase[0]
        i = 0
        while new_char in pattern:
            i += 1
            new_char = string.ascii_lowercase[i]
        return new_char


if __name__ == '__main__':
    print('module')
