import openai
import logging
import psycopg2

logger = logging.getLogger(__name__)

class BaseAIAgent:
    """
    Base AI Agent that encapsulates common functionality for interfacing with the OpenAI API.
    Provides shared schema discovery methods.
    """
    def __init__(self, model_name: str, temperature: float = 0.7):
        self.model_name = model_name
        self.temperature = temperature
        self.client = openai.OpenAI()  # Create and store the client once during construction

    def generate_response(self, input_data) -> str:
        """
        Abstract method to generate a response given input_data.
        Subclasses should override this method.
        """
        raise NotImplementedError("Subclasses must implement generate_response.")

    def _discover_schema(self, connection_string: str) -> dict:
        """
        Retrieves the database schema from INFORMATION_SCHEMA.
        """
        schema_dict = {}
        query = """
            SELECT table_schema, table_name, column_name
            FROM information_schema.columns
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY table_schema, table_name, ordinal_position
        """
        try:
            with psycopg2.connect(connection_string) as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    rows = cur.fetchall()
            for (schema, table, column) in rows:
                full_name = f"{schema}.{table}"
                schema_dict.setdefault(full_name, []).append(column)
            return schema_dict
        except Exception as e:
            logger.error("Schema discovery failed: %s", e)
            return {}

    def _format_schema_for_prompt(self, schema_dict: dict) -> str:
        """
        Formats the schema dictionary into a string for LLM context.
        """
        lines = []
        for table, cols in schema_dict.items():
            lines.append(f"Table: {table}\n  Columns: {', '.join(cols)}\n")
        return "\n".join(lines)

    def __del__(self):
        if hasattr(self, 'client'):
            del self.client
