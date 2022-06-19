import gettext
import sqlalchemy.orm

from sqlalchemy import Column, ForeignKey, Integer, String, Float, Date

from .base import Base, ValidationException

_ = gettext.gettext


class SharePrice(Base):
    __tablename__ = "share_prices"
    id = Column(Integer, primary_key=True)
    share_id = Column(Integer, ForeignKey("shares.id"), nullable=False)
    date = Column(Date, nullable=False)
    price = Column(Float, nullable=False)
    currency_id = Column(Integer, ForeignKey("shares.id"), nullable=False)
    source = Column(String(250), nullable=False)

    share = sqlalchemy.orm.relationship(
        "Share", back_populates="prices", foreign_keys=share_id
    )
    currency = sqlalchemy.orm.relationship("Share", foreign_keys=currency_id)

    @sqlalchemy.orm.validates("share_id")
    def validate_share_id(self, key, value):
        self.validate_missing_field(key, value, _("Missing share price share ID"))
        if value is not None and value == self.currency_id:
            raise ValidationException(
                _("Share Price currency can't be the share itself"), self, key, value
            )
        return value

    @sqlalchemy.orm.validates("date")
    def validate_date(self, key, value):
        self.validate_missing_field(key, value, _("Missing share price date"))
        return value

    @sqlalchemy.orm.validates("price")
    def validate_price(self, key, value):
        self.validate_missing_field(key, value, _("Missing share price actual price"))
        return value

    @sqlalchemy.orm.validates("currency_id")
    def validate_currency(self, key, value):
        self.validate_missing_field(key, value, _("Missing share price currency"))
        if value is not None and value == self.share_id:
            raise ValidationException(
                _("Share Price currency can't be the share itself"), self, key, value
            )
        return value

    @sqlalchemy.orm.validates("source")
    def validate_source(self, key, value):
        self.validate_missing_field(key, value, _("Missing share price source"))
        if len(value) > 250:
            raise ValidationException(
                _("Max length for share price source is 250 characters"),
                self,
                key,
                value,
            )
        return value

    def validate_missing_field(self, key, value, message):
        if value == "" or value is None:
            raise ValidationException(message, self, key, value)
        return value

    def __repr__(self):
        output = [
            "Price (",
            self.share.name + " at " if self.share else "",
            str(self.price)
            + " "
            + str(self.currency.main_code if self.currency.main_code else self.currency)
            if self.price and self.currency
            else "Unknown",
            " on " + str(self.date) if self.date else "",
            ")",
        ]
        return "".join(output)

    def short_name(self):
        output = [
            str(self.price)
            + " "
            + str(self.currency.main_code if self.currency.main_code else self.currency)
            if self.price and self.currency
            else "Unknown",
            " on " + str(self.date) if self.date else "",
        ]
        return "".join(output)
