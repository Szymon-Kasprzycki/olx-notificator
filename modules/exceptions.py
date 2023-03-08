
class RequestResponseInterrupted(Exception):
    """Exception raised for errors in request responses.

    Attributes:
        reason -- response part which caused the error
        message -- explanation of the error
    """

    def __init__(self, reason, message="Response seems not to be proper."):
        self.reason = reason
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return f'{self.message} -> {self.reason}'


class BaseFacebookException(Exception):
    """Exception raised for errors in facebook requests.

    Attributes:
        reason -- response part which caused the error
        message -- explanation of the error
    """
    def __init__(self, reason, message="Facebook API error."):
        self.reason = reason
        self.message = message

    def __str__(self) -> str:
        return f"{self.message} -> {self.reason}"


class NotAFriendException(BaseFacebookException):
    """Exception raised when target user is not a friend on facebook.

    Attributes:
        reason -- response part which caused the error
        message -- explanation of the error
    """
    def __init__(self, reason, message="User is not a friend on FB!"):
        super().__init__(reason, message)


class NotSentException(BaseFacebookException):
    """Exception raised when facebook message was not sent.

    Attributes:
        reason -- response part which caused the error
        message -- explanation of the error
    """
    def __init__(self, reason, message="Message was not sent!"):
        super().__init__(reason, message)
