"""SQLAlchemy-based classes for handling share groups.

Classes
----------
ShareGroup
    Database class for handling share groups
"""
import gettext
import sqlalchemy.orm

from sqlalchemy import Column, Integer, String

from .base import Base, ValidationException

_ = gettext.gettext


class ShareGroup(Base):
    """Database class for handling share groups

    Share groups help users organize their shares. They have no specific meaning.

    Attributes
    ----------
    id : int
        Unique ID
    name : str
        The name of the group to display
    shares : list of models.share.Share
        List of shares within that group

    Methods
    -------
    validate_* (key, value)
        Validator for the corresponding field

    validate_missing_field (key, value, message)
        Raises a ValidationException if the corresponding field is empty
    """

    __tablename__ = "share_groups"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    shares = sqlalchemy.orm.relationship(
        "Share", order_by="Share.name", back_populates="group"
    )

    @sqlalchemy.orm.validates("name")
    def validate_name(self, key, value):
        """Validates the name field: mandatory + should have less than 250 characters"""
        self.validate_missing_field(key, value, _("Missing share group name"))
        if len(value) > 250:
            raise ValidationException(
                _("Max length for share group name is 250 characters"), self, key, value
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
        if not value:
            raise ValidationException(message, self, key, value)
        return value
