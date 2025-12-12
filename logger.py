import os
import time


class Logger:
    """
    This logger uses 2 files each with the max_size.
    Logger is toggling between these 2 files, and overwrite it each time.
    The max_size is approximate value, loger do not care about the precise size of file but is faster.
    """
    def __init__(self, filename="log.txt", max_size=10240, use_file=True):
        self._filename1 = "1" + filename
        self._filename2 = "2" + filename
        self.filename = self._filename1
        self.max_size = max_size
        self.use_file = use_file
        self._write_estimator = 0   # Compare integer instead of use os.stat to save time.
        self._mode = "a"
        self.buf = []
        self.size = self.get_size()

    def info(self, message: str) -> None:
        line = f"[{time.ticks_ms()}] {message}\n"
        if self.use_file:
            if self._write_estimator % 50 == 0 and self.get_size() > self.max_size:
                self.filename = self._filename1 if self.filename == self._filename2 else self._filename2
                self._mode = "w"
            else:
                self._mode = "a"
            with open(self.filename, self._mode) as f:
                f.write(line)
            self._write_estimator += 1
        else:
            print(line, end="")


    def to_file(self):
        self.use_file = True
        self.size = self.get_size()

    def to_console(self):
        self.use_file = False

    def get_size(self):
        if self.use_file:
            try:
                return os.stat(self.filename)[6]
            except OSError:
                return 0
        return 0

# Global logger instance.
# This can be used in multiple modules.
logger = None

def init_logger(filename="og.txt", max_size=10240, use_file=True):
    """Initialize global logger."""
    global logger
    logger = Logger(filename, max_size, use_file)
    return logger

def get_logger():
    """Get the global logger instance."""
    global logger
    if logger is None:
        logger = Logger()
    return logger
