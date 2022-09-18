import logging
import time

import bs4
import re
import json
import random
from datetime import datetime
from requests import Response
from db_connector import DBConnector
from proxy_manager import ProxyManager
from exceptions import *
import cloudscraper

##########################################################

# DEBUG
with open('credentials.json', 'r', encoding='utf-8') as f:
    auth = json.load(f)


##########################################################

class BaseConnectionClass:
    def __init__(self):
        self.logger = logging.getLogger()
        self.db_connector = DBConnector(credentials=auth)
        self.proxy_manager = ProxyManager()
        time.sleep(3)
        self._get_new_session()

    def _get_new_session(self):
        self.session = cloudscraper.create_scraper(interpreter='V8')
        proxy = self.proxy_manager.get_random_proxy()
        self.session.proxies = {
            'http': f'http://{proxy["ip"]}:{proxy["port"]}',
            'https': f'http://{proxy["ip"]}:{proxy["port"]}'
        }


class ABCMonitor(BaseConnectionClass):
    """
    Base object to allow monitoring changes in products for given urls
    """

    def __init__(self, refresh_time: int):
        super(ABCMonitor, self).__init__()
        self.refresh_time = refresh_time
        self.url_list = []
        self.logger.debug('URL Monitor has been successfully initialised')
        # self._get_user_agents()

    # def _get_user_agents(self):
    #     """
    #     This function reads web user agents from txt file in utils folder.
    #     """
    #     with open('utils/user-agents.txt', 'r', encoding='utf-8') as f:
    #         self.user_agents = [line.strip().replace('\n', '') for line in f.readlines()]
    #         self.logger.info(f'Read {len(self.user_agents)} user agents from txt file.')
    # 
    # def _get_random_user_agent(self):
    #     return random.choice(self.user_agents)

    def _add_url(self, url: str, title: str):
        """
        This function allows to add new OLX web address to monitor new items there
        :param url: link to the search page
        :param title: record name
        """
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$',
            re.IGNORECASE
        )
        if re.match(regex, url) is not None:
            self.url_list.append(
                {
                    'title': title,
                    'url': url,
                    'time_added': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                    'last_updated': 'none',
                }
            )


class OlxUrlMonitor(ABCMonitor):
    def __init__(self, refresh_time: int):
        super().__init__(refresh_time)

    @staticmethod
    def _prepare_url(url: str):
        """
        This function makes change to the OLX search URL to use it properly in the script
        :param url: web address to be checked as string
        :return: ready url as string
        """
        if 'search%5Border%5D=' in url:
            to_replace = None
            if '=filter_float_price:asc' in url:
                to_replace = '=filter_float_price:asc'
            elif '=filter_float_price:desc' in url:
                to_replace = '=filter_float_price:desc'
            elif '=relevance:desc' in url:
                to_replace = '=relevance:desc'

            if to_replace:
                url.replace(to_replace, '=created_at:desc')

        elif '/?' in url:
            url += '&search%5Border%5D=created_at:desc'

        else:
            url += '/?search%5Border%5D=created_at:desc'

        return url

    def add_url(self, url: str, title: str):
        url = self._prepare_url(url)
        self._add_url(url=url, title=title)

    @staticmethod
    def _check_search_complete(response: str):
        soup = bs4.BeautifulSoup(response)
        elem_nav_1 = soup.find('h1', attrs={
            'class': 'c-container__title'
        })
        elem_nav_2 = soup.find('p', attrs={
            'class': 'c-container__description'
        })
        elem_succes = soup.find('div', attrs={'data-testid': 'total-count'})
        if elem_nav_1 and elem_nav_2:
            if 'wygląda na to, że używasz nieaktualnej wersji przeglądarki' in elem_nav_1.text.lower() and \
                    'aby nadal korzystać z OLX, przejdź do ustawień przeglądarki i zaktualizuj ją do najnowszej wersji.' \
                    in elem_nav_2.text.lower():
                raise RequestResponseInterrupted('Too old browser is being used. Try something newer.')
        elif 'znaleźliśmy' in elem_succes.text.lower():
            pass
        else:
            raise RequestResponseInterrupted('Unknown error occurred, page was not loaded properly.')

    @staticmethod
    def _get_products_from_search(search: Response):
        soup = bs4.BeautifulSoup(search.text, 'html.parser')
        products = soup.find_all('div', attrs={'class': 'css-19ucd76'}, recursive=True)
        for prod in products:
            link_button = prod.find('a', attrs={'class': 'css-1bbgabe'})
            if link_button:
                yield link_button.get('href')

    def _get_product_info(self, olx_href: str):
        url = f'https://olx.pl{olx_href}'
        response = self.session.get(url)

    # TODO insert products to db, and the rest of logic of checking products
    def _check_search(self, url: str):
        self._get_new_session()
        try:
            response = self.session.get(url)
            self._check_search_complete(response.text)
            hrefs = self._get_products_from_search(response)
            # products = []
            # for link in hrefs:

        except TimeoutError:
            self.logger.exception(
                f'Proxy `{self.session.proxies["http"]}` has been timed out. Retrying with different one...')
            self._check_search(url)

        except RequestResponseInterrupted as e:
            self.logger.exception(f'Request failed. Reason: `{e.reason}`. Retrying...')
            self._check_search(url)


class OlxProduct(BaseConnectionClass):
    def __init__(self, url: str):
        super().__init__()
        self.link = url
        self.title = ''
        self.id = ''
        self.session = None
        self._get_new_session()

    def get_product_data(self):
        soup = None
        try:
            product_data = self.session.get(self.link)
            soup = bs4.BeautifulSoup(product_data)
            elem_nav_1 = soup.find('h1', attrs={
                'class': 'c-container__title'
            })
            elem_nav_2 = soup.find('p', attrs={
                'class': 'c-container__description'
            })
            elem_succes = soup.find('div', attrs={'data-cy': 'ad_description'}).find('h3', attrs={
                'class': 'css-1m9lat4-Text'})
            if elem_nav_1 and elem_nav_2:
                if 'wygląda na to, że używasz nieaktualnej wersji przeglądarki' in elem_nav_1.text.lower() and \
                        'aby nadal korzystać z OLX, przejdź do ustawień przeglądarki i zaktualizuj ją do najnowszej wersji.' \
                        in elem_nav_2.text.lower():
                    raise RequestResponseInterrupted('Too old browser is being used. Try something newer.')
            elif 'opis' in elem_succes.text.lower():
                pass
            else:
                raise RequestResponseInterrupted('Unknown error occurred, page was not loaded properly.')

        except TimeoutError:
            self.logger.exception(
                f'Proxy `{self.session.proxies["http"]}` has been timed out. Retrying with different one...')
        except RequestResponseInterrupted as e:
            self.logger.exception(f'Request failed. Reason: `{e.reason}`. Retrying...')

        self.title = soup.find('h1', attrs={'class': 'css-r9zjja-Text'}).text.strip()
        self.id = soup.find('div', attrs={'data-cy': 'ad-footer-bar-section'}).find('span', attrs={
            'class': 'css-9xy3gn-Text'}).text.strip().split(' ')[1]
