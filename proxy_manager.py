import random

import cloudscraper
from ThreadingPool import ThreadPool
import logging
import requests
from bs4 import BeautifulSoup
from log import LogFileHandler, LogStreamHandler

logger = logging.getLogger()
logger.setLevel('INFO')
ch = LogStreamHandler()
logger.addHandler(ch)
fh = LogFileHandler()
logger.addHandler(fh)


class ProxyManager:
    def __init__(self):
        self.proxies = []
        self._proxies_to_remove = []
        self.working_count: int
        self.logger = logging.getLogger()
        self._get_session()
        self.logger.debug('Proxy manager initialised')
        self.get_new_proxies()

    def _get_session(self):
        s = requests.Session()
        self.session = cloudscraper.create_scraper(s)

    def _check_proxy(self, proxy: dict):
        proxies = {
            "http": f"http://{proxy['ip']}:{proxy['port']}/",
            "https": f"http://{proxy['ip']}:{proxy['port']}/"
        }
        url = 'https://api.ipify.org'

        try:
            response = requests.get(url, proxies=proxies, timeout=5)
            assert response.text == proxy['ip']
        except:
            self._proxies_to_remove.append(proxy)

    # TODO make a loop to validate proxies
    def _validate_proxies(self):
        pool = ThreadPool(100)
        for p in self.proxies:
            pool.add_task(self._check_proxy, p)
        pool.wait_completion()
        self.logger.debug(f'TOTAL VALID PROXIES: {len(self.proxies) - len(self._proxies_to_remove)}')

    # TODO make a loop to remove broken proxies
    def _remove_broken_proxies(self):
        self.proxies = [x for x in self.proxies if x not in self._proxies_to_remove]

    def get_new_proxies(self):
        try:
            url = 'https://free-proxy-list.net/'
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            proxies_data = soup.find('textarea', attrs={'readonly': 'readonly'}).text
            proxies_data = proxies_data.split('\n')
            self.proxies = [
                {'ip': address.split(':')[0], 'port': address.split(':')[1]} for address in proxies_data[3:-1]
            ]
            self._validate_proxies()
        except Exception as e:
            self.logger.exception(f'Cannot download new proxies, error: {e}')

    def get_random_proxy(self):
        return random.choice(self.proxies)

    def remove_broken_proxy(self, proxy: dict):
        self.proxies.remove(proxy)

# TESTS
# if __name__ == '__main__':
#     pm = ProxyManager()
#     pm.get_new_proxies()
