import time


class Logger:
    def __init__(self, filename='log.txt', max_size=10240, use_file=True):
        self.filename = filename
        self.max_size = max_size
        self.use_file = use_file
        self.buf = []
        self.size = 0

    def _get_timestamp(self) -> str:
        year, month, day, _, hour, minute, second, _ = time.localtime()
        return ("{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".
                format(year, month, day, hour, minute, second))

    def info(self, message: str) -> None:
        line = f"[{self._get_timestamp()}] {message}\n"

        if self.use_file:
            # Add to buffer
            self.buf.append(line)
            self.size += len(line)

            # Drop old entries if too big
            while self.size > self.max_size and len(self.buf) > 1:
                old = self.buf.pop(0)
                self.size -= len(old)

            # Write to file
            try:
                with open(self.filename, 'w') as f:
                    f.write(''.join(self.buf))
            except:
                pass
        else:
            print(line, end='')

    def to_file(self):
        self.use_file = True

    def to_console(self):
        self.use_file = False


# Global logger instance.
# This can be used in multiple modules.
logger = None

def init_logger(filename='log.txt', max_size=10240, use_file=True):
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
