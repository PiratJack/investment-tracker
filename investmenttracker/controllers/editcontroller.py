import gettext

from PyQt5.QtWidgets import (
    QVBoxLayout,
    QDialogButtonBox,
    QGroupBox,
    QFormLayout,
    QLineEdit,
    QLabel,
    QCheckBox,
    QComboBox,
    QDialog,
)
import PyQt5.QtGui

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

        self.window = QDialog(self.parent_controller.parent_window)
        self.window.setModal(True)

        # Display content
        self.window.layout = QVBoxLayout()
        self.window.setWindowTitle(self.name)
        self.window.setLayout(self.window.layout)

        # Size & Move to center
        self.window.setMinimumSize(300, 200)
        self.window.resize(500, 300)
        # TODO: Center the dialog compared to its parent

        # Create the form
        form_group = QGroupBox("")
        self.form_layout = QFormLayout()
        form_group.setLayout(self.form_layout)
        self.window.layout.addWidget(form_group)

        # Create the fields
        for field_id in self.fields:
            field = self.fields[field_id]
            label = QLabel(_(field["label"]))

            # Create the field widget
            if field["type"] == "text":
                field["widget"] = QLineEdit()
                field["widget"].setText(field.get("default", ""))

            elif field["type"] == "list":
                field["widget"] = QComboBox()
                if "possible_values" in field:
                    field["widget"].addItem("", 0)
                    for val in field["possible_values"]:
                        field["widget"].addItem(*val)
                if "default" in field:
                    if type(field["default"]) == int:
                        field["widget"].setCurrentIndex(field["default"])
                    else:
                        field["widget"].setCurrentText(field["default"])

            elif field["type"] == "checkbox":
                field["widget"] = QCheckBox()
                field["widget"].setChecked(field.get("default", False))

            elif field["type"] == "date":
                field["widget"] = QDateEdit()
                try:
                    field["widget"].setDate(QDate.fromString(field["default"]))
                except:
                    field["widget"].setDate(QDate.currentDate())

            elif field["type"] == "float":
                field["widget"] = QLineEdit()
                field["widget"].setValidator(PyQt5.QtGui.QDoubleValidator)
                field["widget"].setText(field.get("default", ""))

            elif field["type"] == "sharelist":
                include_choice_all = field.get(include_all_choice, False)
                field["widget"] = ShareComboBox(self.database, include_choice_all)
                if "default" in field:
                    if type(field["default"]) == int:
                        field["widget"].setCurrentIndex(field["default"])
                    else:
                        field["widget"].setCurrentText(field["default"])

            # Add to layout
            self.form_layout.addRow(label, field["widget"])

        # Create the validation buttons
        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        buttonBox = QDialogButtonBox(buttons)
        buttonBox.accepted.connect(self.save)
        buttonBox.rejected.connect(self.close)

        self.window.layout.addWidget(buttonBox)

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
                elif self.fields[field_id]["type"] == "list":
                    value = field_widget.currentIndex()
                    if value == 0:
                        value = None
                else:
                    value = field_widget.isChecked()
                setattr(self.item, field_id, value)

                field_widget.setProperty("class", "")
                field_widget.style().polish(field_widget)
            except ValidationException as e:
                field_widget.setProperty("class", "validation_error")
                field_widget.style().polish(field_widget)

                error_widget = QLabel(e.message)
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
