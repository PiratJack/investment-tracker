import gettext
import sqlalchemy.orm

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey

from .base import Base, ValidationException
from .transaction import TransactionTypes

_ = gettext.gettext


class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    code = Column(String(250))
    enabled = Column(Boolean, default=True)
    hidden = Column(Boolean, default=False)

    base_currency_id = Column(Integer, ForeignKey("shares.id"))
    base_currency = sqlalchemy.orm.relationship("Share")
    transactions = sqlalchemy.orm.relationship(
        "Transaction", order_by="Transaction.date", back_populates="account"
    )

    def __init__(self, **kwargs):
        if "enabled" not in kwargs:
            kwargs["enabled"] = self.__table__.c.enabled.default.arg
        if "hidden" not in kwargs:
            kwargs["hidden"] = self.__table__.c.hidden.default.arg
        super().__init__(**kwargs)

    @sqlalchemy.orm.validates("name")
    def validate_name(self, key, value):
        self.validate_missing_field(key, value, _("Missing account name"))
        if len(value) > 250:
            raise ValidationException(
                _("Max length for account name is 250 characters"),
                self,
                key,
                value,
            )
        return value

    @sqlalchemy.orm.validates("code")
    def validate_code(self, key, value):
        if len(value) > 250:
            raise ValidationException(
                _("Max length for account code is 250 characters"),
                self,
                key,
                value,
            )
        return value

    @sqlalchemy.orm.validates("base_currency")
    def validate_base_currency(self, key, value):
        self.validate_missing_field(key, value, _("Missing account base currency"))
        return value

    def __getattr__(self, attr):
        if attr == "balance":
            balance = 0
            for transaction in self.transactions:
                balance += (
                    transaction.type.value["impact_currency"]
                    * transaction.quantity
                    * transaction.unit_price
                )
            return balance

        if attr == "shares":
            shares = {}
            for transaction in self.transactions:
                if transaction.share:
                    share_id = transaction.share.id
                    if share_id not in shares:
                        shares[share_id] = 0
                    shares[share_id] += (
                        transaction.type.value["impact_asset"] * transaction.quantity
                    )
            return shares

        if attr == "total_invested":
            return sum(
                [
                    transaction.quantity
                    for transaction in self.transactions
                    if transaction.type == TransactionTypes.cash_entry
                ]
            )

        if attr == "total_value":
            # TODO: Evaluate based on value & currency exchange (if needed)
            return 0
            value = 0
            value += self.balance
            for transaction in self.transactions:
                if transaction.share:
                    value += (
                        transaction.type.value["impact_asset"]
                        * transaction.quantity
                        * transaction.share.last_price.price
                    )

            return value

        raise AttributeError

    def validate_missing_field(self, key, value, message):
        if value == "" or value is None:
            raise ValidationException(message, self, key, value)
        return value

    def __repr__(self):
        output = "Account " + self.name + " ("
        if self.code:
            output += self.code + ", "
        output += "enabled, " if self.enabled else "disabled, "
        output += "hidden" if self.hidden else "visible"
        output += ")"
        return output

    def balance_as_of_transaction(self, transaction):
        if type(transaction) == int:
            try:
                transaction = [i for i in self.transactions if i.id == transaction][0]
            except IndexError:
                raise ValueError("Transaction doesn't exist in that account")
        elif transaction not in self.transactions:
            raise ValueError("Transaction doesn't exist in that account")

        cash_balance = sum(
            t.type.value["impact_currency"] * t.quantity * t.unit_price
            for t in self.transactions
            if t.date < transaction.date
            or (t.date == transaction.date and t.id <= transaction.id)
        )
        asset_balance = sum(
            t.type.value["impact_asset"] * t.quantity
            for t in self.transactions
            if (
                t.date < transaction.date
                or (t.date == transaction.date and t.id <= transaction.id)
            )
            and t.share == transaction.share
        )

        return cash_balance, asset_balance
