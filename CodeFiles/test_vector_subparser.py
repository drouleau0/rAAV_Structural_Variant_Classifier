import unittest
from vector_subparser import *
from tile_classes import *
from parse_file import *

class TestVectorSubParser(unittest.TestCase):
    def test_vector_lexer(self):
        test_lexer = VectorLexer()

        test_results = test_lexer.test('Payload')
        self.assertEqual('P', test_results[0]['type'])
        self.assertEqual('Payload', test_results[0]['value'])

        test_results = test_lexer.test('ITR-FLIP')
        self.assertEqual('I', test_results[0]['type'])
        self.assertEqual('ITR-FLIP', test_results[0]['value'])

        test_results = test_lexer.test(' ')
        self.assertEqual('AND', test_results[0]['type'])
        self.assertEqual(' ', test_results[0]['value'])

        test_results = test_lexer.test('Payload Payload ITR-FLIP ITR-FLIP Payload')
        correct_types = ['P', 'AND', 'P', 'AND', 'I', 'AND', 'I', 'AND', 'P']
        correct_values = ['Payload', ' ', 'Payload', ' ', 'ITR-FLIP', ' ', 'ITR-FLIP', ' ', 'Payload']
        i = 0
        for d in test_results:
            self.assertEqual(correct_types[i], d['type'])
            self.assertEqual(correct_values[i], d['value'])
            i += 1
    
    def test_vector_subparser(self):
        test_parser = VectorSubParser(VectorLexer())

        # 1 tile
        test_parser.run('ITR-FLIP')
        self.assertEqual('itr_only', test_parser.get_end_state())
        test_parser.run('Payload')
        self.assertEqual('payload_only', test_parser.get_end_state())

        # 2 tiles
        test_parser.run('ITR-FLIP Payload')
        self.assertEqual('truncated_right', test_parser.get_end_state())
        test_parser.run('Payload ITR-FLIP')
        self.assertEqual('truncated_left', test_parser.get_end_state())
        test_parser.run('Payload Payload')
        self.assertEqual('doubled_payload', test_parser.get_end_state())

        # 3 tiles
        test_parser.run('ITR-FLIP Payload ITR-FLIP')
        self.assertEqual('expected', test_parser.get_end_state())
        test_parser.run('ITR-FLIP Payload Payload')
        self.assertEqual('truncated_sp_IPP', test_parser.get_end_state())
        test_parser.run('Payload ITR-FLIP Payload')
        self.assertEqual('truncated_selfprime', test_parser.get_end_state())
        test_parser.run('Payload Payload ITR-FLIP')
        self.assertEqual('truncated_sp_PPI', test_parser.get_end_state())

        # 4 tiles
        test_parser.run('ITR-FLIP Payload ITR-FLIP Payload')
        self.assertEqual('extended', test_parser.get_end_state())
        test_parser.run('ITR-FLIP Payload Payload ITR-FLIP')
        self.assertEqual('snapback', test_parser.get_end_state())
        test_parser.run('Payload ITR-FLIP Payload ITR-FLIP')
        self.assertEqual('extended', test_parser.get_end_state())

        # 5 tiles
        test_parser.run('ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP')
        self.assertEqual('expected_selfprime', test_parser.get_end_state())
        test_parser.run('Payload ITR-FLIP Payload ITR-FLIP Payload')
        self.assertEqual('extended', test_parser.get_end_state())

        # 6 tiles
        test_parser.run('ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload')
        self.assertEqual('extended', test_parser.get_end_state())
        test_parser.run('Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP')
        self.assertEqual('extended', test_parser.get_end_state())
        test_parser.run('Payload Payload ITR-FLIP Payload Payload ITR-FLIP')
        self.assertEqual('truncated_snapback_selfprime', test_parser.get_end_state())
        # reverse of the above
        test_parser.run('ITR-FLIP Payload Payload ITR-FLIP Payload Payload')
        self.assertEqual('truncated_snapback_selfprime', test_parser.get_end_state())

        # 7 tiles
        test_parser.run('ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP')
        self.assertEqual('expected_selfprime', test_parser.get_end_state())
        test_parser.run('Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload')
        self.assertEqual('extended', test_parser.get_end_state())
        test_parser.run('ITR-FLIP Payload Payload ITR-FLIP Payload Payload ITR-FLIP')
        self.assertEqual('snapback_selfprime', test_parser.get_end_state())

        # 8 tiles 
        test_parser.run('ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload')
        self.assertEqual('extended', test_parser.get_end_state())
        test_parser.run('Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP')
        self.assertEqual('extended', test_parser.get_end_state())
        
        # 9 tiles
        test_parser.run('ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP')
        self.assertEqual('expected_selfprime', test_parser.get_end_state())
        test_parser.run('Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload')
        self.assertEqual('extended', test_parser.get_end_state())
        test_parser.run('Payload Payload ITR-FLIP Payload Payload ITR-FLIP Payload Payload ITR-FLIP')
        self.assertEqual('truncated_snapback_selfprime', test_parser.get_end_state())

        # 10 tiles 
        test_parser.run('ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload')
        self.assertEqual('extended', test_parser.get_end_state())
        test_parser.run('Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP')
        self.assertEqual('extended', test_parser.get_end_state())
        test_parser.run('ITR-FLIP Payload Payload ITR-FLIP Payload Payload ITR-FLIP Payload Payload ITR-FLIP')
        self.assertEqual('snapback_selfprime', test_parser.get_end_state())

        # 3000 tiles
        test_PIPI_string = 'Payload ITR-FLIP ' * 1500
        test_parser.run(test_PIPI_string.strip())
        self.assertEqual('extended', test_parser.get_end_state())
        test_IPIP_string = 'ITR-FLIP Payload ' * 1500
        test_parser.run(test_IPIP_string.strip())
        self.assertEqual('extended', test_parser.get_end_state())
        test_truncated_snapback_selfprime_string = 'Payload Payload ITR-FLIP ' * 1000
        test_parser.run(test_truncated_snapback_selfprime_string.strip())
        self.assertEqual('truncated_snapback_selfprime', test_parser.get_end_state())

        # 3001 tiles
        test_snapback_string = 'ITR-FLIP' + (' Payload Payload ITR-FLIP' * 1000) 
        test_parser.run(test_snapback_string)
        self.assertEqual('snapback_selfprime', test_parser.get_end_state())
        test_expected_selfprime_string = 'ITR-FLIP' + (' Payload ITR-FLIP' * 1500)
        test_parser.run(test_expected_selfprime_string)
        self.assertEqual('expected_selfprime', test_parser.get_end_state())
        test_truncated_selfprime_string = 'Payload' + (' ITR-FLIP Payload' * 1500)
        test_parser.run(test_truncated_selfprime_string)
        self.assertEqual('extended', test_parser.get_end_state())

        # other tests: tests to ensure all unclassified patterns end up in other
        # Adjacent ITRs. These shouldn't occur after preprocessing, but it's better that they
        # end up in 'other' than get misclassified in the case of an error
        test_parser.run('ITR-FLIP ITR-FLIP')
        self.assertEqual('other', test_parser.get_end_state())
        test_parser.run('ITR-FLIP ITR-FLIP ITR-FLIP')
        self.assertEqual('other', test_parser.get_end_state())
        test_parser.run(('ITR-FLIP ' * 100).strip())
        self.assertEqual('other', test_parser.get_end_state())
        test_parser.run('ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP ITR-FLIP')
        self.assertEqual('other', test_parser.get_end_state())
        # Adjacent Payloads greater than 2 tiles
        for i in range(3, 100):  # at one point 4x payload lengths were payload_only, and 5x were doubled_payload, so keep this test
            test_string = ('Payload ' * i).strip()
            test_parser.run(test_string)
            self.assertEqual('other', test_parser.get_end_state(), f'failure defining a group as "other": {i} Payloads')
        # Misc:
        misc_patterns = (
            'ITR-FLIP Payload Payload Payload',
            'Payload ITR-FLIP Payload Payload',
            'Payload Payload ITR-FLIP Payload',
            'ITR-FLIP Payload ITR-FLIP Payload Payload',
            'ITR-FLIP Payload Payload ITR-FLIP Payload',
            'Payload ITR-FLIP Payload ITR-FLIP Payload Payload',
            'ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload Payload',
            'Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload Payload',
            'ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload Payload',
            'Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload Payload'
        )
        for pattern in misc_patterns:
            test_parser.run(pattern)
            self.assertEqual('other', test_parser.get_end_state())
    
    def test_get_repeat_count(self):
        test_parser = VectorSubParser(VectorLexer())

        test_parser.run('Payload Payload')
        self.assertEqual(0, test_parser.get_repeat_count())
        test_parser.run('ITR-FLIP Payload')
        self.assertEqual(0, test_parser.get_repeat_count())

        test_parser.run('ITR-FLIP Payload ITR-FLIP')
        self.assertEqual(0, test_parser.get_repeat_count())
        test_parser.run('ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP')
        self.assertEqual(1, test_parser.get_repeat_count())
        test_parser.run('ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP')
        self.assertEqual(2, test_parser.get_repeat_count())
        test_parser.run('ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP')
        self.assertEqual(3, test_parser.get_repeat_count())
        test_parser.run(('ITR-FLIP' + 'Payload ITR-FLIP ' * 1000).strip())
        self.assertEqual(999, test_parser.get_repeat_count())

        test_parser.run('Payload ITR-FLIP')
        self.assertEqual(0, test_parser.get_repeat_count())
        test_parser.run('Payload ITR-FLIP Payload')
        self.assertEqual(0, test_parser.get_repeat_count())
        test_parser.run('Payload ITR-FLIP Payload ITR-FLIP')
        self.assertEqual(1, test_parser.get_repeat_count())
        test_parser.run('Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP')
        self.assertEqual(2, test_parser.get_repeat_count())
        test_parser.run('Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP')
        self.assertEqual(3, test_parser.get_repeat_count())
        test_parser.run('Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP')
        self.assertEqual(4, test_parser.get_repeat_count())
        test_parser.run(('Payload ITR-FLIP ' * 1000).strip())
        self.assertEqual(999, test_parser.get_repeat_count())

        test_parser.run('ITR-FLIP Payload')
        self.assertEqual(0, test_parser.get_repeat_count())
        test_parser.run('ITR-FLIP Payload ITR-FLIP Payload')
        self.assertEqual(1, test_parser.get_repeat_count())
        test_parser.run('ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload')
        self.assertEqual(2, test_parser.get_repeat_count())
        test_parser.run('ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload')
        self.assertEqual(3, test_parser.get_repeat_count())
        test_parser.run('ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload')
        self.assertEqual(4, test_parser.get_repeat_count())
        test_parser.run(('ITR-FLIP Payload ' * 1000).strip())
        self.assertEqual(999, test_parser.get_repeat_count())

        test_parser.run('ITR-FLIP Payload Payload ITR-FLIP')
        self.assertEqual(0, test_parser.get_repeat_count())
        test_parser.run('ITR-FLIP Payload Payload ITR-FLIP Payload Payload ITR-FLIP')
        self.assertEqual(1, test_parser.get_repeat_count())
        test_parser.run('ITR-FLIP Payload Payload ITR-FLIP Payload Payload ITR-FLIP Payload Payload ITR-FLIP')
        self.assertEqual(2, test_parser.get_repeat_count())
        test_parser.run(('ITR-FLIP' + 'Payload Payload ITR-FLIP ' * 1000).strip())
        self.assertEqual(999, test_parser.get_repeat_count())

        # Misc:
        misc_patterns = (
            'ITR-FLIP Payload Payload Payload',
            'Payload ITR-FLIP Payload Payload',
            'Payload Payload ITR-FLIP Payload',
            'ITR-FLIP Payload ITR-FLIP Payload Payload',
            'ITR-FLIP Payload Payload ITR-FLIP Payload',
            'Payload ITR-FLIP Payload ITR-FLIP Payload Payload',
            'ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload Payload',
            'Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload Payload',
            'ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload Payload',
            'Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload ITR-FLIP Payload Payload'
        )
        for pattern in misc_patterns:
            test_parser.run(pattern)
            self.assertEqual(0, test_parser.get_repeat_count(), f'repeat found in |{pattern}|')
    
    def test_check_snapback(self):
        test_parser = VectorSubParser(VectorLexer())

        sample = TileLine('1 1 ITR-FLIP[1-145](t) Payload[1-1000](t) Payload[1-1000](f) ITR-FLIP[1-145](t)')
        test_parser.run(sample)
        self.assertEqual('snapback', sample.category)
        self.assertFalse(sample.snapback_pattern_with_same_strand_payloads)

        sample = TileLine('1 1 ITR-FLIP[1-145](t) Payload[1-1000](t) Payload[1-1000](t) ITR-FLIP[1-145](t)')
        test_parser.run(sample)
        self.assertEqual('irregular_payload', sample.category)
        self.assertTrue(sample.snapback_pattern_with_same_strand_payloads)

        sample = TileLine('1 1 ITR-FLIP[1-145](t) Payload[1-1000](t) Payload[1-1000](t) ITR-FLIP[1-145](t) Payload[1-1000](t) Payload[1-1000](t) ITR-FLIP[1-145](t)')
        test_parser.run(sample)
        self.assertEqual('irregular_payload', sample.category)
        self.assertTrue(sample.snapback_pattern_with_same_strand_payloads)

        sample = TileLine('1 1 ITR-FLIP[1-145](t) Payload[1-1000](t) Payload[1-1000](f) ITR-FLIP[1-145](t) Payload[1-1000](t) Payload[1-1000](t) ITR-FLIP[1-145](t) Payload[1-1000](t) Payload[1-1000](f) ITR-FLIP[1-145](t)')
        test_parser.run(sample)
        self.assertEqual('other', sample.category)
        self.assertTrue(sample.snapback_pattern_with_same_strand_payloads)

        sample = TileLine('1 1 Payload[1-1000](t) Payload[1-1000](t) ITR-FLIP[1-145](t)')
        test_parser.run(sample)
        self.assertEqual('other', sample.category)
        self.assertTrue(sample.snapback_pattern_with_same_strand_payloads)

        sample = TileLine('1 1 ITR-FLIP[1-145](t) Payload[1-1000](t) Payload[1-1000](t) ITR-FLIP[1-145](t) Payload[1-1000](t) Payload[1-1000](f) ITR-FLIP[1-145](t)')
        test_parser.run(sample)
        self.assertEqual('other', sample.category)
        self.assertTrue(sample.snapback_pattern_with_same_strand_payloads)

        sample = TileLine('1 1 ITR-FLIP[1-145](t) Payload[1-1000](t) Payload[1-1000](f) ITR-FLIP[1-145](t) Payload[1-1000](t) Payload[1-1000](t) ITR-FLIP[1-145](t)')
        test_parser.run(sample)
        self.assertEqual('other', sample.category)
        self.assertTrue(sample.snapback_pattern_with_same_strand_payloads)
    
    def test_check_expected(self):
        test_parser = VectorSubParser(VectorLexer())

        sample = TileLine('1 1 ITR-FLIP[1-145](t) Payload[1-500](f) ITR-FLIP[1-145](f)')
        test_parser.run(sample)
        self.assertEqual('irregular_payload', sample.category)

        sample = TileLine('1 1 ITR-FLIP[1-145](t) Payload[1-1000](f) ITR-FLIP[1-145](f) Payload[1-500](f) ITR-FLIP[1-145](f)')
        test_parser.run(sample)
        self.assertEqual('irregular_payload', sample.category)

        test_parser = VectorSubParser(VectorLexer(), require_full_payloads_in_expected=False)

        sample = TileLine('1 1 ITR-FLIP[1-145](t) Payload[1-500](f) ITR-FLIP[1-145](f)')
        test_parser.run(sample)
        self.assertEqual('expected', sample.category)

        sample = TileLine('1 1 ITR-FLIP[1-145](t) Payload[1-1000](f) ITR-FLIP[1-145](f) Payload[1-500](f) ITR-FLIP[1-145](f)')
        test_parser.run(sample)
        self.assertEqual('expected_selfprime', sample.category)

    def test_run(self):
        test_parser = VectorSubParser(VectorLexer())

        sample = TileLine('2 0 polyA[2](f)')
        test_parser.run(sample)
        self.assertEqual('other', test_parser._end_state)

        sample = TileLine('2 0 polyA[2](f) polyA[2](f) polyA[2](f) polyA[2](f) polyA[2](f)')
        test_parser.run(sample)
        self.assertEqual('other', test_parser._end_state)

        with self.assertRaises(ValueError):
            test_parser.run(TileLine('2 0 foo[200](f)'))       


class TestTile(unittest.TestCase):
    def test_Tile_constructor(self):
        sample = Tile('ITR-FLIP[1-100](f)')
        self.assertEqual('ITR-FLIP', sample.name)
        self.assertEqual(1, sample.coordinate_start)
        self.assertEqual(100, sample.coordinate_end)
        self.assertEqual('f', sample.orientation)
        sample = Tile('fo-o-------f-oo[100](x)')
        self.assertEqual('fo-o-------f-oo', sample.name)
        self.assertEqual(100, sample.coordinate_start)
        self.assertIsNone(sample.coordinate_end)
        self.assertEqual('x', sample.orientation)

    def test_Tile_payload_sizing(self):
        sample = Tile('foo[56-20](t)')
        self.assertTrue(sample.is_full)
        sample = Tile('Payload[1-100](t)')
        self.assertFalse(sample.is_full)
        sample = Tile('Payload[1-1000](t)')
        self.assertTrue(sample.is_full)
        Tile.expected_payload_size = 5000
        sample = Tile('Payload[1-1000](t)')
        self.assertFalse(sample.is_full)
        sample = Tile('Payload[1-5000](t)')
        self.assertTrue(sample.is_full)
        sample = Tile('Payload[8-5000](t)')
        self.assertFalse(sample.is_full)
        Tile.expected_payload_size = 1000
    
    def test_compare_tiles(self):
        r = Tile("x[1-145](f)")
        self.assertEqual('full', r.compare_tiles(r))
        self.assertEqual('left_partial', Tile("x[20-145](f)").compare_tiles(r))
        self.assertEqual('right_partial', Tile("x[1-120](t)").compare_tiles(r))
        self.assertEqual('both_partial', Tile("x[20-100](f)").compare_tiles(r))

    def test_coordinates_are_equal(self):
        self.assertFalse(Tile.coordinates_are_equal(-6, 1))
        self.assertTrue(Tile.coordinates_are_equal(-5, 1))
        self.assertTrue(Tile.coordinates_are_equal(7, 1))
        self.assertFalse(Tile.coordinates_are_equal(8, 1))
        Tile.coordinate_buffer = 10
        self.assertFalse(Tile.coordinates_are_equal(-1, 10))
        self.assertTrue(Tile.coordinates_are_equal(0, 10))
        self.assertTrue(Tile.coordinates_are_equal(20, 10))
        self.assertFalse(Tile.coordinates_are_equal(21, 10))
        Tile.coordinate_buffer = 6

    def test_equality(self):
        r = Tile("ITR-FLIP[1-145](f)")
        x = Tile("ITR-FLIP[20-145](f)")
        self.assertEqual(r, r)
        self.assertNotEqual(r, x)
    
    def test_set_is_full(self):
        sample = Tile("ITR-FLIP[1-100](f)")
        self.assertEqual(sample.is_full, True)
        sample = Tile("Payload[1-100](f)")
        self.assertEqual(sample.is_full, False)
        sample = Tile("Payload[1-1000](f)")
        self.assertEqual(sample.is_full, True)


class TestTileLine(unittest.TestCase):
    def test_Tileline_constructor(self):
        x = TileLine('154 0 b[1-10](f) c[5-9](t) b[33-100](f) d[40](f)')
        self.assertEqual(154, x.count)
        self.assertTrue(Tile.name_matches(x[0], x[2]))
        self.assertFalse(Tile.name_matches(x[0], x[1]))
        self.assertEqual('f', x[3].orientation)
        self.assertEqual(40, x[3].coordinate_start)
        self.assertIsNone(x[3].coordinate_end)

    def test_set_condensed(self):
        # testing condensed_pattern Tile list creation
        self.assertEqual(TileLine('1 1 ITR-FLIP[1-145](f)'), 
                         TileLine('1 1 ITR-FLIP[1-145](f) ITR-FLIP[1-145](f) ITR-FLIP[1-145](f) ITR-FLIP[1-145](f) ITR-FLIP[1-145](f)').condensed_pattern)
        self.assertEqual(TileLine('1 1 ITR-FLIP[1-145](f) Payload[1-40](f) ITR-FLIP[1-145](f)'), 
                         TileLine('1 1 ITR-FLIP[1-145](f) Payload[1-40](f) ITR-FLIP[1-145](f) ITR-FLIP[1-145](f) ITR-FLIP[1-145](f)').condensed_pattern)
        self.assertEqual(TileLine('1 1 ITR-FLIP[1-145](f) Payload[1-40](f) ITR-FLIP[1-145](f)'), 
                         TileLine('1 1 ITR-FLIP[1-145](f) Payload[1-40](f) ITR-FLIP[1-145](f)' + ' ITR-FLIP[1-50](t)' * 500).condensed_pattern)
        self.assertEqual(TileLine('1 1 Payload[1-40](t) ITR-FLIP[1-145](f) Payload[1-40](f) ITR-FLIP[1-145](f) Payload[1-145](f)'), 
                         TileLine('1 1 Payload[1-40](t) ITR-FLIP[1-145](f) Payload[1-40](f) ITR-FLIP[1-145](f) ITR-FLIP[1-145](f) Payload[1-145](f)').condensed_pattern)
        self.assertEqual(TileLine('1 1 Payload[1-40](t) ITR-FLIP[1-145](f) Payload[1-40](f) ITR-FLIP[1-145](f) Payload[1-145](f) ITR-FLIP[1-145](f)'), 
                         TileLine('1 1 Payload[1-40](t) ITR-FLIP[1-145](f) ITR-FLIP[1-145](f) ITR-FLIP[1-145](f) Payload[1-40](f) ITR-FLIP[1-145](f) ITR-FLIP[1-145](f) Payload[1-145](f) ITR-FLIP[1-145](f) ITR-FLIP[1-145](f) ITR-FLIP[1-145](f) ITR-FLIP[1-145](f)').condensed_pattern)
        self.assertEqual(TileLine('1 1 ITR-FLIP[21-165](t) Payload[1-1387](t) Payload[1388-3893](t) ITR-FLIP[1-103](t)'), 
                         TileLine('1 1 ITR-FLIP[21-165](t) Payload[1-1387](t) polyA[23](t) polyA[24](t) Payload[1388-3893](t) ITR-FLIP[1-103](t)').condensed_pattern)
        self.assertEqual(TileLine('1 1 ITR-FLIP[21-165](t) Payload[1-1387](t) Payload[1388-3893](t) ITR-FLIP[1-103](t)'), 
                         TileLine('1 1 ITR-FLIP[21-165](t) ITR-FLIP[21-165](t) ITR-FLIP[21-165](t) polyA[2](t) Payload[1-1387](t) polyA[23](t) polyA[24](t) Payload[1388-3893](t) ITR-FLIP[1-103](t)').condensed_pattern)
        self.assertEqual('empty', 
                         TileLine('1 1 polyA[2](t)').condensed_pattern)
        self.assertEqual(TileLine('1 1 Payload[1-100](t)'), 
                         TileLine('1 1 polyA[2](t) polyA[2](t) Payload[1-100](t) polyA[2](t)').condensed_pattern)
        self.assertEqual(TileLine('1 1 Payload[1-40](f) ITR-FLIP[1-145](t) polyA[2](f) ITR-FLIP[1-145](t) Payload[1-40](f)').condensed_pattern,
                         TileLine('1 1 Payload[1-40](f) ITR-FLIP[1-145](t) Payload[1-40](f)'))
        # testing the mutated_itr and contains_polymer flags
        self.assertTrue(TileLine('1 1 ITR-FLIP[1-145](f) ITR-FLIP[1-145](f) ITR-FLIP[1-145](f) ITR-FLIP[1-145](f) ITR-FLIP[1-145](f)').irregular_itrs)
        self.assertFalse(TileLine('1 1 ITR-FLIP[1-145](f) Payload[1-40](f) ITR-FLIP[1-145](f)').irregular_itrs)
        self.assertFalse(TileLine('1 1 Payload[1-40](t) ITR-FLIP[1-145](f) Payload[1-40](f) ITR-FLIP[1-145](f) Payload[1-145](f)').irregular_itrs)
        self.assertTrue(TileLine('1 1 polyA[2](t)').contains_polymer)
        self.assertFalse(TileLine('0 0 ').contains_polymer)
        self.assertFalse(TileLine('0 0 ').irregular_itrs)
        self.assertTrue(TileLine('1 1 ITR-FLIP[21-165](t) ITR-FLIP[21-165](t) ITR-FLIP[21-165](t) polyA[2](t) Payload[1-1387](t) polyA[23](t) polyA[24](t) Payload[1388-3893](t) ITR-FLIP[1-103](t)').contains_polymer)
        self.assertTrue(TileLine('1 1 ITR-FLIP[21-165](t) ITR-FLIP[21-165](t) ITR-FLIP[21-165](t) polyA[2](t) Payload[1-1387](t) polyA[23](t) polyA[24](t) Payload[1388-3893](t) ITR-FLIP[1-103](t)').irregular_itrs)

    def test_check_linearity(self):
        sample1 = TileLine("1 1 Backbone[200-2000](t) ITR-FLIP[1-145](f) Payload[1-2000](t) ITR-FLIP[1-10](t)")
        self.assertEqual('forward_linear', sample1.linear_status)
        sample2 = TileLine("1 1 ITR-FLIP[1-145](t) Payload[1-2000](f) ITR-FLIP[1-145](t)")
        self.assertEqual('reverse_linear', sample2.linear_status)
        sample3 = TileLine("1 1 ITR-FLIP[1-145](t) Payload[1-2000](t) ITR-FLIP[1-145](f) ITR-FLIP[1-100](t) Payload[1-2000](f) ITR-FLIP[1-145](f)")
        self.assertEqual('non_linear', sample3.linear_status)
        sample4 = TileLine("1 1 ITR-FLIP[1-145](t) Payload[1-2000](t) ITR-FLIP[1-145](f) ITR-FLIP[1-100](t) Payload[1-2000](t) ITR-FLIP[1-145](f)")
        self.assertEqual('forward_linear', sample4.linear_status)
        sample5 = TileLine('1 1 ITR-FLIP[1-100](t) ITR-FLIP[1-100](f) ITR-FLIP[1-100](t) ITR-FLIP[1-100](f) ITR-FLIP[1-100](t)')
        self.assertEqual('itr_only', sample5.linear_status)
    
    def test_check_full_payload(self):
        sample = TileLine('1 1 ITR-FLIP[1-145](t) Payload[1-1000](t) Payload[1-1000](t) ITR-FLIP[1-145](t)')
        self.assertTrue(sample.contains_full_payload)
        sample = TileLine('1 1 ITR-FLIP[1-145](t) Payload[1-500](t) Payload[500-1000](t) ITR-FLIP[1-145](t)')
        self.assertFalse(sample.contains_full_payload)
        sample = TileLine('1 1 ITR-FLIP[1-145](t) Payload[1-993](t) Payload[8-1000](t) ITR-FLIP[1-145](t)')
        self.assertFalse(sample.contains_full_payload)
        Tile.expected_payload_size = 50
        Tile.coordinate_buffer = 0
        sample = TileLine('1 1 ITR-FLIP[1-145](t) Payload[1-51](t) Payload[1-49](f) ITR-FLIP[1-145](t) Payload[2-50](t) Payload[0-50](t) ITR-FLIP[1-145](t) Payload[1-51](t) Payload[1-50](f) ITR-FLIP[1-145](t)')
        self.assertTrue(sample.contains_full_payload)
        sample = TileLine('1 1 ITR-FLIP[1-145](t) Payload[1-51](t) Payload[1-49](f) ITR-FLIP[1-145](t) Payload[2-50](t) Payload[0-50](t) ITR-FLIP[1-145](t) Payload[1-51](t) Payload[3-49](f) ITR-FLIP[1-145](t)')
        self.assertFalse(sample.contains_full_payload)
        Tile.expected_payload_size = 1000
        Tile.coordinate_buffer = 6
        sample = TileLine('1 1 ITR-FLIP[1-145](t)')
        self.assertFalse(sample.contains_full_payload)

class TestTileBin(unittest.TestCase):
    def test_TileLineBin_constructor(self):
        # test constructor
        test_tileline = TileLine("110341 1 ITR-FLIP[1-145](f) Payload[1-2000](t) ITR-FLIP[1-10](t)")
        test_tileline.category = 'foo'  # manually set category so ValueError isn't raised
        sample = TileLineBin(test_tileline)
        self.assertEqual(110341, sample.sequence_count)
        self.assertEqual(1, len(sample.tile_line_list))
        self.assertEqual(TileLine("110341 1 ITR-FLIP[1-145](f) Payload[1-2000](t) ITR-FLIP[1-10](t)"), sample[0])
        # test add_tileline
        sample.add_tileline(TileLine('1 1 ITR-FLIP[1-145](f) ITR-FLIP[1-145](f) ITR-FLIP[1-145](f) ITR-FLIP[1-145](f) ITR-FLIP[1-145](f)'))
        self.assertEqual(TileLine('1 1 ITR-FLIP[1-145](f) ITR-FLIP[1-145](f) ITR-FLIP[1-145](f) ITR-FLIP[1-145](f) ITR-FLIP[1-145](f)'), sample[1])
        for _ in range(244):
            sample.add_tileline(TileLine('1 1 Payload[1-3](t)'))
        for i in range(2, 244):
            self.assertEqual(TileLine('1 1 Payload[1-3](t)'), sample[i])
        self.assertEqual(110586, sample.sequence_count)
        self.assertEqual(246, sample.pattern_count)
        self.assertEqual(0, sample[0].proportion)
        self.assertEqual(0, sample[1].proportion)
        # test calculate_tileline_proportions
        sample.calculate_tileline_proportions()
        self.assertEqual(0.99778, round(sample[0].proportion, 5))
        self.assertEqual(1e-5, round(sample[1].proportion, 5))
    
    def test_calculate_full_proportions(self):
        fulls = TileLine('75 1 Payload[1-1000](t) Payload[1-1000](t)')
        fulls.category = 'foo'
        partials = TileLine('25 1 Payload[1-500](t) Payload[1-500](t)')
        partials.category = 'foo'
        sample_bin = TileLineBin(fulls)
        sample_bin.add_tileline(partials)
        sample_bin.calculate_full_payload_proportions()
        self.assertEqual(.75, sample_bin.full_proportion)
        Tile.expected_payload_size = 50
        fulls = TileLine('75 1 Payload[1-1000](t) Payload[1-1000](t)')
        fulls.category = 'foo'
        partials = TileLine('25 1 Payload[1-500](t) Payload[1-1000](t)')
        partials.category = 'foo'
        sample_bin = TileLineBin(fulls)
        sample_bin.add_tileline(partials)
        sample_bin.calculate_full_payload_proportions()
        self.assertEqual(.0, sample_bin.full_proportion)
        Tile.expected_payload_size = 1000
        fulls = TileLine('75 1 Payload[1-1000](t) Payload[1-1000](t)')
        fulls.category = 'foo'
        fulls_2 = TileLine('25 1 Payload[1-1000](t) Payload[1-1000](t)')
        fulls_2.category = 'foo'
        sample_bin = TileLineBin(fulls)
        sample_bin.add_tileline(fulls_2)
        sample_bin.calculate_full_payload_proportions()
        self.assertEqual(1, sample_bin.full_proportion)


class TestFileParser(unittest.TestCase):
    test_file = '/analysis/Projects/Pipeline_Development/VectorSubparser2.1/DataFiles/Inputs/IntegrationTests/AllSequences.counts'

    def test_FileParser_constructor(self):
        test_bins = FileParser(self.test_file)
        self.assertEqual(0, len(test_bins.bins_list))
        self.assertEqual(66, len(test_bins.unbinned_tilelines))

    def test_process_U_line(self):
        bin_list = FileParser('')
        test_tileline_objects = bin_list.process_U_line('1 1 Payload[1-10](f) U Payload[1-10](t) ITR-FLIP[1-145](t) ITR-FLIP[1-145](f)')
        self.assertEqual('payload_only', test_tileline_objects[0].category)
        self.assertFalse(test_tileline_objects[0].irregular_itrs)
        self.assertEqual(0.5, test_tileline_objects[0].count)
        self.assertEqual('truncated_left', test_tileline_objects[1].category)
        self.assertTrue(test_tileline_objects[1].irregular_itrs)
        self.assertEqual(0.5, test_tileline_objects[1].count)
        test_tileline_objects = bin_list.process_U_line('108 1 Payload[1-10](t) polyA[100](t) Payload[1-10](f) U ITR-FLIP[1-145](t) Payload[1-1000](t) ITR-FLIP[1-145](t) ITR-FLIP[1-145](f)')
        self.assertEqual('doubled_payload', test_tileline_objects[0].category)
        self.assertTrue(test_tileline_objects[0].contains_polymer)
        self.assertEqual(54, test_tileline_objects[0].count)
        self.assertEqual('expected', test_tileline_objects[1].category)        
        self.assertFalse(test_tileline_objects[1].contains_polymer) 
        self.assertEqual(54, test_tileline_objects[1].count)
        test_tileline_objects = bin_list.process_U_line('10 1 Payload[1-10](f) U JAKU10101.1[1-20](f)')
        self.assertEqual('payload_only', test_tileline_objects[0].category)
        self.assertIsNone(test_tileline_objects[1])

    def test_process_x_2_line(self):
        bin_list = FileParser('')
        test_tileline_object = bin_list.process_x_2_line('18 1 Payload[1-10](f) x 2')
        self.assertEqual('payload_only', test_tileline_object.category)
        self.assertEqual(18, test_tileline_object.count)

    def test_process_line(self):
        bin_list = FileParser('')
        test_tileline_object = bin_list.process_line('18 1 ITR-FLIP[1-100](t) Payload[1-1000](f) ITR-FLIP[1-100](t) Payload[1-1000](t) ITR-FLIP[1-50](f) Payload[1-1000](t) ITR-FLIP[1-50](f)')
        self.assertEqual('expected_selfprime', test_tileline_object.category)
        self.assertEqual(18, test_tileline_object.count)
        self.assertEqual(2, test_tileline_object.repeat_count)

    def test_calculate_bin_proportions(self):
        test_bins = FileParser(self.test_file, raise_error_on_low_fulls=False)
        add_empty_untileable_sequence_bin(test_bins, self.test_file)
        test_bins.bin_tilelines()
        expected_categories_proportions = {"expected":10, "expected_selfprime":126, "itr_only":54, "payload_only":20, "truncated_right":43, "truncated_left":47, 
                                           "truncated_selfprime":78, "snapback":87, "snapback_selfprime":165, "doubled_payload":170, "truncated_sp_IPP":200, "truncated_sp_PPI":225, 
                                           "other":389, "extended":222, "irregular_payload":246, "truncated_snapback_selfprime":129, "untileable_sequences":123, }
        for key in expected_categories_proportions:
            expected_categories_proportions[key] = expected_categories_proportions[key]/2334
        test_bins.calculate_bin_proportions()
        for bin in test_bins.bins_list:
            if bin.name == 'other':
                continue
            self.assertEqual(expected_categories_proportions[bin.name], bin.proportion, f'test_process_file failed category proportion check at key: {bin.name}')

    def test_group_categories(self):
        test_bins = FileParser(self.test_file, raise_error_on_low_fulls=False)
        add_empty_untileable_sequence_bin(test_bins, self.test_file)
        # standard modification dictionary
        MOD_DICTIONARY = dict()
        MOD_DICTIONARY.update(dict.fromkeys(['expected', 'expected_selfprime'], 'expected'))
        MOD_DICTIONARY.update(dict.fromkeys(['itr_only', 'payload_only', 'truncated_right', 'truncated_left', 'truncated_selfprime'], 'truncated'))
        MOD_DICTIONARY.update(dict.fromkeys(['snapback', 'snapback_selfprime'], 'snapback'))
        MOD_DICTIONARY.update(dict.fromkeys(['truncated_sp_IPP', 'truncated_sp_PPI', 'truncated_snapback_selfprime'], 'truncated_snapback'))
        MOD_DICTIONARY.update(dict.fromkeys(['other', 'extended', 'irregular_payload', 'untileable_sequences', 'doubled_payload'], 'other'))
        test_bins.group_categories(MOD_DICTIONARY)
        test_bins.bin_tilelines()

        self.assertEqual(len(test_bins.bins_list), 5, f'{[bin.name for bin in test_bins.bins_list]}')
        expected_categories_counts = {"expected":136, "truncated":242, "snapback":252, "other":1150, "truncated_snapback":554, }
        expected_pattern_counts = {"expected":16, "truncated":11, "snapback":8, "other":19, "truncated_snapback":12, }
        for bin in test_bins.bins_list:
            self.assertEqual(expected_categories_counts[bin.name], bin.sequence_count, f'test_process_file failed category sequence_count check at key: {bin.name}')
            self.assertEqual(expected_pattern_counts[bin.name], bin.pattern_count, f'test_process_file failed category pattern_count check at key: {bin.name}')

    def test_bin_tilelines(self):
        test_bins = FileParser(self.test_file, raise_error_on_low_fulls=False)
        add_empty_untileable_sequence_bin(test_bins, self.test_file)
        test_bins.bin_tilelines()
        self.assertEqual(17, len(test_bins.bins_list))
        self.assertEqual(0, len(test_bins.unbinned_tilelines))
        expected_categories_counts = {"expected":10, "expected_selfprime":126, "itr_only":54, "payload_only":20, "truncated_right":43, "truncated_left":47, 
                                      "truncated_selfprime":78, "snapback":87, "snapback_selfprime":165, "doubled_payload":170, "truncated_sp_IPP":200, "truncated_sp_PPI":225, 
                                      "other":389, "extended":222, "irregular_payload":246, "truncated_snapback_selfprime":129, "untileable_sequences":123, }
        expected_pattern_counts = {"expected":4, "expected_selfprime":12, "itr_only":3, "payload_only":1, "truncated_right":2, "truncated_left":2, "truncated_selfprime":3, 
                                   "snapback":3, "snapback_selfprime":5, "doubled_payload":4, "truncated_sp_IPP":5, "truncated_sp_PPI":5, "other":7, "extended":4, 
                                   "irregular_payload":4, "truncated_snapback_selfprime":2, "untileable_sequences":0, }

        for bin in test_bins.bins_list:
            if bin.name == 'other':
                continue
            self.assertEqual(expected_categories_counts[bin.name], bin.sequence_count, f'test_process_file failed category sequence_count check at key: {bin.name}')
            self.assertEqual(expected_pattern_counts[bin.name], bin.pattern_count, f'test_process_file failed category pattern_count check at key: {bin.name}')

    def test_extended_payload_name(self):
        test_tileline = '14657 0.0602935 Payload_scAAV[1-100](t) polyA[1-10](t) U ITR-FLIP[21-165](t) Payload_scAAV[1-1831](f) ITR-FLIP[25-141](t) Payload_scAAV[1-1831](t) ITR-FLIP[21-165](f)'
        parser = FileParser('', raise_error_on_low_fulls=False, require_full_payloads_in_expected=False)
        lines = parser.process_U_line(test_tileline)
        self.assertEqual('payload_only', lines[0].category)
        self.assertEqual('expected_selfprime', lines[1].category)

if __name__ == '__main__':
    unittest.main()
