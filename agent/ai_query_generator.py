"""
Module: ai_query_generator
This module defines the AIQueryGenerator class which uses an LLM to generate SQL queries based on a given goal
and discovered database schema. It logs each query to a file and places them as QueryMessage objects on a shared queue.
"""

from pathlib import Path
import re
import psycopg2
import openai
import logging
from typing import Dict, List

from utils.global_utils import extract_fenced_code, current_timestamp
from queue_manager.query_message import QueryMessage
from queue_manager.shared_queue import SharedQueue

logger = logging.getLogger(__name__)


class AIQueryGenerator:
    """
    Generates Postgres-like SQL queries using an LLM and places them onto a shared queue.
    """

    def __init__(
        self,
        connection_string: str,
        shared_queue: SharedQueue,
        logs_dir: str = "logs/sql",
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
    ):
        """
        Initialize the AIQueryGenerator.

        :param connection_string: Postgres connection string.
        :param shared_queue: An instance of SharedQueue for inter-process communication.
        :param logs_dir: Directory where SQL files will be logged.
        :param model_name: The OpenAI model name to use.
        :param temperature: Sampling temperature for the LLM.
        """
        self.connection_string = connection_string
        self.shared_queue = shared_queue
        # Initialize logs_dir as a Path object and ensure it exists.
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.model_name = model_name
        self.temperature = temperature

        try:
            self.conn = psycopg2.connect(self.connection_string)
            self.conn.autocommit = True
            logger.info("Connected to database successfully.")
        except Exception as e:
            logger.error("Database connection failed: %s", e)
            raise

        self.schema_dict = self._discover_schema()
        self.schema_text = self._format_schema_for_prompt(self.schema_dict)

    def _discover_schema(self) -> Dict[str, List[str]]:
        """
        Discovers the database schema by querying the INFORMATION_SCHEMA.

        :return: A dictionary mapping full table names to lists of columns.
        """
        schema_dict = {}
        query = """
            SELECT table_schema, table_name, column_name
            FROM information_schema.columns
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY table_schema, table_name, ordinal_position
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
        for (schema, table, column) in rows:
            full_name = f"{schema}.{table}"
            schema_dict.setdefault(full_name, []).append(column)
        logger.info("Discovered schema with %d tables.", len(schema_dict))
        return schema_dict

    def _format_schema_for_prompt(self, schema_dict: Dict[str, List[str]]) -> str:
        """
        Formats the schema dictionary into a string for the LLM prompt.

        :param schema_dict: The schema dictionary.
        :return: A string representation of the schema.
        """
        lines = []
        for table, cols in schema_dict.items():
            lines.append(f"Table: {table}\n  Columns: {', '.join(cols)}\n")
        return "\n".join(lines)

    def _generate_llm_message(self, messages: List[dict]) -> str:
        """
        Calls the OpenAI ChatCompletion API with the provided messages.

        :param messages: A list of message dictionaries for the LLM.
        :return: The response text from the LLM.
        """
        logger.debug("Sending message to LLM with %d messages.", len(messages))
        response = openai.ChatCompletion.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
        )
        return response["choices"][0]["message"]["content"]

    def _extract_sql_query_and_comment(self, llm_output: str):
        """
        Extracts the SQL query and its purpose comment from the LLM output.

        Expected format in a fenced code block:
            ```sql
            -- Purpose: <description>
            SELECT ...
            ```

        :param llm_output: The output text from the LLM.
        :return: A tuple (query, comment).
        """
        logger.debug("Extracting SQL query and comment from LLM output: %s", llm_output)
        # If no fenced code block is in the output, treat it as no SQL.
        if "```" not in llm_output:
            logger.debug("No code fence found in LLM output.")
            return "", "No purpose comment provided by LLM"
        text = extract_fenced_code(llm_output, language="sql")
        if not text.strip():
            logger.debug("Fenced code is empty.")
            return "", "No purpose comment provided by LLM"
        lines = text.splitlines()
        comment = None
        query_lines = []
        for line in lines:
            if line.strip().startswith("--") and comment is None:
                comment = line.strip().lstrip("-").strip()
                # Strip "Purpose: " prefix if present
                if comment.lower().startswith("purpose:"):
                    comment = comment[len("purpose:"):].strip()
            else:
                query_lines.append(line)
        if not comment:
            comment = "No purpose comment provided by LLM"
        query = "\n".join(query_lines).strip()
        logger.debug("Extracted query: '%s', comment: '%s'", query, comment)
        return query, comment

    def _log_query_to_file(self, query: str, comment: str, index: int):
        """
        Logs the generated query to a SQL file.

        :param query: The SQL query string.
        :param comment: A brief comment describing the query.
        :param index: The sequential index of the query.
        """
        timestamp = current_timestamp()
        filename = f"query_{index}_{timestamp}.sql"
        filepath = self.logs_dir / filename
        filepath.write_text(f"-- {comment}\n{query}\n", encoding="utf-8")
        logger.info("Logged query #%d to file: %s", index, filename)

    def generate_queries(self, goal: str, max_queries: int = 10):
        """
        Generates queries based on the provided goal, logs them, and places them on the shared queue.

        :param goal: The user-defined goal for query generation.
        :param max_queries: Maximum number of queries to generate.
        """
        system_prompt = f"""
You are an expert data scientist and SQL specialist. You have the following schema:

{self.schema_text}

The user's goal is: {goal}

Generate multiple Postgres-like queries to explore or analyze data relevant to this goal.
Include a short comment (like '-- Purpose: ...') at the start of each query in a fenced code block:
    ```sql
    -- Purpose: ...
    SELECT ...
    ```
When you are done, respond with "DONE" (outside any code block).
        """.strip()

        messages = [{"role": "system", "content": system_prompt}]
        query_count = 0
        while query_count < max_queries:
            user_prompt = (
                "Please provide your next SQL query in a fenced code block, "
                "or say DONE if you have no more queries."
            )
            messages.append({"role": "user", "content": user_prompt})
            llm_output = self._generate_llm_message(messages)
            messages.append({"role": "assistant", "content": llm_output})
            logger.debug("LLM output: %s", llm_output)
            if "DONE" in llm_output.upper():
                logger.info("LLM indicated it is done generating queries.")
                break
            query_str, comment = self._extract_sql_query_and_comment(llm_output)
            if not query_str.strip():  # Skip if the query is empty
                logger.warning("No SQL found in LLM output; stopping query generation.")
                break
            logger.debug("Placing query onto queue: %s", query_str)
            query_count += 1
            self._log_query_to_file(query_str, comment, query_count)
            msg = QueryMessage(query=query_str, comment=comment)
            self.shared_queue.put(msg)
            logger.info("Placed query #%d on shared queue: %s", query_count, msg)
        logger.info("Finished generating %d queries.", query_count)


def main():
    """
    Main function for testing the AIQueryGenerator directly.
    """
    import openai
    openai.api_key = "YOUR_OPENAI_API_KEY"
    from queue_manager.shared_queue import SharedQueue
    shared_q = SharedQueue()
    connection_str = "postgresql://user:pass@localhost:5432/mydb"
    generator = AIQueryGenerator(connection_str, shared_q)
    generator.generate_queries("Analyze customer order patterns", max_queries=5)
    while not shared_q.empty():
        msg = shared_q.get()
        print("Queue item:", msg)


if __name__ == "__main__":
    main()
