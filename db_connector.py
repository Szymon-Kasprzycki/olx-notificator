import psycopg2
import psycopg2.extras
import logging
from typing import Union
from datetime import datetime


class DBConnector:
    """
    Connector object to the PostgreSQL database.
    It permforms every database operation in the script.
    """
    def __init__(self, credentials: dict):
        self.logger = logging.getLogger()
        self.connection = psycopg2.connect(
            host=credentials['hostname'],
            dbname=credentials['database'],
            user=credentials['login'],
            password=credentials['password'],
            port=credentials['port']
        )
        self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        self.connected = True
        self._init_tables()
        self.logger.info('Successfully connected to the database')

    def _init_tables(self):
        """
        Create two tables in database if they not exist - "urls_to_monitor" and "items"
        """
        self.cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS urls_to_monitor (
                    id              int PRIMARY KEY,
                    title           varchar(40) NOT NULL,
                    url             varchar(250),
                    last_updated    varchar(50))
            """
        )

        self.cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS products (
                    id          int PRIMARY KEY,
                    url         varchar(250),
                    upload_date varchar(50),
                    parent_id   int,
                    FOREIGN KEY ("parent_id") REFERENCES "urls_to_monitor"("id"))
            """
        )

    def download_existing_data(self):
        """
        This functions downloads from database existing urls that needs to be monitored.

        :return: list with all urls as dictionaries
        """
        self.cursor.execute(
            """
                SELECT * from urls_to_monitor
            """
        )
        for position in self.cursor.fetchall():
            yield dict(position)

    def insert_new_link(self, title: str, url: str, last_updated: Union[str, datetime]):
        """
        This function adds new record to table "urls_to_monitor" to database. It allows you to add new link to get notifications from
        :param title: Title of link, it's name
        :param url: Link address
        :param last_updated: Last time when link was checked for update
        """
        if self.connected:
            self.cursor.execute(
                """
                    SELECT MAX(id)
                    FROM urls_to_monitor;
                """
            )
            highest_id = int(self.cursor.fetchone()['max'])
            new_id = highest_id + 1 if highest_id else 1
            self.cursor.execute(
                """
                    INSERT INTO urls_to_monitor (id, title, url, last_updated) VALUES (%s, %s, %s, %s)
                """, (new_id, title, url, str(last_updated))
            )
        else:
            self.logger.exception(f'Cannot insert `{title}` [url] to the database, connection is not established!')

    def _insert_new_product(self, title: str, id: int, url: str, parent_id: int):
        """
        This function adds new record to table "urls_to_monitor" to database. It allows you to add new link to get notifications from
        :param title: product name
        :param id: product ID
        :param url: product link
        """
        if self.connected:
            upload_date = datetime.now().strftime('%Y-%m-%d %T')
            self.cursor.execute(
                """
                    INSERT INTO products (id, url, upload_date, parent_id) VALUES (%s, %s, %s, %s)
                """, (id, url, upload_date, parent_id)
            )
        else:
            self.logger.exception(f'Cannot insert `{title}` [product] to the database, connection is not established!')