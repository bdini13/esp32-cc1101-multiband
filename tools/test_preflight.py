#!/usr/bin/env python3
import unittest
from preflight import evaluate, REQUIRED_REVIEWS

class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.erc = {'sheets': [{'violations': []}]}
        self.drc = {'violations': [], 'unconnected_items': []}
        self.bom = [{'Qty per board': '1', 'Proposed part': 'example'}]
        self.reviews = [{'id': name, 'status': 'approved', 'reviewer': 'test fixture',
                         'evidence': 'test only'} for name in REQUIRED_REVIEWS]

    def result(self):
        return evaluate(self.erc, self.drc, self.bom, self.reviews)[1]

    def test_zero_drc_does_not_override_unconnected(self):
        self.drc['unconnected_items'] = [{}]
        self.assertIn('candidate_unconnected: 1', self.result())

    def test_all_required_reviews_mandatory(self):
        self.reviews = []
        self.assertEqual(len(self.result()), 6)

    def test_empty_signature_is_not_approval(self):
        self.reviews[0]['reviewer'] = ' '
        self.assertEqual(len(self.result()), 1)

    def test_populated_bom_only(self):
        self.bom += [{'Qty per board': '0', 'Proposed part': ''}]
        self.assertEqual(self.result(), [])
        self.bom[0]['Proposed part'] = ''
        self.assertIn('populated_positions_without_exact_part: 1', self.result())

    def test_erc_drc_parity_all_block(self):
        self.erc['sheets'][0]['violations'] = [{}]
        self.drc['violations'] = [{}]
        self.drc['schematic_parity'] = [{}]
        self.assertEqual(len(self.result()), 3)

    def test_duplicate_review_rejected(self):
        self.reviews += [self.reviews[0]]
        self.assertIn('Duplicate human review IDs', self.result())

if __name__ == '__main__':
    unittest.main()
