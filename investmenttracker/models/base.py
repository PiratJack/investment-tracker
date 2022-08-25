"""Various classes used in models

Classes
----------
NoPriceException
    Used when a share doesn't have any price matching the searched filters
ValidationException
    Raised when provided data doesn't match requirements (such as mandatory fields)
ValidationWarningException
    Raised when provided data doesn't seem to make sense (can be bypassed)

Functions
----------
format_number (number, currency=None)
    Formats a number for display

"""
import locale
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


def format_number(number, currency=None):
    """Formats a number for display

    Returns
    -------
    str
        Either '-' for numbers <= 10**-7, or formatted number
        Includes the currency string if provided
    """
    if abs(number) <= 10**-7:
        return "-"
    return locale.format_string("%.2f", number, grouping=True) + (
        (" " + currency) if currency else ""
    )
