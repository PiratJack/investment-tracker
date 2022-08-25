"""Controller for editing items - should be used only as base class (not directly)

Classes
----------
AccountController
    Controller for editing items - should be used only as base class (not directly)
"""
import gettext
import datetime

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

from models.base import ValidationException, ValidationWarningException
from controllers.widgets.sharecombobox import ShareComboBox


_ = gettext.gettext


class EditController:
    """Controller for editing items - should be used only as base class (not directly)

    This controller facilitates the display of various fields for editing items.
    The fields can be of different types:
        Text: free text
        List: a list of possible values (dropdown list)
        Checkbox: a true/false checkbox
        Date: a date
        Float: a numeric value
        Sharelist: a share from the database (uses widget ShareComboBox)
    Each field may be mandatory, have a handler for change, default values, ...

    Attributes
    ----------
    name : str
        Name of the controller - used in display
    fields : dict of fields
        Which fields to display for edition.
        The key should be the ID of the field (as is stored in the database)
        The value is a dict with the following keys:
            name (mandatory): the label to display
            type (mandatory): which field type to display.
                Can be text, list, checkbox, date, float or sharelist
            onchange (optional): the handler to call when data is changed by the user
            possible_values (mandatory for combobox): the list of possible values
            default (optional, default to blank): the value to display at the start
            widget (added by this controller): the QWidget item to display in the screen
            excluded (only for sharelist type): forbidden value
            mandatory (optional, default to False): whether the field is mandatory
    error_widgets : dict
        Which fields have errors
        Format: {field_id: "error message"}
    seen_warnings : dict
        Which fields have warnings that the user saw already (and thus are non-blocking)
        Format: {field_id: "error message"}
    item : model.*.*
        The item being edited or created

    parent_controller : *Controller
        The controller displaying this edit dialog

    window : QtWidgets.QDialog
        The window to display
    layout : QtWidgets.QVBoxLayout
        The layout of the window
    form_layout : QtWidgets.QFormLayout
        The layout of the form displayed

    Methods
    -------
    __init__ (parent_controller)
        Stores parameters & creates all UI elements
    show_window
        Displays the dialog
    validate_data
        Validates the entered data
            Checks if fields have the right format
            Checks if models raise any error for this field
    add_error_field (message, error_field, is_warning=False)
        Displays an error
    clear_errors
        Clears all errors
    set_value (field_id)
        Sets the value for a single field on the database model being edited/created
    save (field_id)
        Saves the database model being edited/created
    close
        Closes the dialog
    """

    name = ""
    fields = {}

    error_widgets = []
    seen_warnings = []

    def __init__(self, parent_controller):
        """Stores parameters & creates all UI elements

        Parameters
        ----------
        parent_controller : QtWidgets.QMainWindow
            The main window displaying this controller
        """
        self.parent_controller = parent_controller
        self.database = parent_controller.database
        self.item = None

        self.window = QtWidgets.QDialog(self.parent_controller.parent_window)
        self.layout = QtWidgets.QVBoxLayout()
        self.form_layout = QtWidgets.QFormLayout()

    def show_window(self):
        """Displays the dialog based on self.fields"""
        # Discard previous windows
        if self.window:
            self.window.close()
            self.window = QtWidgets.QDialog(self.parent_controller.parent_window)

        self.window.setModal(True)

        # Display content
        self.window.setWindowTitle(self.name)
        self.window.setLayout(self.layout)

        # Create the form
        form_group = QtWidgets.QGroupBox("")
        form_group.setLayout(self.form_layout)
        self.layout.addWidget(form_group)

        # Create the fields
        for field in self.fields.values():
            label = QtWidgets.QLabel(_(field["label"]))
            if field.get("mandatory", False):
                label.setText(
                    _(field["label"]) + '<span style="color:orange;"> *</span>'
                )

            # Create the field widget
            if field["type"] == "text":
                field["widget"] = QtWidgets.QLineEdit()
                field["widget"].setText(field.get("default", ""))
                if "onchange" in field:
                    field["widget"].textChanged.connect(field["onchange"])

            elif field["type"] == "list":
                field["widget"] = QtWidgets.QComboBox()
                if "possible_values" in field:
                    field["widget"].addItem("", 0)
                    for val in field["possible_values"]:
                        field["widget"].addItem(*val)
                if "default" in field:
                    field["widget"].setCurrentIndex(
                        field["widget"].findData(field["default"])
                    )
                if "onchange" in field:
                    field["widget"].currentIndexChanged.connect(field["onchange"])

            elif field["type"] == "checkbox":
                field["widget"] = QtWidgets.QCheckBox()
                field["widget"].setChecked(field.get("default", False))
                if "onchange" in field:
                    field["widget"].stateChanged.connect(field["onchange"])

            elif field["type"] == "date":
                field["widget"] = QtWidgets.QDateEdit()
                width = field["widget"].sizeHint().width()
                field["widget"].setMinimumWidth(width * 2)

                try:
                    field["widget"].setDate(
                        QtCore.QDate.fromString(field["default"], "yyyy-MM-dd")
                    )
                except (ValueError, TypeError):
                    try:
                        field["widget"].setDate(QtCore.QDate(field["default"]))
                    except (ValueError, TypeError):
                        field["widget"].setDate(QtCore.QDate.currentDate())
                except KeyError:
                    field["widget"].setDate(QtCore.QDate.currentDate())

                if "onchange" in field:
                    field["widget"].dateChanged.connect(field["onchange"])

            elif field["type"][-5:] == "float":
                field["widget"] = QtWidgets.QDoubleSpinBox()

                field["widget"].setDecimals(6)

                if field["type"] == "positivefloat":
                    field["widget"].setMinimum(0)
                field["widget"].setMaximum(10**10)

                field["widget"].setValue(field.get("default", 0))

                if "onchange" in field:
                    field["widget"].valueChanged.connect(field["onchange"])

            elif field["type"] == "sharelist":
                include_choice_all = field.get("include_choice_all", False)
                field["widget"] = ShareComboBox(
                    self.database, include_choice_all=include_choice_all
                )

                if "default" in field:
                    if isinstance(field["default"], int):
                        index = field["widget"].findData(field["default"])
                        field["widget"].setCurrentIndex(index)
                    else:
                        field["widget"].setCurrentText(field["default"])
                if "excluded" in field:
                    index = field["widget"].findData(field["excluded"])
                    field["widget"].removeItem(index)
                if "onchange" in field:
                    field["widget"].currentIndexChanged.connect(field["onchange"])

            # Expand horizontally + Add to layout
            field["widget"].setSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
            )
            self.form_layout.addRow(label, field["widget"])

        # Trigger onchange events to ensure consistency
        for field in self.fields.values():
            if "onchange" in field:
                field["onchange"]()

        # Create the validation buttons
        buttons = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        button_box = QtWidgets.QDialogButtonBox(buttons)
        button_box.accepted.connect(self.save)
        button_box.rejected.connect(self.close)

        self.layout.addWidget(button_box)
        # Size & Move to center
        self.window.setMinimumSize(300, 200)
        self.window.resize(self.layout.sizeHint())

        self.seen_warnings = []

        self.window.exec()

    def validate_data(self):
        """Validates the entered data

        Checks if fields have the right format
        Checks if models raise any error for this field
        Displays any error or warning raised
        If warnings have already been seen, they will no longer be blocking the save

        Triggers self.on_validation_end() for additional validations
        """

        # Clear previous errors
        has_error = False
        has_new_warnings = False
        self.clear_errors()

        # Apply user entry
        for field_id, field in self.fields.items():
            field_widget = field["widget"]
            try:
                self.set_value(field_id)
            except ValidationException as exception:
                self.add_error_field(exception.message, field_widget)

                has_error = True
            except ValidationWarningException as exception:
                self.add_error_field(exception.message, field_widget, True)

                if field_id not in self.seen_warnings:
                    has_new_warnings = True
                    self.seen_warnings.append(field_id)
                else:
                    self.item.ignore_warnings = True
                    self.set_value(field_id)
                    self.item.ignore_warnings = False

        if not has_error:
            try:
                self.on_validation_end()
            except AttributeError:
                pass
            except ValidationException as exception:
                field_widget = self.fields[exception.key]["widget"]
                self.add_error_field(exception.message, field_widget)

                has_error = True
            except ValidationWarningException as exception:
                field_widget = self.fields[exception.key]["widget"]
                self.add_error_field(exception.message, field_widget, True)

                if exception.key not in self.seen_warnings:
                    has_new_warnings = True
                    self.seen_warnings.append(exception.key)
                else:
                    self.item.ignore_warnings = True
                    self.set_value(exception.key)
                    self.item.ignore_warnings = False

        return has_error or has_new_warnings

    def add_error_field(self, message, error_field, is_warning=False):
        """Displays errors on the screen

        Parameters
        ----------
        message : str
            The error message to display
        error_field : QWidget
            The widget with the bad data
        is_warning : bool
            Whether the error is a warning or not (displays differently)
        """
        error_widget = QtWidgets.QLabel(message)
        if is_warning:
            error_widget.setProperty("class", "validation_warning")
        else:
            error_widget.setProperty("class", "validation_error")
        self.error_widgets.append(error_widget)

        field_row = self.form_layout.getWidgetPosition(error_field)
        self.form_layout.insertRow(field_row[0] + 1, "", error_widget)

    def clear_errors(self):
        """Removes all errors being displayed"""
        for error_widget in self.error_widgets:
            self.form_layout.removeRow(error_widget)
        self.error_widgets = []

    def set_value(self, field_id):
        """Sets the value for a single field on the database model being edited/created

        Warnings and errors will be raised by the DB as exceptions
        Those exceptions will be handled by the caller self.validate_data()

        Parameters
        ----------
        field_id : str
            The ID of the field being validated/Set"""
        field_widget = self.fields[field_id]["widget"]
        if self.fields[field_id]["type"] == "text":
            value = field_widget.text()
        elif self.fields[field_id]["type"] in ("list", "sharelist"):
            value = field_widget.currentData()
            if value == 0:
                value = None
        elif self.fields[field_id]["type"] == "checkbox":
            value = field_widget.isChecked()
        elif self.fields[field_id]["type"] == "date":
            value = field_widget.date

            if isinstance(value, QtCore.QDate):
                value = datetime.date.fromisoformat(value.toString(Qt.ISODate))
            elif callable(value):
                value = datetime.date.fromisoformat(value().toString(Qt.ISODate))
            elif isinstance(value, datetime.date):
                pass
            elif isinstance(value, str):
                value = datetime.date.fromisoformat(value)
            elif isinstance(value, int):
                value = datetime.date.fromtimestamp(value)
            else:
                value = ""
        elif self.fields[field_id]["type"][-5:] == "float":
            value = field_widget.value()

        setattr(self.item, field_id, value)

    def save(self):
        """Saves the database model being edited/created

        Calls self.after_item_save() after saving.
        If that raises exceptions, they will be displayed (data will not be saved)"""
        has_error = self.validate_data()
        has_new_warnings = False

        if not has_error:
            try:
                self.database.session.add(self.item)
                self.after_item_save()
            except AttributeError:
                pass
            except ValidationException as exception:
                field_widget = self.fields[exception.key]["widget"]
                self.add_error_field(exception.message, field_widget)

                has_error = True
            except ValidationWarningException as exception:
                field_widget = self.fields[exception.key]["widget"]
                self.add_error_field(exception.message, field_widget, True)

                if exception.key not in self.seen_warnings:
                    has_new_warnings = True
                    self.seen_warnings.append(exception.key)
                else:
                    self.item.ignore_warnings = True
                    self.set_value(exception.key)
                    self.item.ignore_warnings = False

            if has_error or has_new_warnings:
                return

            self.database.session.commit()

            self.parent_controller.reload_data()

            self.window.close()

    def close(self):
        """Closes the dialog"""
        self.window.close()
