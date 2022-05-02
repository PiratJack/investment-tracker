import enum
import gettext
import sqlalchemy.orm

from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Float, Date, Enum

from .base import Base, ValidationException

_ = gettext.gettext


class TransactionTypes(enum.Enum):
    arbitrage_buy = {
        "name": _("Arbitrage - Buy"),
        "impact_currency": 0,
        "impact_asset": 1,
        "has_asset": True,
    }
    arbitrage_sell = {
        "name": _("Arbitrage - Sell"),
        "impact_currency": 0,
        "impact_asset": -1,
        "has_asset": True,
    }
    asset_buy = {
        "name": _("Asset buy / subscription"),
        "impact_currency": -1,
        "impact_asset": 1,
        "has_asset": True,
    }
    asset_refund = {
        "name": _("Asset refund"),
        "impact_currency": 0,
        "impact_asset": 1,
        "has_asset": True,
    }
    asset_sell = {
        "name": _("Asset sell"),
        "impact_currency": 1,
        "impact_asset": -1,
        "has_asset": True,
    }
    cash_entry = {
        "name": _("Cash deposit"),
        "impact_currency": 1,
        "impact_asset": 0,
        "has_asset": False,
    }
    cash_exit = {
        "name": _("Cash withdrawal"),
        "impact_currency": -1,
        "impact_asset": 0,
        "has_asset": False,
    }
    company_funding = {
        "name": _("Company funding"),
        "impact_currency": 1,
        "impact_asset": 0,
        "has_asset": False,
    }
    dividends = {
        "name": _("Dividends"),
        "impact_currency": 1,
        "impact_asset": 0,
        "has_asset": False,
    }
    fee_asset = {
        "name": _("Management fee - in units"),
        "impact_currency": 0,
        "impact_asset": -1,
        "has_asset": True,
    }
    fee_cash = {
        "name": _("Management fee - in cash"),
        "impact_currency": -1,
        "impact_asset": 0,
        "has_asset": False,
    }
    forex = {
        "name": _("Foreign exchange"),
        "impact_currency": -1,
        "impact_asset": 1,
        "has_asset": True,
    }
    interest = {
        "name": _("Interests"),
        "impact_currency": 1,
        "impact_asset": 0,
        "has_asset": False,
    }
    movement_fee = {
        "name": _("Movement fee"),
        "impact_currency": -1,
        "impact_asset": 0,
        "has_asset": False,
    }
    profit_asset = {
        "name": _("Profit - in units"),
        "impact_currency": 0,
        "impact_asset": 1,
        "has_asset": True,
    }
    profit_cash = {
        "name": _("Profit - in cash"),
        "impact_currency": 1,
        "impact_asset": 0,
        "has_asset": False,
    }
    split_source = {
        "name": _("Split & merge - Source"),
        "impact_currency": 0,
        "impact_asset": -1,
        "has_asset": True,
    }
    split_target = {
        "name": _("Split & merge - Target"),
        "impact_currency": 0,
        "impact_asset": 1,
        "has_asset": True,
    }
    taxes_cash = {
        "name": _("Taxes - in cash"),
        "impact_currency": -1,
        "impact_asset": 0,
        "has_asset": False,
    }
    taxes_asset = {
        "name": _("Taxes - in units"),
        "impact_currency": 0,
        "impact_asset": -1,
        "has_asset": True,
    }


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    label = Column(String(250))
    type = Column(Enum(TransactionTypes, validate_strings=True), nullable=False)
    share_id = Column(Integer, ForeignKey("shares.id"))
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    share = sqlalchemy.orm.relationship("Share", back_populates="transactions")
    account = sqlalchemy.orm.relationship("Account", back_populates="transactions")

    @sqlalchemy.orm.validates("label")
    def validate_label(self, key, value):
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
        self.validate_missing_field(key, value, _("Missing transaction type"))

        if value not in self.__table__.columns["type"].type.enums:
            raise ValidationException(
                _("Transaction type is invalid"),
                self,
                key,
                value,
            )
        return value

    @sqlalchemy.orm.validates("account_id")
    def validate_account_id(self, key, value):
        self.validate_missing_field(key, value, _("Missing transaction account"))
        return value

    @sqlalchemy.orm.validates("quantity")
    def validate_quantity(self, key, value):
        self.validate_missing_field(key, value, _("Missing transaction quantity"))
        return value

    @sqlalchemy.orm.validates("unit_price")
    def validate_unit_price(self, key, value):
        self.validate_missing_field(key, value, _("Missing transaction unit price"))
        return value

    def validate_missing_field(self, key, value, message):
        if value == "" or value is None:
            raise ValidationException(message, self, key, value)
        return value

    def __repr__(self):
        type_str = self.type if type(self.type) == str else self.type.value["name"]
        account_str = self.account.name if self.account else ""
        share_str = self.share.name if self.share else ""

        return "Transaction " + str((type_str, str(self.date), share_str, account_str))
