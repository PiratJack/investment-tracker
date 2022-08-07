import gettext
import datetime

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

from models.base import ValidationException, ValidationWarningException
from .widgets.sharecombobox import ShareComboBox


_ = gettext.gettext


class EditController:
    name = ""
    fields = {}
    error_widgets = []
    seen_warnings = []

    def show_window(self):
        # Discard previous ones
        if hasattr(self, "window"):
            self.window.close()
            self.window = None

        self.window = QtWidgets.QDialog(self.parent_controller.parent_window)
        self.window.setModal(True)

        # Display content
        self.window.layout = QtWidgets.QVBoxLayout()
        self.window.setWindowTitle(self.name)
        self.window.setLayout(self.window.layout)

        # Create the form
        form_group = QtWidgets.QGroupBox("")
        self.form_layout = QtWidgets.QFormLayout()
        form_group.setLayout(self.form_layout)
        self.window.layout.addWidget(form_group)

        # Create the fields
        for field_id in self.fields:
            field = self.fields[field_id]
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
                    field["widget"].setDate(QtCore.QDate.fromString(field["default"]))
                except:
                    try:
                        field["widget"].setDate(QtCore.QDate(field["default"]))
                    except:
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
                    if type(field["default"]) == int:
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
        for field_id in self.fields:
            field = self.fields[field_id]
            if "onchange" in field:
                field["onchange"]()

        # Create the validation buttons
        buttons = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        buttonBox = QtWidgets.QDialogButtonBox(buttons)
        buttonBox.accepted.connect(self.save)
        buttonBox.rejected.connect(self.close)

        self.window.layout.addWidget(buttonBox)
        # Size & Move to center
        self.window.setMinimumSize(300, 200)
        self.window.resize(self.window.layout.sizeHint())

        self.seen_warnings = []

        self.window.exec()

    def validate_data(self):
        # Clear previous errors
        has_error = False
        has_new_warnings = False
        self.clear_errors()

        # Apply user entry
        for field_id in self.fields:
            try:
                field_widget = self.fields[field_id]["widget"]

                self.set_value(field_id)
            except ValidationException as e:
                self.add_error_field(e.message, field_widget)

                has_error = True
            except ValidationWarningException as e:
                self.add_error_field(e.message, field_widget, True)

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
            except ValidationException as e:
                field_widget = self.fields[e.key]["widget"]
                self.add_error_field(e.message, field_widget)

                has_error = True
            except ValidationWarningException as e:
                field_widget = self.fields[e.key]["widget"]
                self.add_error_field(e.message, field_widget, True)

                if e.key not in self.seen_warnings:
                    has_new_warnings = True
                    self.seen_warnings.append(e.key)
                else:
                    self.item.ignore_warnings = True
                    self.set_value(e.key)
                    self.item.ignore_warnings = False

        return has_error or has_new_warnings

    def add_error_field(self, message, error_field, is_warning=False):
        error_widget = QtWidgets.QLabel(message)
        if is_warning:
            error_widget.setProperty("class", "validation_warning")
        else:
            error_widget.setProperty("class", "validation_error")
        self.error_widgets.append(error_widget)

        field_row = self.form_layout.getWidgetPosition(error_field)
        self.form_layout.insertRow(field_row[0] + 1, "", error_widget)

    def clear_errors(self):
        for error_widget in self.error_widgets:
            self.form_layout.removeRow(error_widget)
        self.error_widgets = []

    def set_value(self, field_id):
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

            if type(value) == QtCore.QDate:
                value = datetime.date.fromisoformat(value.toString(Qt.ISODate))
            elif callable(value):
                value = datetime.date.fromisoformat(value().toString(Qt.ISODate))
            elif type(value) == datetime.date:
                value = value
            elif type(value) == str:
                value = datetime.date.fromisoformat(value)
            elif type(value) == int:
                value = datetime.date.fromtimestamp(value)
            else:
                value = ""
        elif self.fields[field_id]["type"][-5:] == "float":
            value = field_widget.value()

        setattr(self.item, field_id, value)

    def save(self):
        has_error = self.validate_data()
        has_new_warnings = False

        if not has_error:
            try:
                self.database.session.add(self.item)
                self.after_item_save()
            except AttributeError:
                pass
            except ValidationException as e:
                field_widget = self.fields[e.key]["widget"]
                self.add_error_field(e.message, field_widget)

                has_error = True
            except ValidationWarningException as e:
                field_widget = self.fields[e.key]["widget"]
                self.add_error_field(e.message, field_widget, True)

                if e.key not in self.seen_warnings:
                    has_new_warnings = True
                    self.seen_warnings.append(e.key)
                else:
                    self.item.ignore_warnings = True
                    self.set_value(e.key)
                    self.item.ignore_warnings = False

            if has_error or has_new_warnings:
                return

            self.database.session.commit()

            self.parent_controller.reload_data()

            self.window.close()

    def close(self):
        self.window.close()
