import psycopg2
import psycopg2.extras
import logging
from typing import Union
from datetime import datetime


def print_psycopg2_exception(err) -> None:
    """
    Prints the error message from psycopg2
    :param err: Exception
    """
    err_type, traceback = err.__class__, err.__traceback__
    line_number = traceback.tb_lineno
    log = logging.getLogger()
    log.error(f'Psycopg2 ERROR: {err} on line number: {line_number}')
    log.error('Psycopg2 traceback: ', exc_info=err)
    diag = err.diag
    log.error(f'Psycopg2 error: {diag.pgcode}: {diag.pgerror}')


class DBConnector:
    """
    Connector object to the PostgreSQL database.
    It performs every database operation in the script.
    Credentials:
        - hostname
        - port
        - database
        - login
        - password
    """

    def __init__(self, credentials: dict) -> None:
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

    def _init_tables(self) -> None:
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
        self.logger.info('Successfully prepared table `urls` in database')
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
        self.logger.info('Successfully prepared table `products` in database')
        self.connection.commit()

    def download_existing_data(self) -> list:
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

    def insert_new_link(self, title: str, url: str, last_updated: Union[str, datetime] = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")) -> None:
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
            data = self.cursor.fetchone()
            if data['max']:
                highest_id = int(data['max'])
            else:
                highest_id = None
            new_id = highest_id + 1 if highest_id else 1
            self.cursor.execute(
                """
                    INSERT INTO urls_to_monitor (id, title, url, last_updated) VALUES (%s, %s, %s, %s)
                """, (new_id, title, url, str(last_updated))
            )
            self.connection.commit()
        else:
            self.logger.exception(f'Cannot insert `{title}` [url] to the database, connection is not established!')

    def insert_new_product(self, id: int, url: str, parent_id: int) -> None:
        """
        This function adds new record to table "urls_to_monitor" to database. It allows you to add new link to get notifications from

        :param title: product name
        :param id: product ID
        :param url: product link
        :param parent_id: ID of the search url from the database
        """
        if self.connected:
            upload_date = datetime.now().strftime('%Y-%m-%d %T')
            self.cursor.execute(
                """
                    INSERT INTO products (id, url, upload_date, parent_id) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
                """, (id, url, upload_date, parent_id)
            )
            self.connection.commit()
        else:
            self.logger.exception(f'Cannot insert `{id}` [product] to the database, connection is not established!')

    def is_product_in_db(self, url: str = None, product_id: int = None) -> bool:
        """
        Check whether product already exists in database, include one of two attributes

        :param url: Product URL, default None
        :param product_id: Product OLX ID, default None
        :return: True if product exists else False
        """
        if self.connected:
            if url:
                self.cursor.execute(
                    """
                        SELECT id FROM products WHERE url = %s
                    """
                ), (url,)
                data = self.cursor.fetchone()
            elif product_id:
                self.cursor.execute(
                    """
                        SELECT id FROM products WHERE id = %s
                    """
                ), (product_id,)
                data = self.cursor.fetchone()
            else:
                self.logger.exception('Failed to search for product in database, no needed data provided.')
                raise ValueError('Neither URL nor PRODUCT_ID not provided')

            return True if data else False
        else:
            self.logger.exception(f'Cannot search for product in database, connection is not established!')
            return False

    def __del__(self) -> None:
        self.connection.commit()
        self.cursor.close()
        self.connection.close()
        self.logger.info('Successfully disconnected from the database')

# TEST
if __name__ == '__main__':
    import json
    from log import prepare_logger
    logger = prepare_logger()
    with open('credentials.json') as f:
        credentials = json.load(f)
    conn = DBConnector(credentials)