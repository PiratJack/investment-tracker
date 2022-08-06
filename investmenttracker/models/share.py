import enum
import gettext
import datetime
import sqlalchemy.orm

from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Enum

from .base import Base, NoPriceException, ValidationException

_ = gettext.gettext


class ShareDataOrigin(enum.Enum):
    alphavantage = {
        "name": "Alphavantage",
    }
    boursorama = {
        "name": "Boursorama",
    }
    quantalys = {
        "name": "Quantalys",
    }


class Share(Base):
    __tablename__ = "shares"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    main_code = Column(String(250), nullable=True)
    sync_origin = Column(Enum(ShareDataOrigin, validate_strings=True), nullable=True)
    hidden = Column(Boolean, default=False)

    group_id = Column(Integer, ForeignKey("share_groups.id"), nullable=True)
    group = sqlalchemy.orm.relationship("ShareGroup", back_populates="shares")

    base_currency_id = Column(Integer, ForeignKey("shares.id"), nullable=True)
    base_currency = sqlalchemy.orm.relationship("Share", remote_side=[id])

    # used_by = sqlalchemy.orm.relationship("Share", back_populates="base_currency")

    codes = sqlalchemy.orm.relationship("ShareCode", back_populates="share")
    transactions = sqlalchemy.orm.relationship(
        "Transaction", order_by="Transaction.date", back_populates="share"
    )
    prices = sqlalchemy.orm.relationship(
        "SharePrice",
        back_populates="share",
        remote_side="[SharePrice.share_id]",
        primaryjoin="SharePrice.share_id==Share.id",
    )

    def __init__(self, **kwargs):
        if "hidden" not in kwargs:
            kwargs["hidden"] = self.__table__.c.hidden.default.arg
        super().__init__(**kwargs)

    def __getattr__(self, attr):
        if attr == "last_price":
            try:
                prices = [
                    price
                    for price in self.prices
                    if price.date
                    >= datetime.date.today() + datetime.timedelta(days=-31)
                ]
                return sorted(prices, key=lambda price: price.date)[-1]
            except IndexError:
                raise NoPriceException(
                    _("No price available for share {name} ({main_code})").format(
                        name=self.name, main_code=self.main_code
                    ),
                    self,
                ) from None

        # Display in graph
        if attr == "graph_label":
            return self.name + (
                " (" + self.base_currency.name + ")" if self.base_currency else ""
            )

        raise AttributeError("'Share' object has no attribute '" + attr + "'")

    @sqlalchemy.orm.validates("main_code")
    def validate_main_code(self, key, value):
        if len(value) > 250:
            raise ValidationException(
                _("Max length for share main code is 250 characters"), self, key, value
            )
        return value

    @sqlalchemy.orm.validates("name")
    def validate_name(self, key, value):
        self.validate_missing_field(key, value, _("Missing share name"))
        if len(value) > 250:
            raise ValidationException(
                _("Max length for share name is 250 characters"), self, key, value
            )
        return value

    @sqlalchemy.orm.validates("base_currency_id")
    def validate_base_currency_id(self, key, value):
        if value is not None and value == self.id:
            raise ValidationException(
                _("Share base currency can't be itself"), self, key, value
            )
        return value

    @sqlalchemy.orm.validates("base_currency")
    def validate_base_currency(self, key, value):
        if value is not None and value.id == self.id:
            raise ValidationException(
                _("Share base currency can't be itself"), self, key, value
            )
        return value

    def validate_missing_field(self, key, value, message):
        if value == "" or value is None:
            raise ValidationException(message, self, key, value)
        return value

    def __repr__(self):
        output = "Share " + self.name + " ("
        if self.main_code:
            output += self.main_code + ", "
        if self.base_currency:
            output += self.base_currency.main_code + ", "
        output += "synced" if self.sync_origin else "unsynced"
        output += ")"
        return output

    def short_name(self):
        output = self.name
        if self.main_code:
            output += " (" + self.main_code + ")"
        return output
