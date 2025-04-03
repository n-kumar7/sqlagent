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
from agent.base_ai_agent import BaseAIAgent

logger = logging.getLogger(__name__)

class QueryRunner(BaseAIAgent):
    """
    Executes queries from a shared queue concurrently.
    Inherits common OpenAI and schema discovery functionality from BaseAIAgent.
    """
    def __init__(
        self,
        connection_string: str,
        shared_queue: SharedQueue,
        logs_dir: str = "logs/runner",
        concurrency: int = 5,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.0,  # Validator uses low temperature for determinism
    ):
        # Initialize common AI functionality.
        super().__init__(model_name, temperature)
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

    def get_schema_context(self) -> str:
        """
        Retrieves schema context using BaseAIAgent shared methods.
        """
        schema_dict = self._discover_schema(self.connection_string)
        return self._format_schema_for_prompt(schema_dict)

    def validate_query(self, query: str, comment: str) -> bool:
        """
        Evaluates the SQL query for validity and logical sense using the responses API.
        Incorporates the current database schema context.
        """
        schema_context = self.get_schema_context()
        prompt = (
            f"Using the following schema context:\n{schema_context}\n\n"
            f"Is the following SQL query valid and does it make sense? Answer YES or NO.\n\n"
            f"Query:\n{query}\n\nComment:\n{comment}"
        )
        try:
            response_text = self.generate_response([{"role": "user", "content": prompt}])
            logger.debug(f"Validation response: {response_text}")
            answer = response_text.strip().upper()
            if answer == "YES":
                return True
            else:
                logger.warning("Query validation failed: %s", answer)
                return False
        except Exception as e:
            logger.error("Error during query validation: %s", e)
            return False

    def generate_response(self, input_data: List[dict]) -> str:
        """
        Implements the abstract method from BaseAIAgent.
        Uses the OpenAI Responses API to generate a short answer.
        """
        response = self.client.responses.create(
            model=self.model_name,
            input=input_data,
            temperature=self.temperature,
            max_output_tokens=1500  # increased from 10 to meet minimum requirement
        )
        logger.debug(f"openai response: {response.output[0].content[0].text}")
        return response.output[0].content[0].text.strip()

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
