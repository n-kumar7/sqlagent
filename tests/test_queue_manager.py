# tests/test_queue_manager.py

import unittest
from queue_manager.query_message import QueryMessage
from queue_manager.shared_queue import SharedQueue

class TestQueueManager(unittest.TestCase):
    def test_query_message_repr(self):
        msg = QueryMessage("SELECT * FROM test_table;", "Test query")
        self.assertIn("Test query", repr(msg))
        self.assertIn("SELECT * FROM test_table;", repr(msg))
    
    def test_shared_queue(self):
        sq = SharedQueue()
        self.assertTrue(sq.empty(), "Queue should be empty initially")
        test_item = "test_item"
        sq.put(test_item)
        self.assertFalse(sq.empty(), "Queue should not be empty after putting an item")
        retrieved = sq.get()
        self.assertEqual(test_item, retrieved)
        self.assertTrue(sq.empty(), "Queue should be empty after retrieving the item")

if __name__ == '__main__':
    unittest.main()
