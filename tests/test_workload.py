# tests/test_workload.py

import unittest
from queue_manager.shared_queue import SharedQueue
from queue_manager.query_message import QueryMessage
from workload.query_runner import QueryRunner

# Create a dummy subclass for QueryRunner that bypasses actual DB calls.
class DummyQueryRunner(QueryRunner):
    def __init__(self, connection_string, shared_queue, logs_dir="logs/runner", concurrency=1, steady_state_queries=None, steady_state_interval=0.1):
        self.connection_string = connection_string
        self.shared_queue = shared_queue
        self.logs_dir = logs_dir
        self.concurrency = concurrency
        self.steady_state_queries = steady_state_queries or []
        self.steady_state_interval = steady_state_interval
        self._stop_steady_state = False

    def _execute_query(self, query_str, comment):
        # Simulate query execution by returning a dummy message.
        return f"Dummy executed: {comment}"

class TestWorkload(unittest.TestCase):
    def test_run_concurrent_queries(self):
        shared_queue = SharedQueue()
        # Place two dummy query messages in the queue.
        shared_queue.put(QueryMessage("SELECT * FROM dummy;", "Dummy query 1"))
        shared_queue.put(QueryMessage("SELECT 1;", "Dummy query 2"))
        runner = DummyQueryRunner("dummy_connection", shared_queue, concurrency=2)
        results = runner.run_concurrent_queries(timeout=2)
        self.assertEqual(len(results), 2)
        self.assertTrue(all("Dummy executed:" in res for res in results))
    

if __name__ == '__main__':
    unittest.main()
