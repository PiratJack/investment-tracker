import gettext
import sqlalchemy.orm

from sqlalchemy import Column, Integer, String

from .base import Base, ValidationException

_ = gettext.gettext


class Config(Base):
    __tablename__ = "config"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False, unique = True)
    value = Column(String(250), nullable=False)

    @sqlalchemy.orm.validates("name")
    def validate_name(self, key, value):
        self.validate_missing_field(key, value, _("Missing config name"))
        if len(value) > 250:
            raise ValidationException(
                _("Max length for config name is 250 characters"), self, key, value
            )
        return value

    @sqlalchemy.orm.validates("value")
    def validate_value(self, key, value):
        self.validate_missing_field(key, value, _("Missing config value"))
        if len(value) > 250:
            raise ValidationException(
                _("Max length for config value is 250 characters"), self, key, value
            )
        return value

    def validate_missing_field(self, key, value, message):
        if value == "" or value is None:
            raise ValidationException(message, self, key, value)
        return value

    def __repr__(self):
        return " ".join(("Config for", self.name, ":", self.value))
