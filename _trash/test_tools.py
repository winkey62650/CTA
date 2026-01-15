import unittest
import os
import json
import pandas as pd
from scan_factors import scan_factors

class TestFactorTools(unittest.TestCase):
    
    def setUp(self):
        self.root_dir = os.getcwd()
        
    def test_scan_factors(self):
        """Test if scan_factors returns valid list of factors"""
        factors = scan_factors(self.root_dir)
        self.assertTrue(len(factors) > 0)
        
        # Check structure
        sample = factors[0]
        self.assertIn('name', sample)
        self.assertIn('path', sample)
        self.assertIn('param_count', sample)
        self.assertIn('import_path', sample)
        
    def test_metadata_file(self):
        """Test if metadata json exists and is valid"""
        self.assertTrue(os.path.exists('factor_metadata.json'))
        with open('factor_metadata.json', 'r') as f:
            data = json.load(f)
            self.assertTrue(isinstance(data, list))
            
    def test_analysis_report(self):
        """Test if analysis reports are generated"""
        self.assertTrue(os.path.exists('Factor_Analysis.md'))
        # Multi factor report might not exist if run failed, but in this session it passed
        self.assertTrue(os.path.exists('Multi_Factor_Analysis_Report.md'))

if __name__ == '__main__':
    unittest.main()
