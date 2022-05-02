import sqlalchemy

from . import account
from . import share
from . import sharegroup

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
            .all()
        )

    def accounts_get_all_with_hidden(self):
        return self.session.query(account.Account).all()

    def accounts_get_by_id(self, account_id):
        return (
            self.session.query(account.Account)
            .filter(account.Account.id == account_id)
            .one()
        )

    # Shares
    def shares_query(self):
        return self.session.query(share.Share)

    def shares_get_all(self):
        return self.session.query(share.Share).filter(share.Share.hidden == False).all()

    def shares_get_all_with_hidden(self):
        return self.session.query(share.Share).all()

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
