"""
Module: shared_queue
This module provides the SharedQueue class, a wrapper around a multiprocessing.Queue,
to enable inter-process communication.
"""

import multiprocessing

class SharedQueue:
    """
    A wrapper for a multiprocessing.Queue to allow easy adaptation and extension.
    """

    def __init__(self):
        """Initialize the shared queue."""
        self.queue = multiprocessing.Queue()

    def put(self, item):
        """
        Put an item onto the queue.

        :param item: The item to place on the queue.
        """
        self.queue.put(item)

    def get(self, block=True, timeout=None):
        """
        Retrieve an item from the queue.

        :param block: Whether to block until an item is available.
        :param timeout: Timeout in seconds if blocking.
        :return: The item from the queue.
        """
        return self.queue.get(block, timeout)

    def empty(self) -> bool:
        """
        Check if the queue is empty.

        :return: True if the queue is empty, False otherwise.
        """
        return self.queue.empty()
