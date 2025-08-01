import datetime
import logging
import os

def log_function(file_name):
    current_time = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_folder = "Log Folder"
    os.makedirs(log_folder, exist_ok=True)
    
    log_file_path = os.path.join(log_folder, f"{file_name}_{current_time}.txt")
    
    # Create a custom logger
    logger = logging.getLogger("my_logger")
    logger.setLevel(logging.INFO)

    # Check if handlers are already added to avoid duplication
    if not logger.handlers:
        # File handler
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

    return logger