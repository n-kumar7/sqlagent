# tests/test_utils.py

import unittest
import os
import json
from utils.global_utils import extract_fenced_code, current_timestamp, load_config, setup_logging

class TestGlobalUtils(unittest.TestCase):
    def test_extract_fenced_code(self):
        text = """```sql
-- Purpose: Test query
SELECT * FROM test_table;
```"""
        code = extract_fenced_code(text, language="sql")
        self.assertIn("SELECT * FROM test_table;", code)
        self.assertNotIn("```", code)

    def test_current_timestamp(self):
        ts = current_timestamp()
        # Check the format (YYYYMMDD_HHMMSS) which is 15 characters long.
        self.assertEqual(len(ts), 15)

    def test_load_config(self):
        # Create a temporary configuration file
        temp_config = {"key": "value"}
        temp_filename = "temp_config.json"
        with open(temp_filename, "w", encoding="utf-8") as f:
            json.dump(temp_config, f)
        loaded_config = load_config(temp_filename)
        self.assertEqual(loaded_config, temp_config)
        os.remove(temp_filename)
    
    def test_setup_logging(self):
        # Ensure setup_logging runs without error.
        try:
            setup_logging()
        except Exception as e:
            self.fail(f"setup_logging() raised an exception: {e}")

if __name__ == '__main__':
    unittest.main()
