import logging
import requests
import re
import json
from datetime import datetime
from db_connector import DBConnector


##########################################################


# DEBUG
with open('credentials.json', 'r', encoding='utf-8') as f:
    auth = json.load(f)


##########################################################


class URLMonitor:
    """
    This object allow You to monitor changes in products for given urls
    """
    def __init__(self, refresh_time: int):
        self.logger = logging.getLogger()
        self.refresh_time = refresh_time
        self.url_list = []
        self._get_user_agents()
        self.db_connector = DBConnector(credentials=auth)
        self.logger.debug('URL Monitor has been successfully initialised')

    def _get_user_agents(self):
        """
        This function reads web user agents from txt file in utils folder.
        """
        with open('utils/user-agents.txt', 'r', encoding='utf-8') as f:
            self.user_agents = [line.strip().replace('\n', '') for line in f.readlines()]

    def _prepare_url(self, url: str):
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
        if re.match(regex, url) is not None and 'olx.pl' in url:
            url = self._prepare_url(url)
            self.url_list.append(
                {
                    'title': title,
                    'url': url,
                    'time_added': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                    'last_updated': 'none',
                }
            )

    def _check_url_for_update(self, url):
        response = requests.get(url)
