import os
from datetime import datetime

class SimpleLogger:
    """
    A simple logger class to write timestamped messages to a log file with log levels.
    """

    # Define log levels
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'

    def __init__(self, log_file_path: str) -> None:
        """
        Initialize the SimpleLogger with a path to the log file.

        :param log_file_path: Path to the log file where messages will be logged.
        """
        self.log_file_path = log_file_path
        # Ensure the directory exists
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    def write_log(self, message: str, level: str = INFO) -> None:
        """
        Write a message to the log file with a timestamp and log level.

        :param message: The message to log.
        :param level: The level of the log (INFO, WARNING, ERROR).
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}\n"
        with open(self.log_file_path, 'a') as log_file:
            log_file.write(log_message)

    def filter_logs_by_level(self, level: str) -> list[str]:
        """
        Filter and return log messages by the specified log level.

        :param level: The level to filter logs by (INFO, WARNING, ERROR).
        :return: A list of log messages that match the specified level.
        """
        filtered_logs = []
        with open(self.log_file_path, 'r') as log_file:
            for line in log_file:
                if f"[{level}]" in line:
                    filtered_logs.append(line.strip())
        return filtered_logs
