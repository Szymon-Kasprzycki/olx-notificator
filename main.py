import asyncio
import json
import logging
# from db_connector import DBConnector
from log import LogFileHandler, LogStreamHandler
from monitor import OlxUrlMonitor
from log import prepare_logger

# Init logger
# logger = logging.getLogger()
# logger.setLevel('DEBUG')
# ch = LogStreamHandler()
# logger.addHandler(ch)
# fh = LogFileHandler()
# logger.addHandler(fh)
logger = prepare_logger()

URL_TO_MONITOR = 'https://www.olx.pl/d/motoryzacja/czesci-samochodowe/osobowe/q-lampy-golf-4-soczewka/#?search%5Border%5D=created_at:desc&search%5Bfilter_enum_type%5D%5B0%5D=oswietlenie'


# Get config to the variable
with open('config.json', 'r', encoding='utf-8') as config_file:
    config = json.load(config_file)

url_monitor = OlxUrlMonitor(refresh_time=config['page_refresh_time'])

logger.info('Script loaded successfully')

url_monitor.add_url(url=URL_TO_MONITOR, title="TEST")

#url_monitor._check_search(url=URL_TO_MONITOR, case_id=123)

#
# WINDOW_LAYOUT = [
#
# ]
#
# window = PySimpleGUIQt.Window(title='OLX search observer',
#                               layout=WINDOW_LAYOUT,
#                               resizable=False,
#                               size=(400, 200))
# while True:
#     event, values = window.read()
#     if event in (None, 'OK'):
#         break
#     else:
