"""SQLAlchemy-based classes for handling transactions.

Classes
----------
TransactionTypes
    The different types for transactions. Also defines the cash & asset impacts.

Transaction
    Database class for handling transactions
"""

import enum
import gettext
import sqlalchemy.orm

from sqlalchemy import Column, ForeignKey, Integer, String, Float, Date, Enum

from .base import Base, ValidationException

_ = gettext.gettext


class TransactionTypes(enum.Enum):
    """The different types for transactions. Also defines the cash & asset impacts.

    The attributes are:
    - impact_currency:
        1 if the account cash balance increased as a consequence of this transaction
        -1 if the account cash balance decreased as a consequence of this transaction
        0 otherwise
    - impact_asset:
        1 if the account asset balance increased as a consequence of this transaction
        -1 if the account asset balance decreased as a consequence of this transaction
        0 otherwise
    - has_asset:
        1 if the transaction is linked to an asset
        0 otherwise
        This may be 1 even if impact_asset=0: for example to record asset buying fees
    - exclude_from_net_baseline:
        1 if the transaction should be excluded from the net baseline in the graphs
        0 otherwise
    """

    arbitrage_buy = {
        "name": _("Arbitrage - Buy"),
        "impact_currency": 0,
        "impact_asset": 1,
        "has_asset": 1,
        "exclude_from_net_baseline": 0,
    }
    arbitrage_sell = {
        "name": _("Arbitrage - Sell"),
        "impact_currency": 0,
        "impact_asset": -1,
        "has_asset": 1,
        "exclude_from_net_baseline": 0,
    }
    asset_buy = {
        "name": _("Asset buy / subscription"),
        "impact_currency": -1,
        "impact_asset": 1,
        "has_asset": 1,
        "exclude_from_net_baseline": 0,
    }
    asset_sell = {
        "name": _("Asset sell"),
        "impact_currency": 1,
        "impact_asset": -1,
        "has_asset": 1,
        "exclude_from_net_baseline": 0,
    }
    cash_entry = {
        "name": _("Cash deposit"),
        "impact_currency": 1,
        "impact_asset": 0,
        "has_asset": 0,
        "exclude_from_net_baseline": 1,
    }
    cash_exit = {
        "name": _("Cash withdrawal"),
        "impact_currency": -1,
        "impact_asset": 0,
        "has_asset": 0,
        "exclude_from_net_baseline": 1,
    }
    company_funding_cash = {
        "name": _("Company funding - Cash"),
        "impact_currency": 1,
        "impact_asset": 0,
        "has_asset": 0,
        "exclude_from_net_baseline": 0,
    }
    company_funding_asset = {
        "name": _("Company funding - Asset"),
        "impact_currency": 0,
        "impact_asset": 1,
        "has_asset": 1,
        "exclude_from_net_baseline": 0,
    }
    dividends = {
        "name": _("Dividends"),
        "impact_currency": 1,
        "impact_asset": 0,
        "has_asset": 1,
        "exclude_from_net_baseline": 0,
    }
    fee_asset = {
        "name": _("Management fee - in units"),
        "impact_currency": 0,
        "impact_asset": -1,
        "has_asset": 1,
        "exclude_from_net_baseline": 0,
    }
    fee_cash = {
        "name": _("Management fee - in cash"),
        "impact_currency": -1,
        "impact_asset": 0,
        "has_asset": 0,
        "exclude_from_net_baseline": 0,
    }
    movement_fee = {
        "name": _("Movement fee"),
        "impact_currency": -1,
        "impact_asset": 0,
        "has_asset": 1,
        "exclude_from_net_baseline": 0,
    }
    profit_asset = {
        "name": _("Profit - in units"),
        "impact_currency": 0,
        "impact_asset": 1,
        "has_asset": 1,
        "exclude_from_net_baseline": 0,
    }
    profit_cash = {
        "name": _("Profit - in cash"),
        "impact_currency": 1,
        "impact_asset": 0,
        "has_asset": 1,
        "exclude_from_net_baseline": 0,
    }
    split_source = {
        "name": _("Split & merge - Source"),
        "impact_currency": 0,
        "impact_asset": -1,
        "has_asset": 1,
        "exclude_from_net_baseline": 0,
    }
    split_target = {
        "name": _("Split & merge - Target"),
        "impact_currency": 0,
        "impact_asset": 1,
        "has_asset": 1,
        "exclude_from_net_baseline": 0,
    }
    taxes_cash = {
        "name": _("Taxes - in cash"),
        "impact_currency": -1,
        "impact_asset": 0,
        "has_asset": 0,
        "exclude_from_net_baseline": 0,
    }
    taxes_asset = {
        "name": _("Taxes - in units"),
        "impact_currency": 0,
        "impact_asset": -1,
        "has_asset": 1,
        "exclude_from_net_baseline": 0,
    }
    transfer_in_cash = {
        "name": _("Transfer - Cash in"),
        "impact_currency": 1,
        "impact_asset": 0,
        "has_asset": 0,
        "exclude_from_net_baseline": 1,
    }
    transfer_in_asset = {
        "name": _("Transfer - Asset in"),
        "impact_currency": 0,
        "impact_asset": 1,
        "has_asset": 1,
        "exclude_from_net_baseline": 1,
    }
    transfer_out_cash = {
        "name": _("Transfer - Cash out"),
        "impact_currency": -1,
        "impact_asset": 0,
        "has_asset": 0,
        "exclude_from_net_baseline": 1,
    }
    transfer_out_asset = {
        "name": _("Transfer - Asset out"),
        "impact_currency": 0,
        "impact_asset": -1,
        "has_asset": 1,
        "exclude_from_net_baseline": 1,
    }


class Transaction(Base):
    """Database class for handling transactions

    Attributes
    ----------
    id : int
        Unique ID
    date : datetime.datetime
        Record date
    label : str, optional
        Free text label (limited to 250 characters)
    type : TransactionTypes enum
        Type (also defines the impact of the transaction)
    quantity : float
        Number of assets or amount in cash
    unit_price : float
        Unit price (for asset transactions)
    share_id : int, optional
        ID of the related share (if transaction has one)
    share : models.share.Share, optional
        Related share (if transaction has one)
    account_id : int
        ID of the account
    account : models.share.Account
        Account which includes the transaction

    cash_total
        Returns the total cash change due to this transaction (may be negative)
    asset_total
        Returns the total asset change due to this transaction (may be negative)

    Methods
    -------
    copy
        Returns a copy of the transaction

    validate_* (key, value)
        Validator for the corresponding field

    validate_missing_field (key, value, message)
        Raises a ValidationException if the corresponding field is empty
    """

    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    label = Column(String(250))
    type = Column(Enum(TransactionTypes, validate_strings=True), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)

    share_id = Column(Integer, ForeignKey("shares.id"))
    share = sqlalchemy.orm.relationship("Share", back_populates="transactions")

    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    account = sqlalchemy.orm.relationship("Account", back_populates="transactions")

    ignore_warnings = False

    @sqlalchemy.orm.validates("label")
    def validate_label(self, key, value):
        """Ensure the label field has less than 250 characters"""
        if len(value) > 250:
            raise ValidationException(
                _("Max length for transaction label is 250 characters"),
                self,
                key,
                value,
            )
        return value

    @sqlalchemy.orm.validates("type")
    def validate_type(self, key, value):
        """Ensure the type field is filled and has one of the allowed values"""
        self.validate_missing_field(key, value, _("Missing transaction type"))

        if isinstance(value, TransactionTypes):
            return value
        if value and isinstance(value, str):
            try:
                return TransactionTypes[value]
            except KeyError as exception:
                raise ValidationException(
                    _("Transaction type is invalid"),
                    self,
                    key,
                    value,
                ) from exception
        raise ValidationException(
            _("Transaction type is invalid"),
            self,
            key,
            value,
        )

    @sqlalchemy.orm.validates("account_id")
    def validate_account_id(self, key, value):
        """Ensure the account field is filled"""
        self.validate_missing_field(key, value, _("Missing transaction account"))
        return value

    @sqlalchemy.orm.validates("quantity")
    def validate_quantity(self, key, value):
        """Ensure the quantity field is filled and different than 0"""
        self.validate_missing_field(key, value, _("Missing transaction quantity"))
        return value

    @sqlalchemy.orm.validates("unit_price")
    def validate_unit_price(self, key, value):
        """Ensure the unit price field is filled"""
        if not self.type:
            return value
        if not isinstance(self.type, TransactionTypes):
            return value
        type_value = self.type.value
        if type_value["has_asset"] and type_value["impact_currency"]:
            self.validate_missing_field(key, value, _("Missing transaction unit price"))
        return value

    @sqlalchemy.orm.validates("share_id")
    def validate_share_id(self, key, value):
        """Ensure the share_id field is filled if transaction has assets"""
        if self.type:
            type_value = self.type.value
            if type_value["impact_asset"] and value in (-1, 0):
                raise ValidationException("Missing transaction share", self, key, value)
            if type_value["has_asset"] and value in (-1, 0):
                raise ValidationException("Missing transaction share", self, key, value)
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
            The provided value"""
        if not value:
            raise ValidationException(message, self, key, value)
        return value

    @property
    def cash_total(self):
        """Returns the total cash change due to this transaction (may be negative)"""
        type_enum = (
            TransactionTypes[self.type] if isinstance(self.type, str) else self.type
        )
        return type_enum.value["impact_currency"] * self.quantity * self.unit_price

    @property
    def asset_total(self):
        """Returns the total asset change due to this transaction (may be negative)"""
        type_enum = (
            TransactionTypes[self.type] if isinstance(self.type, str) else self.type
        )
        return type_enum.value["impact_asset"] * self.quantity

    def copy(self):
        """Returns a copy of the transaction"""
        new_transaction = Transaction()
        for attr in [
            "date",
            "label",
            "type",
            "quantity",
            "unit_price",
            "share_id",
            "account_id",
            "share",
            "account",
        ]:
            if attr == "type":
                new_transaction.type = self.type.name
            else:
                setattr(new_transaction, attr, getattr(self, attr))
        return new_transaction

    def __repr__(self):
        """Returns a string of form Transaction (type, date, share, account)"""
        type_str = (
            TransactionTypes[self.type].name
            if isinstance(self.type, str)
            else self.type.value["name"]
        )
        account_str = self.account.name if self.account else ""
        share_str = self.share.name if self.share else ""

        return "Transaction " + str((type_str, str(self.date), share_str, account_str))
