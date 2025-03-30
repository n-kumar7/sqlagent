"""
Main entry point for the application.
This file contains only the high-level application logic for launching the app.
"""

import multiprocessing
from queue_manager.shared_queue import SharedQueue
from utils.global_utils import load_config, setup_logging, run_generator, run_runner

def main():
    # Initialize structured logging
    setup_logging()
    
    # Load configuration from JSON
    config = load_config()
    
    # Create a shared queue for inter-process communication
    shared_queue = SharedQueue()

    # Create separate processes for the AI query generator and the query runner
    generator_proc = multiprocessing.Process(target=run_generator, args=(config, shared_queue))
    runner_proc = multiprocessing.Process(target=run_runner, args=(config, shared_queue))
    
    # Start both processes
    generator_proc.start()
    runner_proc.start()
    
    # Wait for both processes to finish
    generator_proc.join()
    runner_proc.join()

    print("All processes complete.")

if __name__ == "__main__":
    main()
