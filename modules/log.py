import logging

FILE_LOGGING_LEVEL = 'DEBUG'
CONSOLE_LOGGING_LEVEL = 'DEBUG'


class LogStreamHandler(logging.StreamHandler):
    def __init__(self):
        logging.StreamHandler.__init__(self)
        fmt = '%(asctime)s %(filename)-18s %(levelname)-8s: %(message)s'
        fmt_date = '%Y-%m-%d %T'
        formatter = logging.Formatter(fmt, fmt_date)
        self.setFormatter(formatter)
        self.setLevel(CONSOLE_LOGGING_LEVEL)


class LogFileHandler(logging.FileHandler):
    def __init__(self):
        with open('logs.log', 'w+', encoding='utf-8') as f:
            f.write('')
        logging.FileHandler.__init__(self, 'logs.log')
        fmt = '%(asctime)s %(filename)-18s %(levelname)-8s: %(message)s'
        fmt_date = '%Y-%m-%d %T'
        formatter = logging.Formatter(fmt, fmt_date)
        self.setFormatter(formatter)
        self.setLevel(FILE_LOGGING_LEVEL)


def prepare_logger() -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel('DEBUG')
    ch = LogStreamHandler()
    logger.addHandler(ch)
    fh = LogFileHandler()
    logger.addHandler(fh)
    return logger