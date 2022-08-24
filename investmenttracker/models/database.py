"""SQLAlchemy-based class acting as entry point for most queries

Classes
----------
Database
    Holds different methods for most queries used in the rest of the application
"""
import datetime
import sqlalchemy

from . import account
from . import share
from . import sharecode
from . import sharegroup
from . import shareprice
from . import transaction
from . import config

from .base import Base


class Database:
    """Point of entry class for queries into the database

    Attributes
    ----------
    engine : sqlalchemy.Engine
        The database engine
    metadata : sqlalchemy.MetaData
        SQLAlchemy medatada object
    session : sqlalchemy.orm.Session
        Database session

    Methods
    -------
    __init__ (self, database_file)
        Loads (or creates) the database from the provided file

    create_tables (self)
        Creates all the DB tables

    accounts_get (self, with_hidden=False, with_disabled=False)
        Returns a list of all accounts (with or without hidden / disabled accounts)
    account_get_by_id (self, account_id)
        Returns a account based on its ID

    shares_query (self)
        Returns a query for shares
    shares_get (self, with_hidden=False)
        Returns all shares (with or without hidden ones)
    share_get_by_id (self, share_id)
        Returns a share based on its ID
    share_search (self, name)
        Searches for shares based on the provided name

    share_groups_get_all (self)
        Returns all share groups
    share_group_get_by_id (self, share_group_id)
        Returns a share group based on its ID

    share_price_query (self)
        Returns a query for share prices
    share_price_get_by_id (self, share_price_id)
        Returns a share price based on its ID
    share_prices_get (
            self,
            share_id=None,
            currency_id=None,
            start_date=None,
            end_date=None,
            exact_date=False,
        )
        Returns share prices based on various filters

    transaction_get_by_id (self, transaction_id):
        Returns a transaction based on its ID
    transactions_get_by_account_and_shares(self, accounts, account_shares)
        Returns transactions based on various filters

    configs_get_all (self)
        Returns all configuration items
    config_get_by_name (self, name)
        Returns a configuration item based on its *name*
    config_set (self, name, value)
        Sets a configuration based on the name & value

    delete (self, item)
        Deletes the provided item
    """

    def __init__(self, database_file):
        self.engine = sqlalchemy.create_engine("sqlite:///" + database_file)
        self.metadata = sqlalchemy.MetaData()
        self.create_tables()

        self.session = sqlalchemy.orm.sessionmaker(bind=self.engine)()

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    # Accounts
    def accounts_get(self, with_hidden=False, with_disabled=False):
        query = self.session.query(account.Account)
        if not with_hidden:
            query = query.filter(account.Account.hidden.is_(False))
        if not with_disabled:
            query = query.filter(account.Account.enabled)
        return query.all()

    def account_get_by_id(self, account_id):
        return (
            self.session.query(account.Account)
            .filter(account.Account.id == account_id)
            .one()
        )

    # Shares
    def shares_query(self):
        return self.session.query(share.Share)

    def shares_get(self, with_hidden=False):
        query = self.session.query(share.Share)
        if not with_hidden:
            query = query.filter(share.Share.hidden.is_(False))
        return query.all()

    def share_get_by_id(self, share_id):
        return self.session.query(share.Share).filter(share.Share.id == share_id).one()

    def share_search(self, name):
        """Searches a share based on the provided name

        The criteria used are, in descending order of preference:
        - The main_code of the share, or one of its codes
        - The share ID (never displayed to the user, hence its lower priority)

        Parameters
        ----------
        name : str
            The string to search for

        Returns
        -------
        A list of corresponding shares"""
        query = self.session.query(share.Share).filter(
            sqlalchemy.or_(share.Share.name == name, share.Share.main_code == name)
        )
        values = query.all()
        query = (
            self.session.query(share.Share)
            .join(share.Share.codes, aliased=True)
            .filter(share.Share.codes.any(sharecode.ShareCode.value == name))
        )
        values += query.all()
        if values:
            return list(set(values))
        # Finally, search by ID (separately because it's really prone to errors)
        query = self.session.query(share.Share).filter(share.Share.id == name)
        return query.all()

    # Share groups
    def share_groups_get_all(self):
        return self.session.query(sharegroup.ShareGroup).all()

    def share_group_get_by_id(self, share_group_id):
        return (
            self.session.query(sharegroup.ShareGroup)
            .filter(sharegroup.ShareGroup.id == share_group_id)
            .one()
        )

    # Share prices
    def share_price_query(self):
        return self.session.query(shareprice.SharePrice)

    def share_price_get_by_id(self, share_price_id):
        return (
            self.session.query(shareprice.SharePrice)
            .filter(shareprice.SharePrice.id == share_price_id)
            .one()
        )

    # The date filter will look for values within 2 weeks before
    # start_date and end_date expect a datetime.date object
    def share_prices_get(
        self,
        share_id=None,
        currency_id=None,
        start_date=None,
        end_date=None,
        exact_date=False,
    ):
        """Searches share prices based on various filters

        The criteria used are, in descending order of preference:
        - The main_code of the share, or one of its codes
        - The share ID (never displayed to the user, hence its lower priority)

        Parameters
        ----------
        share_id : int or share.Share
            The share for which prices are needed
        currency_id : int or share.Share
            The currency in which prices are required
        start_date : datetime.date or datetime.datetime
            The start date of prices to look for
        end_date : datetime.date or datetime.datetime
            The end date of prices to look for
        exact_date : bool
            If False, prices 14 days prior to start_date will be included.

        Returns
        -------
        A list of corresponding share prices"""
        query = self.session.query(shareprice.SharePrice)
        if share_id:
            if isinstance(share_id, int):
                query = query.filter(shareprice.SharePrice.share_id == share_id)
            else:
                query = query.filter(shareprice.SharePrice.share == share_id)
        if currency_id:
            if isinstance(currency_id, int):
                query = query.filter(shareprice.SharePrice.currency_id == currency_id)
            else:
                query = query.filter(shareprice.SharePrice.currency == currency_id)
        if start_date:
            two_weeks = datetime.timedelta(days=-14)
            start = start_date if exact_date else start_date + two_weeks
            end = end_date if end_date else start_date
            if isinstance(start, datetime.datetime):
                start = datetime.date(start.year, start.month, start.day)
            if isinstance(end, datetime.datetime):
                end = datetime.date(end.year, end.month, end.day)
            query = query.filter(shareprice.SharePrice.date >= start)
            query = query.filter(shareprice.SharePrice.date <= end)
        return query.all()

    def delete(self, item):
        self.session.delete(item)
        self.session.commit()

    # Transactions
    def transaction_get_by_id(self, transaction_id):
        return (
            self.session.query(transaction.Transaction)
            .filter(transaction.Transaction.id == transaction_id)
            .one()
        )

    # Get transactions that are in some accounts OR combination of accounts + shares
    def transactions_get_by_account_and_shares(self, accounts, account_shares):
        """Returns transactions for the chosen account and shares

        Parameters
        ----------
        accounts : list or set of int
            The list of account IDs to filter for
        account_shares : dict of dict of int
            The list of shares to use, in the form {account_id:[share_id]}

        Returns
        -------
        A list of corresponding transactions"""
        transactions = self.session.query(transaction.Transaction)

        conditions = []
        if accounts:
            conditions.append(transaction.Transaction.account_id.in_(accounts))
        if account_shares:
            for account_id in account_shares:
                shares = account_shares[account_id]
                conditions.append(
                    sqlalchemy.and_(
                        transaction.Transaction.account_id == account_id,
                        transaction.Transaction.share_id.in_(shares),
                    )
                )

        transactions = transactions.filter(sqlalchemy.or_(False, *conditions))

        return transactions.all()

    # Configuration
    def configs_get_all(self):
        query = self.session.query(config.Config).all()
        return {config.name: config.value for config in query}

    def config_get_by_name(self, name):
        query = self.session.query(config.Config).filter(config.Config.name == name)
        return query.one() if query.count() == 1 else None

    def config_set(self, name, value):
        if isinstance(value, bool):
            value = 1 if value else 0

        config_data = self.config_get_by_name(name)
        if config_data:
            config_data.value = str(value)
        else:
            config_data = config.Config(name=str(name), value=str(value))
            self.session.add(config_data)
        self.session.commit()
