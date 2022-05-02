import gettext
import sqlalchemy.orm

from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Float, Date, Enum

from .base import Base, NoPriceException

_ = gettext.gettext


class Share(Base):
    __tablename__ = "shares"
    id = Column(Integer, primary_key=True)
    main_code = Column(String(250), nullable=True)
    name = Column(String(250), nullable=False)
    sync = Column(Boolean, default=True)
    enabled = Column(Boolean, default=True)
    base_currency = Column(String(5), nullable=False)
    group = Column(String(250))
    hidden = Column(Boolean, default=False)

    codes = sqlalchemy.orm.relationship("ShareCode", back_populates="share")
    transactions = sqlalchemy.orm.relationship(
        "Transaction", order_by="Transaction.date", back_populates="share"
    )
    prices = sqlalchemy.orm.relationship("SharePrice", back_populates="share")

    def __getattr__(self, attr):
        if attr == "last_price":
            try:
                return sorted(self.prices, key=lambda price: price.date)[-1]
            except IndexError:
                raise NoPriceException(
                    _("No price available for share {name} ({main_code})").format(
                        name=self.name, main_code=self.main_code
                    ),
                    self,
                )

        raise AttributeError


class ShareCode(Base):
    __tablename__ = "share_codes"
    id = Column(Integer, primary_key=True)
    share_id = Column(Integer, ForeignKey("shares.id"), nullable=False)
    origin = Column(String(250), nullable=False)
    value = Column(String(250), nullable=False)
    share = sqlalchemy.orm.relationship(Share, back_populates="codes")
