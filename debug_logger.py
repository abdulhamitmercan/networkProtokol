import logging
import os

class DebugLogger:
    LEVEL_NONE = 0
    LEVEL_ERROR = 1
    LEVEL_WARN = 2
    LEVEL_INFO = 3
    LEVEL_DEBUG = 4
    LEVEL_VERBOSE = 5
    
    FORMAT_MINIMAL = 0
    FORMAT_COMPACT = 1
    FORMAT_FILE_LINE = 2
    FORMAT_FULL = 3
    
    MAX_LOG_FILE_SIZE = 16 * 1024

    def __init__(self, level=LEVEL_INFO, format_type=FORMAT_FILE_LINE, log_file_path='app.log'):
        self.logger = logging.getLogger(__name__)
        self.set_level(level)
        self.set_format(format_type)

        # Log dosyasının yolunu belirle
        self.log_file_path = log_file_path
        
        # FileHandler ve StreamHandler oluşturulup eklenir
        self.file_handler = self.create_file_handler()
        self.stream_handler = logging.StreamHandler()
        
        self.file_handler.setFormatter(self.formatter)
        self.stream_handler.setFormatter(self.formatter)
        
        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(self.stream_handler)

    def set_level(self, level):
        levels = {
            self.LEVEL_NONE: logging.CRITICAL + 1,
            self.LEVEL_ERROR: logging.ERROR,
            self.LEVEL_WARN: logging.WARNING,
            self.LEVEL_INFO: logging.INFO,
            self.LEVEL_DEBUG: logging.DEBUG,
            self.LEVEL_VERBOSE: logging.DEBUG
        }
        self.logger.setLevel(levels.get(level, logging.INFO))

    def set_format(self, format_type):
        if format_type == self.FORMAT_MINIMAL:
            self.formatter = logging.Formatter('%(message)s')
        elif format_type == self.FORMAT_COMPACT:
            self.formatter = logging.Formatter('%(log_filename)s %(message)s')
        elif format_type == self.FORMAT_FILE_LINE:
            self.formatter = logging.Formatter('[%(levelname)s] %(log_filename)s: %(message)s')
        elif format_type == self.FORMAT_FULL:
            self.formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(log_filename)s - %(category)s - %(status)s - %(message)s')
        else:
            raise ValueError('Invalid format type')

    def create_file_handler(self):
        handler = logging.FileHandler(self.log_file_path)
        handler.setFormatter(self.formatter)
        return handler

    def check_and_reset_log_file(self):
        """Check the size of the log file and reset it if it exceeds the maximum size."""
        if os.path.exists(self.log_file_path):
            try:
                if os.path.getsize(self.log_file_path) > self.MAX_LOG_FILE_SIZE:
                    with open(self.log_file_path, 'w') as f:
                        f.truncate(0)  # Reset the file
            except OSError as e:
                self.logger.error(f"Error checking or resetting log file: {e}")

    def log(self, level, msg, filename='', category='', status='', *args, **kwargs):
        """Log a message with the given level, including extra information."""
        self.check_and_reset_log_file()
        
        log_func = {
            self.LEVEL_ERROR: self.logger.error,
            self.LEVEL_WARN: self.logger.warning,
            self.LEVEL_INFO: self.logger.info,
            self.LEVEL_DEBUG: self.logger.debug,
            self.LEVEL_VERBOSE: self.logger.debug
        }.get(level, self.logger.info)
        
        # Ensure extra parameters are valid
        extra = {
            'log_filename': filename if filename else 'unknown',
            'category': category if category else 'general',
            'status': status if status else 'no_status'
        }
        log_func(msg, *args, extra=extra, **kwargs)

    def error(self, msg, filename='', category='', status='', *args, **kwargs):
        self.log(self.LEVEL_ERROR, msg, filename, category, status, *args, **kwargs)

    def warn(self, msg, filename='', category='', status='', *args, **kwargs):
        self.log(self.LEVEL_WARN, msg, filename, category, status, *args, **kwargs)

    def info(self, msg, filename='', category='', status='', *args, **kwargs):
        self.log(self.LEVEL_INFO, msg, filename, category, status, *args, **kwargs)

    def debug(self, msg, filename='', category='', status='', *args, **kwargs):
        self.log(self.LEVEL_DEBUG, msg, filename, category, status, *args, **kwargs)

    def verbose(self, msg, filename='', category='', status='', *args, **kwargs):
        self.log(self.LEVEL_VERBOSE, msg, filename, category, status, *args, **kwargs)
