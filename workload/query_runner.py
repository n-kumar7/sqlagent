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
import openai
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from queue_manager.shared_queue import SharedQueue
from queue_manager.query_message import QueryMessage
from utils.global_utils import current_timestamp

logger = logging.getLogger(__name__)

class QueryRunner:
    """
    Executes queries from a shared queue concurrently.
    """

    def __init__(
        self,
        connection_string: str,
        shared_queue: SharedQueue,
        logs_dir: str = "logs/runner",
        concurrency: int = 5,
    ):
        """
        Initialize the QueryRunner.

        :param connection_string: Postgres connection string.
        :param shared_queue: SharedQueue instance from which queries are consumed.
        :param logs_dir: Directory to log execution details.
        :param concurrency: Number of worker threads for concurrent execution.
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
        return log_message

    def _get_schema_context(self) -> str:
        """
        Retrieves and formats the current database schema by querying the INFORMATION_SCHEMA.
        """
        schema_dict = {}
        query = """
            SELECT table_schema, table_name, column_name
            FROM information_schema.columns
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY table_schema, table_name, ordinal_position
        """
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    rows = cur.fetchall()
            for (schema, table, column) in rows:
                full_name = f"{schema}.{table}"
                schema_dict.setdefault(full_name, []).append(column)
            lines = [f"Table: {table}\n  Columns: {', '.join(cols)}\n" for table, cols in schema_dict.items()]
            return "\n".join(lines)
        except Exception as e:
            logger.error("Failed to retrieve schema context: %s", e)
            return "Schema context unavailable."

    def validate_query(self, query: str, comment: str) -> bool:
        """
        Evaluates the SQL query for validity and logical sense using OpenAI.
        Incorporates the current database schema context in the prompt.
        Returns True if the AI's answer is "YES", else False.
        """
        schema_context = self._get_schema_context()
        prompt = (
            f"Using the following schema context:\n{schema_context}\n\n"
            f"Is the following SQL query valid and does it make sense? Answer YES or NO.\n\n"
            f"Query:\n{query}\n\nComment:\n{comment}"
        )
        try:
            response = openai.Completion.create(
                model="gpt-3.5-turbo",
                prompt=prompt,
                temperature=0,
                max_tokens=10,
                n=1,
                stop=["\n"]
            )
            answer = response.choices[0].text.strip().upper()
            if answer == "YES":
                return True
            else:
                logger.warning("Query validation failed: %s", answer)
                return False
        except Exception as e:
            logger.error("Error during query validation: %s", e)
            return False

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
            # Validate the query before executing it.
            if not self.validate_query(query_msg.query, query_msg.comment):
                return f"Query skipped due to failed validation: {query_msg.comment}"
            return self._execute_query(query_msg.query, query_msg.comment)

        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            while (time.time() - start_time) < timeout:
                try:
                    query_msg = self.shared_queue.get(block=True, timeout=1)
                    future = executor.submit(worker, query_msg)
                    futures.append(future)
                except queue.Empty:
                    # Continue waiting until overall timeout is reached
                    continue
            for f in as_completed(futures):
                results.append(f.result())
        logger.info("All concurrent queries complete.")
        return results

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
    )
    results = runner.run_concurrent_queries(timeout=60.0)
    for r in results:
        print(r)

if __name__ == "__main__":
    main()
