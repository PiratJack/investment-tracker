import gettext
import sqlalchemy.orm

from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Float, Date, Enum

from .base import Base, FillException, ValidationException
from .transaction import TransactionTypes

_ = gettext.gettext


class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    code = Column(String(250))
    base_currency = Column(String(250), nullable=False)
    enabled = Column(Boolean, default=True)
    transactions = sqlalchemy.orm.relationship(
        "Transaction", order_by="Transaction.date", back_populates="account"
    )

    fillable = ["id", "name", "code", "base_currency", "enabled"]

    def fill(self, data):
        for key, value in data.items():
            if key in self.fillable:
                setattr(self, key, data[key])
            else:
                raise FillException(
                    _("Key {key} is not fillable for account model").format(key=key)
                )

    def get_transactions(self):
        return self.transactions

    @sqlalchemy.orm.validates("name")
    def validate_name(self, key, value):
        if value == "":
            raise ValidationException(
                _("Missing account {field_name}").format(field_name=key)
            )
        if len(value) > 250:
            raise ValidationException(
                _("Max length for account {field_name} is 250 characters").format(
                    field_name=key
                )
            )
        return value

    @sqlalchemy.orm.validates("code")
    def validate_code(self, key, value):
        if len(value) > 250:
            raise ValidationException(
                _("Max length for account {field_name} is 250 characters").format(
                    field_name=key
                )
            )
        return value

    @sqlalchemy.orm.validates("base_currency")
    def validate_base_currency(self, key, value):
        if value == "":
            raise ValidationException(
                _("Missing account {field_name}").format(field_name=key)
            )
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
