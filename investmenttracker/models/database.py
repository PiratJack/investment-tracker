import sqlalchemy

from . import account
from . import share
from . import sharecode
from . import sharegroup
from . import shareprice
from . import transaction

from .base import Base


class Database:
    def __init__(self, DATABASE_FILE):
        self.engine = sqlalchemy.create_engine("sqlite:///" + DATABASE_FILE)
        self.metadata = sqlalchemy.MetaData()
        self.create_tables()

        Session = sqlalchemy.orm.sessionmaker(bind=self.engine)
        self.session = Session()

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    # Accounts
    def accounts_get_all(self):
        return (
            self.session.query(account.Account)
            .filter(account.Account.hidden == False)
            .filter(account.Account.enabled == True)
            .all()
        )

    def accounts_get(self, with_hidden=False, with_disabled=False):
        query = self.session.query(account.Account)
        if not with_hidden:
            query = query.filter(account.Account.hidden == False)
        if not with_disabled:
            query = query.filter(account.Account.enabled == True)
        return query.all()

    def accounts_get_by_id(self, account_id):
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
            query = query.filter(share.Share.hidden == False)
        return query.all()

    def share_get_by_id(self, share_id):
        return self.session.query(share.Share).filter(share.Share.id == share_id).one()

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

    def share_price_delete(self, share_price):
        self.session.delete(share_price)
        self.session.commit()

    # Transactions
    def transaction_delete(self, transaction):
        self.session.delete(transaction)
        self.session.commit()
