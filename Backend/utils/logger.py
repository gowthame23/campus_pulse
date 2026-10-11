import logging
import os
import sys

# Ensure logs directory exists
LOGS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
)
os.makedirs(LOGS_DIR, exist_ok=True)

# Application log file path
LOG_FILE = os.path.join(LOGS_DIR, "application.log")

# Create logger
logger = logging.getLogger("campus_pulse")
logger.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")

# File Handler
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console Handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def get_logger(name):
    # Return a child logger with the specified name
    return logger.getChild(name)
