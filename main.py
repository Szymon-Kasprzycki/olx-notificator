import json
import logging
from db_connector import DBConnector
from log import LogFileHandler, LogStreamHandler
from monitor import URLMonitor

# Init logger
logger = logging.getLogger()
logger.setLevel('DEBUG')
ch = LogStreamHandler()
logger.addHandler(ch)
fh = LogFileHandler()
logger.addHandler(fh)

# URL_TO_MONITOR = 'https://www.olx.pl/d/motoryzacja/czesci-samochodowe/osobowe/q-lampy-golf-4-soczewka/ \
#                  ?search%5Border%5D=created_at:desc&search%5Bfilter_enum_type%5D%5B0%5D=oswietlenie'

# Get config to the variable
with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)

url_monitor = URLMonitor(refresh_time=config['page_refresh_time'])

logger.info('Script run success')
