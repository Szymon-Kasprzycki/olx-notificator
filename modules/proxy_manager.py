import asyncio
import random
import cloudscraper
from ThreadingPool import ThreadPool
import logging
import requests
from bs4 import BeautifulSoup


class ProxyManager:
    """
    Class to manage proxy addresses and share it with other modules
    """
    def __init__(self, loop: asyncio.AbstractEventLoop = None) -> None:
        self.proxies = []
        self._proxies_to_remove = []
        self.loop_tasks = []
        self.working_count: int
        self.logger = logging.getLogger()
        self._get_session()
        #self.get_and_validate_proxies()
        self.loop = loop or asyncio.new_event_loop()
        self.loop_tasks.append(self.loop.create_task(self.get_and_validate_proxies()))
        self.loop_tasks.append(self.loop.create_task(self._remove_broken_proxies()))
        self.loop.create_task(self.get_and_validate_proxies())
        self.loop.create_task(self._remove_broken_proxies())
        self.logger.debug('Proxy manager initialised')
        if not loop:
           self.loop.run_forever()

    def _get_session(self) -> None:
        """
        Get new requests session

        :return: None
        """
        s = requests.Session()
        self.session = cloudscraper.create_scraper(s)
        self.logger.debug('Session for Proxy Manager was successfully created!')

    def _check_proxy(self, proxy: dict) -> None:
        """
        Check if proxy server is accessible and working

        :param proxy: dict["ip", "port"]
        :return: None
        """
        proxies = {
            "http": f"http://{proxy['ip']}:{proxy['port']}/",
            "https": f"http://{proxy['ip']}:{proxy['port']}/"
        }
        url = 'https://api.ipify.org'

        try:
            response = requests.get(url, proxies=proxies, timeout=5)
            assert response.text == proxy['ip']
        except Exception:
            self.logger.debug(f'Proxy {proxy["ip"]}:{proxy["port"]} is not workig, adding it to remove...')
            self._proxies_to_remove.append(proxy)

    async def get_and_validate_proxies(self):
        """
        Get new proxies from the internet and verify their status
        :return: None
        """
        while True:
            self.get_new_proxies()
            if len(self.proxies) > 0:
                pool = ThreadPool(100)
                for p in self.proxies:
                    pool.add_task(self._check_proxy, p)
                pool.wait_completion()
                self.logger.debug(f'[*] TOTAL VALID PROXIES: {len(self.proxies) - len(self._proxies_to_remove)}')
            await asyncio.sleep(240)

    async def _remove_broken_proxies(self) -> None:
        """
        Exclude not working proxy servers from Manager memory

        :return: None
        """
        while True:
            if len(self._proxies_to_remove) > 0:
                self.logger.debug(f'Removed {len(self._proxies_to_remove)} broken proxies!')
                self.proxies = [x for x in self.proxies if x not in self._proxies_to_remove]
                self._proxies_to_remove = []
            await asyncio.sleep(60)

    def get_new_proxies(self) -> None:
        """
        Download new proxy addresses from the internet.
        :return: None
        """
        try:
            url = 'https://free-proxy-list.net/'
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            proxies_data = soup.find('textarea', attrs={'readonly': 'readonly'}).text
            proxies_data = proxies_data.split('\n')[3:-1]
            self.logger.debug(f'Got {len(proxies_data)} proxies from web')
            self.proxies = [
                {'ip': address.split(':')[0], 'port': address.split(':')[1]} for address in proxies_data
            ]
        except Exception as e:
            self.logger.exception(f'Cannot download new proxies, error: {e}')

    def get_random_proxy(self) -> dict:
        """
        Get random proxy from Manager memory
        :return: dict["ip", "port"]
        """
        return random.choice(self.proxies)

    def remove_broken_proxy(self, proxy: dict) -> None:
        """
        Remove one proxy address from Manager's memory

        :param proxy: dict["ip", "port"]
        :return: None
        """
        self.proxies.remove(proxy)
        self.logger.debug(f'Removed one proxy from memory - {proxy["ip"]}:{proxy["port"]}')


# TESTS
if __name__ == '__main__':
    #from log import prepare_logger
    #logger = prepare_logger()
    #pm = ProxyManager()
    #pm.get_new_proxies()
    pass