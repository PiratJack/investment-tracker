import logging
import sqlalchemy

from . import account
from . import shareprice
from . import share
from . import transaction

from .base import Base


class Database:
    def __init__(self, DATABASE_FILE):
        logging.info("Connecting to database")
        self.engine = sqlalchemy.create_engine("sqlite:///" + DATABASE_FILE)
        self.metadata = sqlalchemy.MetaData()
        self.create_tables()

        Session = sqlalchemy.orm.sessionmaker(bind=self.engine)
        self.session = Session()
        logging.info("Connected to database")

    def create_tables(self):
        Base.metadata.create_all(self.engine)

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

    def shares_get_all(self):
        return self.session.query(share.Share).filter(share.Share.hidden == False).all()

    def shares_get_all_with_hidden(self):
        return self.session.query(share.Share).all()

    def share_get_by_id(self, share_id):
        return self.session.query(share.Share).filter(share.Share.id == share_id).one()
