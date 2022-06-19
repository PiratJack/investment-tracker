import gettext
import datetime

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

from models.base import ValidationException
from .widgets.sharecombobox import ShareComboBox


_ = gettext.gettext


class EditController:
    name = ""
    fields = {}
    error_widgets = []

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
                include_choice_all = field.get("include_all_choice", False)
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
        # TODO: Center the dialog compared to its parent

        self.window.exec()

    def validate_data(self):
        # Clear previous errors
        has_error = False
        for error_widget in self.error_widgets:
            self.form_layout.removeRow(error_widget)
        self.error_widgets = []

        # Apply user entry
        for field_id in self.fields:
            try:
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
                        value = datetime.datetime.fromisoformat(
                            value.toString(Qt.ISODate)
                        )
                    elif callable(value):
                        value = datetime.datetime.fromisoformat(
                            value().toString(Qt.ISODate)
                        )
                    elif type(value) == datetime.datetime:
                        value = value
                    elif type(value) == str:
                        value = datetime.datetime.fromisoformat(value)
                    elif type(value) == int:
                        value = datetime.datetime.fromtimestamp(value)
                    else:
                        value = ""
                elif self.fields[field_id]["type"][-5:] == "float":
                    value = field_widget.value()

                setattr(self.item, field_id, value)

                field_widget.setProperty("class", "")
                field_widget.style().polish(field_widget)
            except ValidationException as e:
                field_widget.setProperty("class", "validation_error")
                field_widget.style().polish(field_widget)

                error_widget = QtWidgets.QLabel(e.message)
                self.error_widgets.append(error_widget)
                field_row = self.form_layout.getWidgetPosition(field_widget)
                self.form_layout.insertRow(field_row[0] + 1, "", error_widget)
                has_error = True

        return has_error

    def save(self):
        has_error = self.validate_data()

        if not has_error:
            self.database.session.add(self.item)
            self.database.session.commit()

            self.parent_controller.reload_data()

            self.window.close()

    def close(self):
        self.window.close()
