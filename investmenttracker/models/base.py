from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class FillException(Exception):
    pass


class NoPriceException(Exception):
    pass
