"""
Module: global_utils
This module provides global utility functions and application management routines for the project.
It also sets up structured logging for the entire application.
"""

import re
import datetime
import json
import logging
import logging.config
import os
import openai

def extract_fenced_code(text: str, language: str = "sql") -> str:
    """
    Extracts code from a fenced code block.

    :param text: The text containing a fenced code block.
    :param language: The language identifier for the fenced block (default is 'sql').
    :return: The extracted code as a string.
    """
    pattern = rf"```{language}(.*?)```"
    match = re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()

def current_timestamp() -> str:
    """
    Returns the current timestamp as a formatted string.

    :return: A string representing the current timestamp (YYYYMMDD_HH%M%S).
    """
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def load_config(config_file: str = "config/config.json") -> dict:
    """
    Loads the configuration from a JSON file.

    :param config_file: Path to the JSON configuration file.
    :return: A dictionary of configuration values.
    """
    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)

def setup_logging():
    """
    Sets up structured logging for the application using dictConfig.
    Logs include timestamp, log level, module name, process name, and message.
    """
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(processName)s | %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "structured",
                "level": "DEBUG",
            },
            "file": {
                "class": "logging.FileHandler",
                "formatter": "structured",
                "filename": "logs/app.log",
                "mode": "w",
                "level": "DEBUG",
            }
        },
        "root": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
        }
    }
    logging.config.dictConfig(logging_config)

def run_generator(config: dict, shared_queue):
    """
    Runs the AI query generator process.
    """
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    connection_str = config["db_connection"]
    goal = config.get("goal", "No goal specified")
    max_queries = config.get("max_ad_hoc_queries", 10)  # use config value, default to 10
    model_name = config.get("model_name", "gpt-3.5-turbo")  # configuration parameter used here
    # Import AIQueryGenerator here to break circular dependency
    from agent.ai_query_generator import AIQueryGenerator
    generator = AIQueryGenerator(connection_str, shared_queue, model_name=model_name)
    generator.generate_queries(goal=goal, num_queries=max_queries)

def run_runner(config: dict, shared_queue):
    """
    Runs the query runner process.
    
    :param config: The configuration dictionary.
    :param shared_queue: The shared queue for query messages.
    """
    connection_str = config["db_connection"]
    steady_cfg = config.get("steady_state_workload", {})
    steady_queries = steady_cfg.get("queries", [])
    steady_interval = steady_cfg.get("interval", 5.0)
    from workload.query_runner import QueryRunner
    runner = QueryRunner(
        connection_string=connection_str,
        shared_queue=shared_queue,
        concurrency=3,
        steady_state_queries=steady_queries,
        steady_state_interval=steady_interval
    )
    # Run the steady-state workload in a background thread.
    import threading
    steady_thread = threading.Thread(target=runner.run_steady_state_workload, daemon=True)
    steady_thread.start()
    # Run the ad-hoc queries concurrently.
    runner.run_concurrent_queries(timeout=60.0)
    runner.stop_steady_state()
    steady_thread.join()
