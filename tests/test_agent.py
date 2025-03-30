# tests/test_agent.py

import unittest
from queue_manager.shared_queue import SharedQueue
from agent.ai_query_generator import AIQueryGenerator

# Create a dummy subclass to override methods that rely on external resources.
class DummyAIQueryGenerator(AIQueryGenerator):
    def __init__(self, connection_string, shared_queue):
        # Instead of calling the full __init__, set only what we need.
        self.connection_string = connection_string
        self.shared_queue = shared_queue
        self.logs_dir = "logs/sql"
        self.model_name = "dummy-model"
        self.temperature = 0.0
        self.schema_text = "Dummy schema for testing"
    
    def _generate_llm_message(self, messages):
        # Return a fixed dummy response with a SQL code block.
        return """```sql
-- Purpose: Dummy test query
SELECT * FROM dummy_table;
```"""

class TestAgent(unittest.TestCase):
    def test_extract_sql_query_and_comment(self):
        dummy_queue = SharedQueue()
        generator = DummyAIQueryGenerator("dummy_connection", dummy_queue)
        dummy_response = generator._generate_llm_message([])
        query, comment = generator._extract_sql_query_and_comment(dummy_response)
        self.assertIn("SELECT * FROM dummy_table;", query)
        self.assertEqual(comment, "Dummy test query")
    
    def test_generate_queries_queues_messages(self):
        dummy_queue = SharedQueue()
        generator = DummyAIQueryGenerator("dummy_connection", dummy_queue)
        generator.generate_queries("Test goal", max_queries=2)
        messages = []
        while not dummy_queue.empty():
            messages.append(dummy_queue.get())
        self.assertEqual(len(messages), 2)
        for msg in messages:
            self.assertIn("SELECT * FROM dummy_table;", msg.query)
            self.assertEqual(msg.comment, "Dummy test query")

if __name__ == '__main__':
    unittest.main()
