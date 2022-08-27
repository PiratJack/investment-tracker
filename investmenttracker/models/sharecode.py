"""SQLAlchemy-based classes for handling share codes.

Classes
----------
ShareCode
    Database class for handling share codes
"""
import gettext
import sqlalchemy.orm

from sqlalchemy import Column, ForeignKey, Integer, String, Enum

from .base import Base, ValidationException
from .share import Share, ShareDataOrigin

_ = gettext.gettext


class ShareCode(Base):
    """Database class for handling share codes

    Share codes are the IDs used by various stock price websites, apps, ...
    For example, the CAC40 index could be "1rCAC" on one site, "CAC40" on another, ...

    Attributes
    ----------
    id : int
        Unique ID
    share_id : int
        ID of the related share
    share : models.share.Share
        Related share
    origin : share.ShareDataOrigin
        The origin of this code (name of website, app, ...)
    value : str
        The actual code

    Methods
    -------
    validate_* (key, value)
        Validator for the corresponding field

    validate_missing_field (key, value, message)
        Raises a ValidationException if the corresponding field is empty
    """

    __tablename__ = "share_codes"
    id = Column(Integer, primary_key=True)
    share_id = Column(Integer, ForeignKey("shares.id"), nullable=False)
    origin = Column(Enum(ShareDataOrigin, validate_strings=True), nullable=False)
    value = Column(String(250), nullable=False)
    share = sqlalchemy.orm.relationship(Share, back_populates="codes")

    @sqlalchemy.orm.validates("share_id")
    def validate_share_id(self, key, value):
        """Ensure the share_id field is filled"""
        self.validate_missing_field(key, value, _("Missing share code share ID"))
        return value

    @sqlalchemy.orm.validates("origin")
    def validate_origin(self, key, value):
        """Ensure the origin field is filled and one of the allowed values"""
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
        """Ensure the value field is filled and has less than 250 characters"""
        self.validate_missing_field(key, value, _("Missing share code value"))
        if len(value) > 250:
            raise ValidationException(
                _("Max length for share code value is 250 characters"), self, key, value
            )
        return value

    def validate_missing_field(self, key, value, message):
        """Raises a ValidationException if the corresponding field is None or empty

        Parameters
        ----------
        key : str
            The name of the field to validate
        value : str
            The value of the field to validate
        message : str
            The message to raise if the field is empty

        Returns
        -------
        object
            The provided value"""
        if value == "" or value is None:
            raise ValidationException(message, self, key, value)
        return value

    def __repr__(self):
        """Returns a string of format ShareCode [share_name] ([value] @ [website])"""
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
