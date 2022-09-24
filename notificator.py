import logging
import fbchat

#############################
login_email = 'xx@123.com'
login_pwd = 'xx123'
#############################


class Notificator:
    def __init__(self):
        self.logger = logging.getLogger()
        self.client = fbchat.Client(
            email=login_email,
            password=login_pwd
        )
        self.MESSAGE = """
                            Cześć, tu twój wirtualny asystent OLX. 
                            Pojawiło się nowe ogłoszenie w obserwowanym wyszukiwaniu!
                            Tytuł: {}
                            Link: {}
                        """

    def send_new_product_notification(self, product_url: str, product_title: str, receiver: str = 'Szymon Kasprzycki'):
        self.logger.info(f'Sending message using messenger, about [{product_url}]')
        MESSAGE = self.MESSAGE.format(product_title, product_url)
        target_user = self.client.searchForUsers(receiver)[0]
        if target_user.is_friend:
            sent = self.client.sendMessage(
                message=MESSAGE,
                thread_id=target_user.uid
            )
            if sent:
                self.logger.info(f'Message to {target_user.first_name} {target_user.last_name} was sent successfully!')
            else:
                self.logger.exception(
                    f'Error while sending message to {target_user.first_name} {target_user.last_name} using facebook api!')
                raise Exception(f'Error while sending message using facebook api!')
