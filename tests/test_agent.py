import unittest
from unittest.mock import MagicMock, patch
from queue_manager.shared_queue import SharedQueue
from agent.ai_query_generator import AIQueryGenerator
from pathlib import Path
import shutil

# Create a dummy subclass to override methods that rely on external resources.
class DummyAIQueryGenerator(AIQueryGenerator):
    def __init__(self, connection_string, shared_queue):
        # Instead of calling the full __init__, set only what we need.
        self.connection_string = connection_string
        self.shared_queue = shared_queue
        self.logs_dir = Path("logs/sql")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.model_name = "dummy-model"
        self.temperature = 0.0
        self.schema_text = "Dummy schema for testing"
        # Use a fixed responses list to ensure exactly two valid queries, then "DONE"
        self.responses = [
            """```sql
-- Purpose: Dummy test query 1
SELECT * FROM dummy_table_1;
```""",
            """```sql
-- Purpose: Dummy test query 2
SELECT * FROM dummy_table_2;
```""",
            "DONE"
        ]
        self.response_index = 0

    def _generate_llm_message(self, messages):
        response = self.responses[self.response_index]
        self.response_index += 1
        return response

class TestAgent(unittest.TestCase):
    def setUp(self):
        """Set up shared resources for tests."""
        self.dummy_queue = SharedQueue()
        self.generator = DummyAIQueryGenerator("dummy_connection", self.dummy_queue)
        self.logs_dir = self.generator.logs_dir

    def tearDown(self):
        """Clean up test artifacts."""
        if self.logs_dir.exists():
            shutil.rmtree(self.logs_dir)

    def test_extract_sql_query_and_comment(self):
        """Test extracting SQL query and comment from LLM output."""
        dummy_response = """```sql
-- Purpose: Dummy test query
SELECT * FROM dummy_table_1;
```"""
        query, comment = self.generator._extract_sql_query_and_comment(dummy_response)
        self.assertIn("SELECT * FROM dummy_table_1;", query)  # Match dummy response
        self.assertEqual(comment, "Dummy test query")

    def test_generate_queries_queues_messages(self):
        """Test that queries are generated and placed on the shared queue."""
        self.generator.generate_queries("Test goal", max_queries=2)
        messages = []
        while not self.dummy_queue.empty():
            messages.append(self.dummy_queue.get())
        self.assertEqual(len(messages), 2)  # Expect 2 queries
        self.assertIn("SELECT * FROM dummy_table_1;", messages[0].query)
        self.assertEqual(messages[0].comment, "Dummy test query 1")
        self.assertIn("SELECT * FROM dummy_table_2;", messages[1].query)
        self.assertEqual(messages[1].comment, "Dummy test query 2")

    @patch("agent.ai_query_generator.Path.write_text")
    def test_log_query_to_file(self, mock_write_text):
        """Test that queries are logged to files."""
        query = "SELECT * FROM dummy_table;"
        comment = "Dummy test query"
        self.generator._log_query_to_file(query, comment, index=1)
        mock_write_text.assert_called_once()
        args, kwargs = mock_write_text.call_args
        self.assertIn("-- Dummy test query", args[0])
        self.assertIn("SELECT * FROM dummy_table;", args[0])

    def test_edge_case_no_sql_in_response(self):
        """Test handling of LLM output with no SQL query."""
        with patch.object(self.generator, "_generate_llm_message", return_value="No SQL here"):
            self.generator.generate_queries("Test goal", max_queries=1)
            self.assertTrue(self.dummy_queue.empty())

    def test_edge_case_no_comment_in_response(self):
        """Test handling of LLM output with no comment."""
        with patch.object(self.generator, "_generate_llm_message", return_value="```sql\nSELECT * FROM dummy_table;\n```"):
            self.generator.generate_queries("Test goal", max_queries=1)
            msg = self.dummy_queue.get()
            self.assertEqual(msg.comment, "No purpose comment provided by LLM")
            self.assertIn("SELECT * FROM dummy_table;", msg.query)

if __name__ == '__main__':
    unittest.main()
