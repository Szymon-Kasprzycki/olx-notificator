
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

    def __str__(self):
        return f'{self.message} -> {self.reason}'

