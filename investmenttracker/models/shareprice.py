import gettext
import sqlalchemy.orm

from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Float, Date

from .base import Base

_ = gettext.gettext


class SharePrice(Base):
    __tablename__ = "share_prices"
    id = Column(Integer, primary_key=True)
    share_id = Column(Integer, ForeignKey("shares.id"), nullable=False)
    date = Column(Date, nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String(5), nullable=False)
    source = Column(String(250), nullable=False)
    share = sqlalchemy.orm.relationship("Share", back_populates="prices")
