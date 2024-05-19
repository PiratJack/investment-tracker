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
import sqlalchemy.orm

Base = sqlalchemy.orm.declarative_base()


class NoPriceException(Exception):
    """Exception type when shares have no price according to requested parameters"""

    def __init__(self, message, share):
        super().__init__(message)
        self.share = share


class ValidationException(Exception):
    """Exception type for validating data: missing mandatory fields, invalid value..."""

    def __init__(self, message, item, key, invalid_value):
        super().__init__(message)
        self.message = message
        self.item = item
        self.key = key
        self.invalid_value = invalid_value


class ValidationWarningException(Exception):
    """Exception type for data warnings: things that are possible but not smart"""

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
    if not number or abs(number) <= 10**-7:
        return "-"
    if currency:
        return locale.format_string("%.2f", number, grouping=True) + " " + currency

    return locale.format_string("%.5f", number, grouping=True)
