"""
Module: query_runner
This module defines the QueryRunner class which consumes QueryMessage objects from a shared queue,
executes them concurrently against a Postgres database, and runs a steady-state workload.
"""

import os
import time
import queue
import logging
import psycopg2
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from queue_manager.shared_queue import SharedQueue
from queue_manager.query_message import QueryMessage
from utils.global_utils import current_timestamp

logger = logging.getLogger(__name__)

class QueryRunner:
    """
    Executes queries from a shared queue concurrently and runs a steady-state workload.
    """

    def __init__(
        self,
        connection_string: str,
        shared_queue: SharedQueue,
        logs_dir: str = "logs/runner",
        concurrency: int = 5,
        steady_state_queries: List[str] = None,
        steady_state_interval: float = 5.0,
    ):
        """
        Initialize the QueryRunner.

        :param connection_string: Postgres connection string.
        :param shared_queue: SharedQueue instance from which queries are consumed.
        :param logs_dir: Directory to log execution details.
        :param concurrency: Number of worker threads for concurrent execution.
        :param steady_state_queries: A list of queries for steady-state workload.
        :param steady_state_interval: Time in seconds between each steady-state execution.
        """
        self.connection_string = connection_string
        self.shared_queue = shared_queue
        self.logs_dir = logs_dir
        os.makedirs(self.logs_dir, exist_ok=True)
        logging.basicConfig(
            filename=os.path.join(self.logs_dir, "query_runner.log"),
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s | %(processName)s | %(message)s"
        )
        self.concurrency = concurrency
        self.steady_state_queries = steady_state_queries or []
        self.steady_state_interval = steady_state_interval
        self._stop_steady_state = False

    def _execute_query(self, query_str: str, comment: str) -> str:
        """
        Executes a single SQL query and logs the result.

        :param query_str: The SQL query to execute.
        :param comment: A brief description of the query's purpose.
        :return: A log message with execution details.
        """
        start = time.time()
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(query_str)
                    if cur.description:
                        rows = cur.fetchall()
                        sample = rows[:5]
                        message = f"Executed Query: {comment} | Sample: {sample}"
                    else:
                        message = f"Executed Query: {comment} | Rows affected: {cur.rowcount}"
        except Exception as e:
            message = f"Error executing query: {comment} - {e}"
        duration = time.time() - start
        log_message = f"[RUNNER] {message} | Duration: {duration:.2f}s | Query: {query_str}"
        logger.info(log_message)
        print(log_message)
        return log_message

    def run_concurrent_queries(self, timeout: float = 60.0) -> List[str]:
        """
        Consumes QueryMessage objects from the shared queue and executes them concurrently.

        :param timeout: Maximum time in seconds to run concurrent queries.
        :return: A list of log messages for executed queries.
        """
        start_time = time.time()
        futures = []
        results = []

        def worker(query_msg: QueryMessage):
            return self._execute_query(query_msg.query, query_msg.comment)

        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            while True:
                if (time.time() - start_time) > timeout:
                    logger.info("Timeout reached; stopping concurrent queries.")
                    break
                try:
                    query_msg = self.shared_queue.get(block=True, timeout=1)
                    future = executor.submit(worker, query_msg)
                    futures.append(future)
                except queue.Empty:
                    if self.shared_queue.empty():
                        break
            for f in as_completed(futures):
                results.append(f.result())
        logger.info("All concurrent queries complete.")
        return results

    def run_steady_state_workload(self):
        """
        Runs the steady-state workload continuously until signaled to stop.
        """
        logger.info("Starting steady-state workload with %d queries.", len(self.steady_state_queries))
        while not self._stop_steady_state:
            for query in self.steady_state_queries:
                self._execute_query(query, "steady state query")
            time.sleep(self.steady_state_interval)

    def stop_steady_state(self):
        """
        Signals the steady-state workload loop to stop.
        """
        self._stop_steady_state = True
        logger.info("Steady-state workload signaled to stop.")

def main():
    """
    Main function for testing the QueryRunner directly.
    """
    connection_str = "postgresql://user:pass@localhost:5432/mydb"
    from queue_manager.query_message import QueryMessage
    from queue_manager.shared_queue import SharedQueue
    shared_q = SharedQueue()
    shared_q.put(QueryMessage("SELECT * FROM public.orders LIMIT 10;", "Test ad-hoc query"))
    runner = QueryRunner(
        connection_string=connection_str,
        shared_queue=shared_q,
        concurrency=3,
        steady_state_queries=[
            "SELECT COUNT(*) FROM public.orders;",
            "SELECT AVG(total) FROM public.orders WHERE order_date >= NOW() - INTERVAL '1 day';"
        ],
        steady_state_interval=10.0
    )
    results = runner.run_concurrent_queries(timeout=60.0)
    for r in results:
        print(r)
    runner.stop_steady_state()

if __name__ == "__main__":
    main()
