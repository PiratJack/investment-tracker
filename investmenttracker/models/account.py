"""SQLAlchemy-based classes for handling accounts

Classes
----------
Account
    Database class for handling accounts
    Accounts store cash and assets
"""
import gettext
import datetime
import sqlalchemy.orm

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey

from .base import Base, ValidationException, NoPriceException
from .transaction import TransactionTypes

_ = gettext.gettext


class Account(Base):
    """Database class for handling transactions

    Attributes
    ----------
    id : int
        Unique ID
    name : str
        Name of the share
    code : str, optional
        A code to display in various screens
    enabled : bool
        Whether the account is enabled (useful for obsolete accounts)
    hidden : bool
        Whether the account should be hidden by default
    base_currency_id : int, optional
        ID of main currency in which the share should be evaluated
    base_currency : models.share.Share, optional
        Main currency in which the share should be evaluated
    transactions : list of models.transaction.Transactions, optional
        All transactions recorded for this account

    Properties
    -------
    balance : float
        Cash balance of the account, after all transactions are processed
    start_date : datetime.date
        Date of the first transcation
    graph_label : str
        Label for graph display (assumes there is a base currency)
    shares : list of models.share.Share
        Shares held once all transactions are processed (format: {share_id: # held})
    total_invested : float
        The total amount invested in this account
    total_value
        The total value of the account (cash + assets)
    holdings
        The details of cash & shares held at each transaction date

    Methods
    -------
    validate_* (key, value)
        Validator for the corresponding field

    validate_missing_field (key, value, message)
        Raises a ValidationException if the corresponding field is empty

    balance_after_transaction (transaction)
        Returns the cash and asset balance after a given transaction (for the relevant asset)
    balance_before_staged_transaction (transaction)
        Same as balance_after_transaction for unsaved transactions
    """

    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    code = Column(String(250))
    enabled = Column(Boolean, default=True)
    hidden = Column(Boolean, default=False)

    base_currency_id = Column(Integer, ForeignKey("shares.id"), nullable=False)
    base_currency = sqlalchemy.orm.relationship("Share")
    transactions = sqlalchemy.orm.relationship(
        "Transaction", order_by="Transaction.date", back_populates="account"
    )

    def __init__(self, **kwargs):
        """Defaults the enabled & hidden values based on table defaults"""
        if "enabled" not in kwargs:
            kwargs["enabled"] = self.__table__.c.enabled.default.arg
        if "hidden" not in kwargs:
            kwargs["hidden"] = self.__table__.c.hidden.default.arg
        super().__init__(**kwargs)

    @sqlalchemy.orm.validates("name")
    def validate_name(self, key, value):
        """Ensure the name field is filled and has less than 250 characters"""
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
        """Ensure the code field has less than 250 characters"""
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
        """Ensure the base currency field is filled"""
        self.validate_missing_field(key, value, _("Missing account base currency"))
        return value

    @sqlalchemy.orm.validates("base_currency_id")
    def validate_base_currency_id(self, key, value):
        """Ensure the base currency field is filled"""
        self.validate_missing_field(key, value, _("Missing account base currency"))
        return value

    @property
    def balance(self):
        """Returns the cash balance of the account"""
        balance = 0
        for transaction in self.transactions:
            balance += transaction.cash_total
        if abs(balance) <= 10**-8:
            return 0
        return balance

    @property
    def start_date(self):
        """Returns the date of the first transaction"""
        try:
            return min([t.date for t in self.transactions])
        except ValueError:
            return None

    @property
    def graph_label(self):
        """Returns a label for graph display (assumes there is a base currency)"""
        return self.name + (
            " (" + self.base_currency.name + ")" if self.base_currency else ""
        )

    @property
    def shares(self):
        """Returns all shares held once all transactions are processed

        The key is the share ID. The value is the number of shares held."""
        shares = {}
        for transaction in self.transactions:
            if transaction.type.value["impact_asset"]:
                share_id = transaction.share.id
                if share_id not in shares:
                    shares[share_id] = 0
                shares[share_id] += (
                    transaction.type.value["impact_asset"] * transaction.quantity
                )
        # Remove zeroes to avoid further issues
        shares = {k: v for k, v in shares.items() if abs(v) >= 10**-8}
        return shares

    @property
    def total_invested(self):
        """Returns the sum of all cas_entry transactions"""
        return sum(
            [
                transaction.quantity
                for transaction in self.transactions
                if transaction.type == TransactionTypes.cash_entry
            ]
        )

    @property
    def total_value(self):
        """Returns the total value of the account, based on its held cash & shares"""
        value = 0
        value += self.balance
        shares = {
            transaction.share.id: transaction.share
            for transaction in self.transactions
            if transaction.share
        }
        for share_id in self.shares:
            share = shares[share_id]
            if share == self.base_currency:
                price = 1
            else:
                prices = [
                    price
                    for price in share.prices
                    if price.currency == self.base_currency
                    and price.date
                    >= datetime.date.today() + datetime.timedelta(days=-31)
                ]
                if prices:
                    price = sorted(prices, key=lambda a: a.date, reverse=True)[-1].price
                else:
                    currency_prices = [
                        price
                        for price in share.last_price.currency.prices
                        if price.currency == self.base_currency
                        and price.date
                        >= datetime.date.today() + datetime.timedelta(days=-31)
                    ]
                    if not currency_prices:
                        raise NoPriceException(
                            "Could not find any price for share (even through FOREX)",
                            share,
                        )
                    price = share.last_price.price * currency_prices[-1].price
            value += self.shares[share_id] * price
        return value

    @property
    def holdings(self):
        """Returns all shares held once all transactions are processed

        Returns
        -------
        A dict with the following format:
            datetime.date: {
                "cash": cash_amount,
                "shares": {
                    share_id: number of shares held,
                }
            }
        """
        account_holdings = {}
        previous_holdings = {"cash": 0, "shares": {}}
        for t in sorted(self.transactions, key=lambda t: t.date):
            # Set up value based on previous ones
            if not account_holdings or t.date not in account_holdings:
                account_holdings[t.date] = {
                    "cash": previous_holdings["cash"],
                    "shares": previous_holdings["shares"].copy(),
                }

            # Now, add the actual transaction
            account_holdings[t.date]["cash"] += t.cash_total
            # Cash below precision limit: put as 0
            if abs(account_holdings[t.date]["cash"]) <= 10**-8:
                account_holdings[t.date]["cash"] = 0
            if t.type.value["impact_asset"]:
                if t.share.id not in account_holdings[t.date]["shares"]:
                    account_holdings[t.date]["shares"][t.share.id] = 0
                account_holdings[t.date]["shares"][t.share.id] += t.asset_total
                if account_holdings[t.date]["shares"][t.share.id] == 0:
                    del account_holdings[t.date]["shares"][t.share.id]
            previous_holdings = account_holdings[t.date]

        return account_holdings

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

    def __repr__(self):
        """Returns string of form Account ([code], enabled/disabled, hidden/visible)"""
        output = "Account " + self.name + " ("
        if self.code:
            output += self.code + ", "
        output += "enabled, " if self.enabled else "disabled, "
        output += "hidden" if self.hidden else "visible"
        output += ")"
        return output

    def balance_after_transaction(self, transaction):
        """Calculates the cash and asset balance after a given transaction

        Parameters
        -------
        transaction: models.transaction.Transaction
            The transaction that serves as reference point

        Returns
        -------
        tuple: (cash_balance, asset_balance)
            Only the asset of the transaction is taken into account
        """
        if isinstance(transaction, int):
            try:
                transaction = [i for i in self.transactions if i.id == transaction][0]
            except IndexError as exception:
                raise ValueError(
                    "Transaction doesn't exist in that account"
                ) from exception
        elif transaction not in self.transactions:
            raise ValueError("Transaction doesn't exist in that account")

        cash_balance = sum(
            t.cash_total
            for t in self.transactions
            if t.date < transaction.date
            or (t.date == transaction.date and t.id <= transaction.id)
        )
        asset_balance = sum(
            t.asset_total
            for t in self.transactions
            if (
                t.date < transaction.date
                or (t.date == transaction.date and t.id <= transaction.id)
            )
            and t.share == transaction.share
        )

        return cash_balance, asset_balance

    def balance_before_staged_transaction(self, transaction):
        """Calculates the cash and asset balance after a given staged transaction

        Summary: does the same as balance_after_transaction for unsaved transcations

        Parameters
        -------
        transaction: models.transaction.Transaction
            The transaction that serves as reference point

        Returns
        -------
        tuple: (cash_balance, asset_balance)
            Only the asset of the transaction is taken into account
        """
        cash_balance = sum(
            t.cash_total
            for t in self.transactions
            if t.date < transaction.date
            or (t.date == transaction.date and t.id != transaction.id)
        )
        asset_balance = sum(
            t.asset_total
            for t in self.transactions
            if t.id != transaction.id
            and t.type.value["impact_asset"]
            and t.date <= transaction.date
            and t.share.id == transaction.share_id
        )

        return cash_balance, asset_balance
