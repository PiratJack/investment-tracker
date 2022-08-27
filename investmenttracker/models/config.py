"""SQLAlchemy-based classes for handling basic configuration settings

Classes
----------
Config
    Database class for handling basic configuration settings
"""
import gettext
import sqlalchemy.orm

from sqlalchemy import Column, Integer, String

from .base import Base, ValidationException

_ = gettext.gettext


class Config(Base):
    """Database class for handling basic configuration settings

    Configuration items are simple key:value pairs stored in database

    Attributes
    ----------
    id : int
        Unique ID
    name : str
        Name of the configuration item. Must be unique
    value : str
        Value of the configuration item

    Methods
    -------
    validate_* (key, value)
        Validator for the corresponding field

    validate_missing_field (key, value, message)
        Raises a ValidationException if the corresponding field is empty
    """

    __tablename__ = "config"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False, unique=True)
    value = Column(String(250), nullable=False)

    @sqlalchemy.orm.validates("name")
    def validate_name(self, key, value):
        """Ensure the name field is filled and has less than 250 characters"""
        self.validate_missing_field(key, value, _("Missing config name"))
        if len(value) > 250:
            raise ValidationException(
                _("Max length for config name is 250 characters"), self, key, value
            )
        return value

    @sqlalchemy.orm.validates("value")
    def validate_value(self, key, value):
        """Ensure the value field is filled and has less than 250 characters"""
        self.validate_missing_field(key, value, _("Missing config value"))
        if len(value) > 250:
            raise ValidationException(
                _("Max length for config value is 250 characters"), self, key, value
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

    def __repr__(self):
        """Returns string of form Config for [name]:[value]"""
        return " ".join(("Config for", self.name, ":", self.value))
