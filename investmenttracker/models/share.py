"""SQLAlchemy-based classes for handling shares

Classes
----------
ShareDataOrigin
    The origin of share prices (website, app, ...)

Share
    Database class for handling shares
"""
import enum
import gettext
import datetime
import sqlalchemy.orm

from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Enum

from .base import Base, NoPriceException, ValidationException

_ = gettext.gettext


class ShareDataOrigin(enum.Enum):
    """The different websites / apps usable as origin of share prices"""

    alphavantage = {
        "name": "Alphavantage",
    }
    boursorama = {
        "name": "Boursorama",
    }
    quantalys = {
        "name": "Quantalys",
    }


class Share(Base):
    """Database class for handling transactions

    Attributes
    ----------
    id : int
        Unique ID
    name : str
        Name of the share
    main_code : str, optional
        Main code to display in various screens
    sync_origin : ShareDataOrigin enum
        Where share prices should be taken from
    hidden : bool
        Whether the share should be hidden by default
    group_id : int, optional
        ID of the group the share belongs to
    group : models.sharegroup.ShareGroup, optional
        Group the share belongs to
    base_currency_id : int, optional
        ID of main currency in which the share should be evaluated
    base_currency : models.share.Share, optional
        Main currency in which the share should be evaluated

    Properties
    -------
    last_price
        Most recent price available

    graph_label
        Label for graph display (assumes there is a base currency)

    short_name
        A short name for display where space is at a premium

    Methods
    -------
    validate_* (key, value)
        Validator for the corresponding field

    validate_missing_field (key, value, message)
        Raises a ValidationException if the corresponding field is empty
    """

    __tablename__ = "shares"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    main_code = Column(String(250), nullable=True)
    sync_origin = Column(Enum(ShareDataOrigin, validate_strings=True), nullable=True)
    hidden = Column(Boolean, default=False)

    group_id = Column(Integer, ForeignKey("share_groups.id"), nullable=True)
    group = sqlalchemy.orm.relationship("ShareGroup", back_populates="shares")

    base_currency_id = Column(Integer, ForeignKey("shares.id"), nullable=True)
    base_currency = sqlalchemy.orm.relationship("Share", remote_side=[id])

    # used_by = sqlalchemy.orm.relationship("Share", back_populates="base_currency")

    codes = sqlalchemy.orm.relationship("ShareCode", back_populates="share")
    transactions = sqlalchemy.orm.relationship(
        "Transaction", order_by="Transaction.date", back_populates="share"
    )
    prices = sqlalchemy.orm.relationship(
        "SharePrice",
        back_populates="share",
        remote_side="[SharePrice.share_id]",
        primaryjoin="SharePrice.share_id==Share.id",
    )

    def __init__(self, **kwargs):
        """Defaults hidden value to its default"""
        if "hidden" not in kwargs:
            kwargs["hidden"] = False
        super().__init__(**kwargs)

    @sqlalchemy.orm.validates("main_code")
    def validate_main_code(self, key, value):
        """Ensure the main code field has less than 250 characters"""
        if len(value) > 250:
            raise ValidationException(
                _("Max length for share main code is 250 characters"), self, key, value
            )
        return value

    @sqlalchemy.orm.validates("name")
    def validate_name(self, key, value):
        """Ensure the name field is filled and has less than 250 characters"""
        self.validate_missing_field(key, value, _("Missing share name"))
        if len(value) > 250:
            raise ValidationException(
                _("Max length for share name is 250 characters"), self, key, value
            )
        return value

    @sqlalchemy.orm.validates("base_currency_id")
    def validate_base_currency_id(self, key, value):
        """Ensure the base currency field is not the share itself"""
        if value is not None and value == self.id:
            raise ValidationException(
                _("Share base currency can't be itself"), self, key, value
            )
        return value

    @sqlalchemy.orm.validates("base_currency")
    def validate_base_currency(self, key, value):
        """Ensure the base currency field is not the share itself"""
        if value is not None and value.id == self.id:
            raise ValidationException(
                _("Share base currency can't be itself"), self, key, value
            )
        return value

    @sqlalchemy.orm.validates("sync_origin")
    def validate_sync_origin(self, key, value):
        """Ensure the sync_origin field is one of the allowed values"""
        if isinstance(value, ShareDataOrigin):
            return value
        if value and isinstance(value, str):
            try:
                return ShareDataOrigin[value]
            except KeyError:
                raise ValidationException(
                    _("Share sync origin is invalid"),
                    self,
                    key,
                    value,
                )
        raise ValidationException(
            _("Share sync origin is invalid"),
            self,
            key,
            value,
        )

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
            The provided value"""
        if not value:
            raise ValidationException(message, self, key, value)
        return value

    @property
    def last_price(self):
        """Most recent price available"""
        try:
            prices = [
                price
                for price in self.prices
                if price.date >= datetime.date.today() + datetime.timedelta(days=-31)
            ]
            return sorted(prices, key=lambda price: price.date)[-1]
        except IndexError:
            raise NoPriceException(
                _("No price available for share {name} ({main_code})").format(
                    name=self.name, main_code=self.main_code
                ),
                self,
            ) from None

    @property
    def graph_label(self):
        """Returns a label for graph display (assumes there is a base currency)"""
        return self.name + (
            " (" + self.base_currency.name + ")" if self.base_currency else ""
        )

    @property
    def short_name(self):
        """Returns a string of form [name] ([main_code])"""
        output = self.name
        if self.main_code:
            output += " (" + self.main_code + ")"
        return output

    def __repr__(self):
        """Returns a string of form Share [name] ([main_code], [currency], (un)synced)"""
        output = "Share " + self.name + " ("
        if self.main_code:
            output += self.main_code + ", "
        if self.base_currency:
            output += self.base_currency.main_code + ", "
        output += "synced" if self.sync_origin else "unsynced"
        output += ")"
        return output
