import unittest
from sequence_classes import *
from Subparser_In_Silico import generate_zmw_mismatch, set_snapback_frequencies
import os

class Test_Sequence(unittest.TestCase):
    def test_mutate_sequence(self):
        random.seed(900)
        original_sequence = 'CCCAAAGGAACCC' * 50
        test_sequence = Sequence('foo', original_sequence)
        test_sequence.mutate_sequence(0, len(test_sequence), subs_only=True, mutation_rate=1)
        self.assertEqual(13 * 50, len(test_sequence))
        for i in range(len(test_sequence)):
            self.assertNotEqual(original_sequence[i], test_sequence[i])
        
        original_sequence = 'CCCAAAGGAACCC'
        test_sequence = Sequence('foo', original_sequence)
        mutate_start = 3
        mutate_end = 7
        test_sequence.mutate_sequence(mutate_start, mutate_end, subs_only=True, mutation_rate=1)
        for i in range(len(test_sequence)):
            if i >= mutate_start and i < mutate_end:
                self.assertNotEqual(original_sequence[i], test_sequence[i], f'\n{test_sequence}\n{original_sequence}\n')
            else:
                self.assertEqual(original_sequence[i], test_sequence[i], f'index of failure: {i}')
        
        original_sequence = 'CCCAAAGGAACCC'
        test_sequence = Sequence('foo', original_sequence)
        mutate_start = 5
        mutate_end = 6
        test_sequence.mutate_sequence(mutate_start, mutate_end, subs_only=True, mutation_rate=1)
        for i in range(len(test_sequence)):
            if i >= mutate_start and i < mutate_end:
                self.assertNotEqual(test_sequence[i], original_sequence[i], f'\n{test_sequence}\n{original_sequence}\n')
            else:
                self.assertEqual(test_sequence[i], original_sequence[i], f'index of failure: {i}')
        
        test_sequence = Sequence('foo', 'CCCAAAGGACC')
        test_results = []
        for _ in range(100):
            test_sequence.modify_sequence(test_sequence.mutate_sequence, 0.5, True, 0.1)
            test_results.append(test_sequence.sequence)
            test_sequence.sequence = 'acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga'
        self.assertTrue('acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga' in test_results)
        self.assertFalse(all(x == 'acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga' for x in test_results))

    def test_flip_sequence(self):
        sample_seq = Sequence('foo', 'acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga')
        sample_seq.flip_sequence(10, 20)
        self.assertEqual(sample_seq.sequence, 'acgcgacgttttccaattggaaacccgggttttgggtttgccaccgctga')
        
        sample_seq.flip_sequence(30, 40)
        self.assertEqual(sample_seq.sequence, 'acgcgacgttttccaattggaaacccgggtgtttgggtttccaccgctga')

        sample_seq.flip_sequence(0, 5)
        self.assertEqual(sample_seq.sequence, 'gcgcaacgttttccaattggaaacccgggtgtttgggtttccaccgctga')

        sample_seq.flip_sequence(6, 10)
        sample_seq.flip_sequence(2, 7)
        self.assertEqual(sample_seq.sequence, 'gctaacgtgcttccaattggaaacccgggtgtttgggtttccaccgctga')

        test_sequence = Sequence('foo', 'acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga')
        test_results = []
        for _ in range(100):
            test_sequence.modify_sequence(test_sequence.flip_sequence, 0.5, 10, 20)
            test_results.append(test_sequence.sequence)
            test_sequence.sequence = 'acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga'
        self.assertTrue('acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga' in test_results)
        self.assertTrue('acgcgacgttttccaattggaaacccgggttttgggtttgccaccgctga' in test_results)

    def test_duplicate_sequence(self):
        test_seq = Sequence('foo', 'CCCAAAGGAACCC')
        test_seq.duplicate_sequence(0, 13)
        self.assertEqual(test_seq.sequence, 'CCCAAAGGAACCCCCCAAAGGAACCC')

        test_seq = Sequence('foo','CCCAAAGGAACCC')
        test_seq.duplicate_sequence(2, 8)
        self.assertEqual(test_seq.sequence, 'CCCAAAGGCAAAGGAACCC')

        test_sequence = Sequence('foo', 'acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga')
        test_results = []
        for _ in range(100):
            test_sequence.modify_sequence(test_sequence.duplicate_sequence, 0.5)
            test_results.append(test_sequence.sequence)
            test_sequence.sequence = 'acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga'
        self.assertTrue('acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga' in test_results)
        self.assertTrue('acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctgaacgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga' in test_results)

    def test_insert_sequence(self):
        test_sequence = Sequence('foo','CCCAAAGGAACCC')
        test_sequence.insert_sequence(12, 'XXX')
        self.assertEqual(test_sequence.sequence, 'CCCAAAGGAACCCXXX')

        test_sequence = Sequence('Foo', 'CCCAAAGGAACCC')
        test_sequence.insert_sequence(3, 'XXX')
        self.assertEqual(test_sequence.sequence, 'CCCAXXXAAGGAACCC')

        test_sequence = Sequence('foo', 'acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga')
        test_results = []
        for _ in range(100):
            test_sequence.modify_sequence(test_sequence.insert_sequence, 0.5, 3, 'XXX')
            test_results.append(test_sequence.sequence)
            test_sequence.sequence = 'acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga'
        self.assertTrue('acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga' in test_results)
        self.assertTrue('acgcXXXgacgttggttaaccttaaacccgggttttgggtttgccaccgctga' in test_results)

    def test_delete_sequence(self):
        test_sequence = Sequence('Foo', 'CCCAAAGGAACCC')
        test_sequence.delete_sequence(0, 13)
        self.assertEqual(test_sequence.sequence, '')

        test_sequence = Sequence('Foo', 'CCCAAAGGAACCC')
        test_sequence.delete_sequence(3, 10)
        self.assertEqual(test_sequence.sequence, 'CCCCCC')

        test_sequence = Sequence('Foo', 'ACCCTGAAGTTCATCTGCACCACCGGCAAGCTGC')
        test_sequence.delete_sequence(10, 11)
        self.assertEqual(test_sequence.sequence, 'ACCCTGAAGTCATCTGCACCACCGGCAAGCTGC')

        test_sequence = Sequence('foo', 'acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga')
        test_results = []
        for _ in range(100):
            test_sequence.modify_sequence(test_sequence.delete_sequence, 0.5, 4, 10)
            test_results.append(test_sequence.sequence)
            test_sequence.sequence = 'acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga'
        self.assertTrue('acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga' in test_results)
        self.assertTrue('acgcggttaaccttaaacccgggttttgggtttgccaccgctga' in test_results)

    def test_reverse_complement(self):
        test_sequence = Sequence('Foo', 'CCCAAAGGAACCC')
        test_sequence.reverse_complement(0, len(test_sequence))
        self.assertEqual(test_sequence.sequence, 'GGGTTCCTTTGGG')

        test_sequence.reverse_complement(2, 8)
        self.assertEqual(test_sequence.sequence, 'GGAGGAACTTGGG')

        test_sequence = Sequence('foo', 'CCCGGGAAATTT')
        test_sequence.modify_sequence(test_sequence.reverse_complement)
        self.assertEqual(test_sequence.sequence, 'AAATTTCCCGGG')

        test_sequence = Sequence('foo', 'acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga')
        test_results = []
        for _ in range(100):
            test_sequence.modify_sequence(test_sequence.reverse_complement, 0.5, 4, 10)
            test_results.append(test_sequence.sequence)
            test_sequence.sequence = 'acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga'
        self.assertTrue('acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga' in test_results)
        self.assertTrue('acgcaacgtcggttaaccttaaacccgggttttgggtttgccaccgctga' in test_results)

    def test_create_hairpin(self):
        test_sequence = Sequence('Foo', 'CCCAAAGGAACCC')
        test_sequence.create_hairpin(0, len(test_sequence.sequence), False)
        self.assertEqual(test_sequence.sequence, 'CCCAAAGGAACCCGGGTTCCTTTGGG')

        test_sequence.create_hairpin(0, len(test_sequence.sequence), True)
        self.assertEqual(test_sequence.sequence, 'CCCAAAGGAACCCGGGTTCCTTTGGGCCCAAAGGAACCCGGGTTCCTTTGGG')

        test_sequence = Sequence('foo', 'acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga')
        test_results = []
        for _ in range(100):
            test_sequence.modify_sequence(test_sequence.create_hairpin, 0.5, 4, 10, False)
            test_results.append(test_sequence.sequence)
            test_sequence.sequence = 'acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga'
        self.assertTrue('acgcgacgttggttaaccttaaacccgggttttgggtttgccaccgctga' in test_results)
        self.assertTrue('acgcgacgttaacgtcggttaaccttaaacccgggttttgggtttgccaccgctga' in test_results)

    def test_random_sequence(self):
        for i in range(100):
            test_sequence = Sequence.generate_random_sequence(i)
            self.assertEqual(i, len(test_sequence))
            self.assertTrue('-' not in test_sequence)

    def test_generate_homopolymer_mutations(self):
        # testing deletions
        random.seed(10)
        test_sequence = Sequence('foo', 'ccagttttagtccccc')
        test_sequence.generate_homopolymer_mutations({2: 1, 3: 1, 5: 1}, {2: {'-5': 1}, 3: {'-1': 1}, 5: {'-5':1}})
        self.assertEqual(test_sequence.sequence, 'ttagt')

        # testing insertions
        test_sequence = Sequence('bar', 'cctg')
        test_sequence.generate_homopolymer_mutations({2: 1}, {2: {'+3': 1}})
        self.assertEqual(test_sequence.sequence, 'ccccctg')

        # test both
        test_sequence = Sequence('foobar', 'ccgttttgaccc')
        test_sequence.generate_homopolymer_mutations({2: 1, 4: 1}, {2: {'+3': 1}, 4: {'-7': 1}})
        self.assertEqual(test_sequence.sequence, 'cccccgccccc')

        # test occurance frequency
        test_results = []
        for _ in range(10):
            test_sequence = Sequence('zanzibar', 'ccctg')
            test_sequence.generate_homopolymer_mutations({3: 0.5}, {3: {'-4': 1}})
            test_results.append(test_sequence.sequence)
        self.assertTrue('ccctg' in test_results)
        self.assertTrue('g' in test_results)

    def test_random_indel(self):
        random.seed(10)
        test_distribution = {'+100': 0.01, '-2': 0.79, '-1': 0.1, '+3': 0.1}
        result_types = []
        result_sizes = []
        for _ in range(100):
            result_type, result_size = Sequence.random_indel(test_distribution)
            result_types.append(result_type)
            result_sizes.append(result_size)
        for key in test_distribution:
            self.assertTrue(key[0] in result_types, f'{key[0]} is missing')
            self.assertTrue(int(key[1:]) in result_sizes, f'{key[1:]} is missing')

    def test_generate_size_distribution_dictionary(self):
        test_file = 'test_files/test_file.csv'
        test_dict = Sequence.generate_size_distribution_dictionary(test_file)
        expected_dict = {2: {'-10': 0.05, '-1': 0.5, '+1': 0.4, '+2': 0.05}, 3: {'-5': 0.1, '-1': 0.4, '+1':0.5}, 4: {'-3': 1.0}, 5: {'-3': 1.0}, 6: {'-2': 0.5, '+2': 0.5}, 7: {'-2': 0.5, '+2': 0.5}, 8: {'-2': 0.5, '+2': 0.5}}
        self.assertEqual(expected_dict, test_dict)

class Test_Vector(unittest.TestCase):
    test_attributes = {'L': 'CCC', 'P': 'TTT', 'R': 'GGG', 'C': 'AAA'}

    def test_constructor(self):
        test_vector = Vector('Foo', self.test_attributes, 'LPR')
        self.assertEqual(test_vector.sequence, 'CCCTTTGGG')
    
    def test_generate_extra_itrs(self):
        random.seed(901)
        test_vector = Vector('Foo', self.test_attributes, 'LPR', 'repeat_itrs')
        self.assertEqual(test_vector.sequence, 'CCCCCCTTTGGGGGG')
    
    def test_generate_repeat(self):
        random.seed(905)
        test_patterns = list()

        for _ in range(100):
            test_vector = Vector('Foo', self.test_attributes, 'LPR', 'repeatable', '1')
            test_patterns.append(test_vector.pattern)
        self.assertTrue('LPR' in test_patterns)
        self.assertTrue('LPRPR' in test_patterns)
        self.assertTrue('LPRPRPR' in test_patterns)
        self.assertTrue('LPRPRPRPR' in test_patterns)
        self.assertTrue('LPRPRPRPRPR' in test_patterns)
        self.assertFalse('LPRPRPRPRPRPR' in test_patterns)

        for _ in range(100):
            test_vector = Vector('Foo', self.test_attributes, 'LPR', 'repeatable', 2)
            test_patterns.append(test_vector.pattern)
        self.assertTrue('LPR' in test_patterns)
        self.assertTrue('LPRR' in test_patterns)
        self.assertTrue('LPRRR' in test_patterns)
        self.assertTrue('LPRRRR' in test_patterns)
        self.assertTrue('LPRRRRR' in test_patterns)
        self.assertFalse('LPRRRRRR' in test_patterns)

        # testing end coordinate usage
        test_patterns = list()
        for _ in range(100):
            test_vector = Vector('Foo', self.test_attributes, 'LPCPR', 'repeatable', 2, 4)
            test_patterns.append(test_vector.pattern)
        self.assertTrue('LPCPR' in test_patterns)
        self.assertTrue('LPCPCPR' in test_patterns)
        self.assertTrue('LPCPCPCPR' in test_patterns)
        self.assertTrue('LPCPCPCPCPR' in test_patterns)
        self.assertTrue('LPCPCPCPCPCPR' in test_patterns)
        self.assertFalse('LPCPCPCPCPCPCPR' in test_patterns)
    
    def test_get_new_pattern_key(self):
        self.assertEqual(Vector.get_new_pattern_key('LPR'), 'a')
        self.assertEqual(Vector.get_new_pattern_key('LaRLbRcdef'), 'g')


class Test_Subparser_In_Silico(unittest.TestCase):
    test_attributes = {'L': 'CCC', 'P': 'TTT', 'R': 'GGG', 'C': 'CCGG'}

    def test_repeatable(self):
        random.seed(900)
        vector_sequences = []
        for _ in range(100):
            test_vector = Vector('Foo', self.test_attributes, 'LPCPR', 'repeatable', 2, 4)
            vector_sequences.append(test_vector.sequence)
        self.assertFalse('CCCTTTGGG' in vector_sequences)
        self.assertTrue('CCCTTTCCGGTTTGGG' in vector_sequences)
        self.assertTrue('CCCTTTCCGGTTTCCGGTTTGGG' in vector_sequences)
        self.assertTrue('CCCTTTCCGGTTTCCGGTTTCCGGTTTGGG' in vector_sequences)
        self.assertTrue('CCCTTTCCGGTTTCCGGTTTCCGGTTTCCGGTTTGGG' in vector_sequences)
        self.assertTrue('CCCTTTCCGGTTTCCGGTTTCCGGTTTCCGGTTTCCGGTTTGGG' in vector_sequences)
        self.assertFalse('CCCTTTCCGGTTTCCGGTTTCCGGTTTCCGGTTTCCGGTTTCCGGTTTGGG' in vector_sequences)
        
    def test_repeat_itrs(self):
        random.seed(902)
        test_sequences = []
        for _ in range(100):
            test_vector = Vector('Foo', self.test_attributes, 'LPR', 'repeat_itrs')
            test_sequences.append(test_vector.sequence)
        self.assertTrue('CCCTTTGGG' in test_sequences)
        self.assertTrue('CCCTTTGGGGGG' in test_sequences)
        self.assertTrue('CCCCCCTTTGGG' in test_sequences)
        self.assertTrue('CCCCCCTTTGGGGGG' in test_sequences)
        self.assertFalse('CCCCCCCCCTTTGGG' in test_sequences)

    def test_generate_irregular_payload(self):
        random.seed(900)
        test_vector = Vector('Foo', self.test_attributes, 'LPR', 'irregular_payload')
        self.assertEqual(test_vector.pattern, 'LaR')
        self.assertEqual(test_vector.sequence, 'CCCTTTTTTGGG')
        test_vector = Vector('Foo', self.test_attributes, 'LPRLPR', 'irregular_payload')
        self.assertEqual(test_vector.pattern, 'LaRLbR')
        self.assertEqual(test_vector.sequence, 'CCCTTTTTTGGGCCCTTTTTTGGG')

    def test_generate_zmw_mismatch(self):
        random.seed(902)

        # testing mismatch_pattern=False
        test_vector = Vector('Foo', self.test_attributes, 'LPR')
        new_test_vector = generate_zmw_mismatch(test_vector, mismatch_pattern=False)
        self.assertEqual(test_vector.name, 'Foo/fwd')
        self.assertEqual(new_test_vector.name, 'Foo/rev')
        self.assertEqual(len(new_test_vector.pattern), 4)
        self.assertTrue('a' in new_test_vector.pattern)
        test_patterns = []
        for _ in range(100):
            test_vector = Vector('Foo', self.test_attributes, 'LPR')
            new_test_vector = generate_zmw_mismatch(test_vector, mismatch_pattern=False)
            test_patterns.append(new_test_vector.pattern)
        self.assertFalse('LPR' in test_patterns)
        self.assertTrue('aLPR' in test_patterns)
        self.assertTrue('LaPR' in test_patterns)
        self.assertTrue('LPaR' in test_patterns)
        self.assertTrue('LPRa' in test_patterns)

        # testing mismatch_pattern=True
        test_vector = Vector('Foo', self.test_attributes, 'LPR')
        new_test_vector = generate_zmw_mismatch(test_vector, mismatch_pattern=True)
        self.assertEqual(test_vector.name, 'Foo/fwd')
        self.assertEqual(new_test_vector.name, 'Foo/rev')
        self.assertEqual(new_test_vector.sequence, 'GGAACC')
        test_vector = Vector('Foo', {'P': 'CCC'}, 'P')
        new_test_vector = generate_zmw_mismatch(test_vector, mismatch_pattern=True)
        self.assertEqual(new_test_vector.pattern, 'P')
        self.assertEqual(new_test_vector.sequence, 'GG')
    

if __name__ == '__main__':
    unittest.main()
