import gettext
import sqlalchemy.orm

from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Float, Date, Enum

from .base import Base, NoPriceException, ValidationException
from .share import Share

_ = gettext.gettext


class ShareGroup(Base):
    __tablename__ = "share_groups"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    shares = sqlalchemy.orm.relationship(
        "Share", order_by="Share.name", back_populates="group"
    )

    @sqlalchemy.orm.validates("name")
    def validate_name(self, key, value):
        self.validate_missing_field(key, value, _("Missing share group name"))
        if len(value) > 250:
            raise ValidationException(
                _("Max length for share group name is 250 characters"), self, key, value
            )
        return value

    def validate_missing_field(self, key, value, message):
        if value == "" or value is None:
            raise ValidationException(message, self, key, value)
        return value
