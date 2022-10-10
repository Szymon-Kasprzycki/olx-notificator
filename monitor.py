import logging
import time
import bs4
import re
import json
from datetime import datetime
from requests import Response
from db_connector import DBConnector
from proxy_manager import ProxyManager
from notificator import Notificator
from exceptions import *
import cloudscraper

##########################################################

# DEBUG
with open('credentials.json', 'r', encoding='utf-8') as f:
    auth = json.load(f)


##########################################################

class BaseConnectionClass:
    """
    Base class for any modules using web connection
    """
    def __init__(self):
        self.logger = logging.getLogger()
        self.db_connector = DBConnector(credentials=auth)
        self.proxy_manager = ProxyManager()
        self.notificator = Notificator()
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
        self.logger.debug('New URL Monitor has been successfully initialised')

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
        """
        Add new link to the monitor
        :param url: link
        :param title: Search title
        :return: None
        """
        url = self._prepare_url(url)
        self._add_url(url=url, title=title)

    @staticmethod
    def _check_search_complete(response: str):
        """
        Check if OLX search was complete
        :param response: OLX search GET request response
        :return: If search was not complete, raises RequestResponseInterrupted error
        """
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
        """
        Take products urls from OLX search
        :param search: OLX search request GET response
        :return: list of links to products
        """
        soup = bs4.BeautifulSoup(search.text, 'html.parser')
        products = soup.find_all('div', attrs={'class': 'css-19ucd76'}, recursive=True)
        for prod in products:
            link_button = prod.find('a', attrs={'class': 'css-1bbgabe'})
            if link_button:
                yield link_button.get('href')

    def _check_search(self, url: str, case_id: int):
        """
        Main function, which checks OLX search if there are any new products
        :param url: search link
        :param case_id: search record ID in database
        :return:
        """
        self.logger.debug(f'Checking search for updates, ID: {case_id}, URL: {url}')
        self._get_new_session()
        try:
            response = self.session.get(url)
            self._check_search_complete(response.text)
            hrefs = self._get_products_from_search(response)
            products = []
            for link in hrefs:
                products.append(OlxProduct(url=link, parent_id=case_id))
            for product in products:
                if not self.db_connector.is_product_in_db(product_id=int(product.id)):
                    self.notificator.send_new_product_notification(
                        product_url=product.link,
                        product_title=product.title
                    )
                    product.insert_to_db()

        except TimeoutError:
            self.logger.exception(
                f'Proxy `{self.session.proxies["http"]}` has been timed out. Retrying with different one...')
            self._check_search(url, case_id)

        except RequestResponseInterrupted as e:
            self.logger.exception(f'Request failed. Reason: `{e.reason}`. Retrying...')
            self._check_search(url, case_id)


class OlxProduct(BaseConnectionClass):
    """
    Class to save OLX products as built in objects
    """
    def __init__(self, url: str, parent_id: int):
        super().__init__()
        self.link = url
        self.title = ''
        self.id = ''
        self.parent_id = parent_id
        self.session = None
        self._get_new_session()
        self.get_product_data()

    @staticmethod
    def _check_request(soup):
        """
        Check if request was complete
        :param soup: OLX search GET request response as a beautifulsoup
        :return: If search was not complete, raises RequestResponseInterrupted error
        """
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

    def get_product_data(self):
        self.logger.debug(f'Getting product info for {self.link}...')
        soup = None
        try:
            product_data = self.session.get(self.link)
            soup = bs4.BeautifulSoup(product_data)
            self._check_request(soup)
        except TimeoutError:
            self.logger.exception(
                f'Proxy `{self.session.proxies["http"]}` has been timed out. Retrying with different one...')
        except RequestResponseInterrupted as e:
            self.logger.exception(f'Request failed. Reason: `{e.reason}`. Retrying...')

        self.title = soup.find('h1', attrs={'class': 'css-r9zjja-Text'}).text.strip()
        self.id = soup.find('div', attrs={'data-cy': 'ad-footer-bar-section'}).find('span', attrs={
            'class': 'css-9xy3gn-Text'}).text.strip().split(' ')[1]

    def insert_to_db(self):
        self.logger.debug(f'Inserting new product to database, ID: {self.id}, URL: {self.link}')
        self.db_connector.insert_new_product(
            title=self.title,
            id=int(self.id),
            url=self.link,
            parent_id=self.parent_id
        )
        self.logger.info(f'Inserted product to db ID: {self.id}, PARENT ID: {self.parent_id}')
