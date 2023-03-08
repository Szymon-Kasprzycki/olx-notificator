import logging
import fbchat
from exceptions import *

G_RECEIVER = 'Szymon Kasprzycki'
G_LANGUAGE = 'EN'

#############################
login_email = 'xx@123.com'
login_pwd = 'xx123'

#############################


# TODO Make notificator login credentials from file etc
class Notificator:
    def __init__(self):
        self.logger = logging.getLogger()
        self.client = fbchat.Client(
            email=login_email,
            password=login_pwd
        )
        self.MESSAGES = {
            'PL': """
                        Cześć, tu twój wirtualny asystent OLX. 
                        Pojawiło się nowe ogłoszenie w obserwowanym wyszukiwaniu!
                        Tytuł: {}
                        Link: {}
            """,
            'EN': """
                        Hey, here's you virtual OLX asistent.
                        There is new product in observed search!
                        Title: {}
                        URL: {}
            """
        }


def send_new_product_notification(self, product_url: str, product_title: str, receiver: str = G_RECEIVER,
                                  language: str = G_LANGUAGE) -> None:
    self.logger.info(f'Sending message using fb messenger, about [{product_url}]')
    message = self.MESSAGES[language].format(product_title, product_url)
    target_user = self.client.searchForUsers(receiver)[0]

    if target_user.is_friend:
        sent = self.client.sendMessage(
            message=message,
            thread_id=target_user.uid
        )
        if sent:
            self.logger.info(f'Message to {target_user.first_name} {target_user.last_name} was sent successfully!')
        else:
            self.logger.exception(f'Error while sending message to {target_user.first_name} {target_user.last_name} using facebook api!')
            raise NotSentException(f'Error while sending message using facebook api!')
    else:
        self.logger.exception(f'Error while sending message to {receiver} using facebook api! User is not a friend!')
        raise NotAFriendException(f'{receiver} is not a friend on FB!')
