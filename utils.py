# Logger class for easier management of messages at different levels
class Logger:
    LEVELS = {
        "DEBUG": 1,
        "INFO": 2,
        "WARNING": 3,
        "ERROR": 4
    }

    def __init__(self, level):
        self.level = self.LEVELS.get(level.upper(), 2)

    # Log a message if its level is equal to or higher than the configured log level
    def log(self, message, level="INFO"):
        if self.LEVELS.get(level.upper(), 2) >= self.level:
            print(f"[{level}] {message}")

