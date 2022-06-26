from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class NoPriceException(Exception):
    def __init__(self, message, share):
        super().__init__(message)
        self.share = share


class ValidationException(Exception):
    def __init__(self, message, item, key, invalid_value):
        super().__init__(message)
        self.message = message
        self.item = item
        self.key = key
        self.invalid_value = invalid_value


class ValidationWarningException(Exception):
    def __init__(self, message, item, key, invalid_value):
        super().__init__(message)
        self.message = message
        self.item = item
        self.key = key
        self.invalid_value = invalid_value
