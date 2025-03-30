"""
Module: shared_queue
This module provides the SharedQueue class, a wrapper around a multiprocessing.Queue,
to enable inter-process communication.
"""

import multiprocessing
import logging

logger = logging.getLogger(__name__)

class SharedQueue:
    """
    A wrapper for a multiprocessing.Queue to allow easy adaptation and extension.
    """

    def __init__(self):
        """Initialize the shared queue."""
        self.queue = multiprocessing.Queue()
        self._size = 0  # Track the number of items in the queue
        logger.debug("Initialized SharedQueue with size %d", self._size)

    def put(self, item):
        """
        Put an item onto the queue.

        :param item: The item to place on the queue.
        """
        self.queue.put(item)
        self._size += 1
        logger.debug("Item added to queue. New size: %d", self._size)

    def get(self, block=True, timeout=None):
        """
        Retrieve an item from the queue.

        :param block: Whether to block until an item is available.
        :param timeout: Timeout in seconds if blocking.
        :return: The item from the queue.
        """
        item = self.queue.get(block, timeout)
        if self._size > 0:  # Safeguard against going negative
            self._size -= 1
        logger.debug("Item removed from queue. New size: %d", self._size)
        return item

    def empty(self) -> bool:
        """
        Check if the queue is empty.

        :return: True if the queue is empty, False otherwise.
        """
        return self._size == 0
