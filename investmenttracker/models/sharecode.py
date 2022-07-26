import gettext
import sqlalchemy.orm

from sqlalchemy import Column, ForeignKey, Integer, String, Enum

from .base import Base, ValidationException
from .share import Share, ShareDataOrigin

_ = gettext.gettext


class ShareCode(Base):
    __tablename__ = "share_codes"
    id = Column(Integer, primary_key=True)
    share_id = Column(Integer, ForeignKey("shares.id"), nullable=False)
    origin = Column(Enum(ShareDataOrigin, validate_strings=True), nullable=False)
    value = Column(String(250), nullable=False)
    share = sqlalchemy.orm.relationship(Share, back_populates="codes")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @sqlalchemy.orm.validates("share_id")
    def validate_share_id(self, key, value):
        self.validate_missing_field(key, value, _("Missing share code share ID"))
        return value

    @sqlalchemy.orm.validates("origin")
    def validate_origin(self, key, value):
        self.validate_missing_field(key, value, _("Missing share code origin"))
        if value not in self.__table__.columns["origin"].type.enums:
            raise ValidationException(
                _("Sharecode origin is invalid"),
                self,
                key,
                value,
            )
        return value

    @sqlalchemy.orm.validates("value")
    def validate_value(self, key, value):
        self.validate_missing_field(key, value, _("Missing share code value"))
        if len(value) > 250:
            raise ValidationException(
                _("Max length for share code value is 250 characters"), self, key, value
            )
        return value

    def validate_missing_field(self, key, value, message):
        if value == "" or value is None:
            raise ValidationException(message, self, key, value)
        return value

    def __repr__(self):
        if self.share:
            return (
                "ShareCode "
                + self.share.name
                + " ("
                + str(self.value)
                + " @ "
                + str(self.origin.value["name"])
                + ")"
            )
        return "ShareCode (" + str(self.value) + " @ " + str(self.origin) + ")"
