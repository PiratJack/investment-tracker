"""SQLAlchemy-based classes for handling share prices.

Classes
----------
SharePrice
    Database class for handling share prices
"""
import gettext
import sqlalchemy.orm

from sqlalchemy import Column, ForeignKey, Integer, String, Float, Date

from .base import Base, ValidationException

_ = gettext.gettext


class SharePrice(Base):
    """Database class for handling share prices

    Attributes
    ----------
    id : int
        Unique ID
    date : datetime.datetime
        Date for this price
    price : float
        Asset's unit price
    share_id : int
        ID of the related share
    share : models.share.Share
        Related share
    currency_id : int
        ID of the currency
    currency : models.share.Share
        Currency
    source : str
        Where the price was found (free text)

    Properties
    -------
    short_name
        A short name for display where space is at a premium

    Methods
    -------
    validate_* (key, value)
        Validator for the corresponding field

    validate_missing_field (key, value, message)
        Raises a ValidationException if the corresponding field is empty
    """

    __tablename__ = "share_prices"
    id = Column(Integer, primary_key=True)
    share_id = Column(Integer, ForeignKey("shares.id"), nullable=False)
    date = Column(Date, nullable=False)
    price = Column(Float, nullable=False)
    currency_id = Column(Integer, ForeignKey("shares.id"), nullable=False)
    source = Column(String(250), nullable=False)

    share = sqlalchemy.orm.relationship(
        "Share", back_populates="prices", foreign_keys=share_id
    )
    currency = sqlalchemy.orm.relationship("Share", foreign_keys=currency_id)

    @sqlalchemy.orm.validates("share_id")
    def validate_share_id(self, key, value):
        """Ensure the share_id field is filled and is not the currency"""
        self.validate_missing_field(key, value, _("Missing share price share ID"))
        if value is not None and value == self.currency_id:
            raise ValidationException(
                _("Share Price currency can't be the share itself"), self, key, value
            )
        return value

    @sqlalchemy.orm.validates("date")
    def validate_date(self, key, value):
        """Ensure the date field is filled"""
        self.validate_missing_field(key, value, _("Missing share price date"))
        return value

    @sqlalchemy.orm.validates("price")
    def validate_price(self, key, value):
        """Ensure the price field is filled"""
        self.validate_missing_field(key, value, _("Missing share price actual price"))
        return value

    @sqlalchemy.orm.validates("currency_id")
    def validate_currency(self, key, value):
        """Ensure the currency_id field is filled and is not the share itself"""
        self.validate_missing_field(key, value, _("Missing share price currency"))
        if value is not None and value == self.share_id:
            raise ValidationException(
                _("Share Price currency can't be the share itself"), self, key, value
            )
        return value

    @sqlalchemy.orm.validates("source")
    def validate_source(self, key, value):
        """Ensure the source field is filled and has less than 250 characters"""
        self.validate_missing_field(key, value, _("Missing share price source"))
        if len(value) > 250:
            raise ValidationException(
                _("Max length for share price source is 250 characters"),
                self,
                key,
                value,
            )
        return value

    def validate_missing_field(self, key, value, message):
        """Raises a ValidationException if the corresponding field is None or empty

        Parameters
        ----------
        key : str
            The name of the field to validate
        value : str
            The value of the field to validate
        message : str
            The message to raise if the field is empty

        Returns
        -------
        object
            The provided value
        """
        if not value:
            raise ValidationException(message, self, key, value)
        return value

    def __repr__(self):
        """Returns a string of form Price (share name at price currency on date)"""
        output = [
            "Price (",
            self.share.name + " at " if self.share else "",
            str(self.price)
            + " "
            + str(self.currency.main_code if self.currency.main_code else self.currency)
            if self.price and self.currency
            else "Unknown",
            " on " + str(self.date) if self.date else "",
            ")",
        ]
        return "".join(output)

    @property
    def short_name(self):
        '''Returns a string of form "[price] [currency] on [date]"'''
        output = [
            str(self.price)
            + " "
            + str(self.currency.main_code if self.currency.main_code else self.currency)
            if self.price and self.currency
            else "Unknown",
            " on " + str(self.date) if self.date else "",
        ]
        return "".join(output)
