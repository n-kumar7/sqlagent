"""
Module: query_message
This module defines the QueryMessage class which encapsulates a SQL query and its associated purpose comment.
"""

class QueryMessage:
    """
    Represents a SQL query message with a brief purpose comment.
    """

    def __init__(self, query: str, comment: str):
        """
        Initialize a QueryMessage.

        :param query: The SQL query string.
        :param comment: A brief description of the query's purpose.
        """
        self.query = query
        self.comment = comment

    def __repr__(self):
        return f"QueryMessage(comment='{self.comment}', query='{self.query[:50]}...')"
