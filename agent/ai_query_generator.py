"""
Module: ai_query_generator
This module defines the AIQueryGenerator class which uses an LLM to generate SQL queries based on a given goal
and discovered database schema. It logs each query to a file and places them as QueryMessage objects on a shared queue.
"""

from pathlib import Path
import re
import psycopg2
import logging
from typing import Dict, List

from utils.global_utils import extract_fenced_code, current_timestamp
from queue_manager.query_message import QueryMessage
from queue_manager.shared_queue import SharedQueue
from agent.base_ai_agent import BaseAIAgent

logger = logging.getLogger(__name__)


class AIQueryGenerator(BaseAIAgent):
    """
    Generates Postgres-like SQL queries using an LLM and places them onto a shared queue.
    Inherits common OpenAI functionality from BaseAIAgent.
    """

    def __init__(
        self,
        connection_string: str,
        shared_queue: SharedQueue,
        logs_dir: str = "logs/sql",
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
    ):
        # Initialize common AI client functionality.
        super().__init__(model_name, temperature)
        self.connection_string = connection_string
        self.shared_queue = shared_queue
        # Initialize logs_dir as a Path object and ensure it exists.
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        # Clean up existing query files in logs_dir
        for file in self.logs_dir.glob("query_*.sql"):
            file.unlink()
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

    def generate_response(self, input_data: List[dict]) -> str:
        """
        Implements the abstract method from BaseAIAgent.
        Here, input_data is expected to be a list of messages.
        """
        response = self.client.responses.create(
            model=self.model_name,
            input=input_data,
            temperature=self.temperature,
            max_output_tokens=1500
        )
        logger.debug(f"openai response: {response.output[0].content[0].text}")
        return response.output[0].content[0].text.strip()

    def _generate_llm_message(self, messages: List[dict]) -> str:
        # Delegate to the common generate_response method.
        return self.generate_response(messages)

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
        # Use a simplified filename without timestamp
        filename = f"query_{index}.sql"
        filepath = self.logs_dir / filename
        filepath.write_text(f"-- {comment}\n{query}\n", encoding="utf-8")
        logger.info("Logged query #%d to file: %s", index, filename)

    def generate_queries(self, goal: str, num_queries: int):
        """
        Generates a specified number of queries based on the provided goal, 
        logs each query, and places them on the shared queue.
        """
        system_prompt = f"""
You are an expert data scientist and SQL specialist. You have the following schema:

{self.schema_text}

The user's goal is: {goal}

IMPORTANT: Generate ONLY ONE query per prompt that references ONLY the columns and tables listed in the schema above. Do NOT introduce any columns or tables that are not present in the schema. Ensure that the SQL is valid SQL.
Generate a valid SQL query, using the Postgres syntax, that is complex and, if applicable, involves multiple joins.
Include a short comment (like '-- Purpose: ...') as the first line inside a fenced SQL code block:
```sql
-- Purpose: ...
SELECT ...
```
        """.strip()
        
        for i in range(1, num_queries + 1):
            messages = [{"role": "system", "content": system_prompt}]
            user_prompt = "Please provide one SQL query in a fenced code block."
            messages.append({"role": "user", "content": user_prompt})
            llm_output = self._generate_llm_message(messages)
            logger.debug("LLM output for query %d: %s", i, llm_output)
            query_str, comment = self._extract_sql_query_and_comment(llm_output)
            if not query_str.strip():
                logger.warning("No SQL found in LLM output for query %d; skipping.", i)
                continue
            self._log_query_to_file(query_str, comment, i)
            msg = QueryMessage(query=query_str, comment=comment)
            self.shared_queue.put(msg)
            logger.info("Placed query #%d on shared queue: %s", i, msg)
        logger.info("Finished generating %d queries.", num_queries)

    def __del__(self):
        """
        Cleanup the stored OpenAI client if necessary.
        """
        if hasattr(self, 'client'):
            del self.client


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
