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
import PyQt5.QtCore

from models.base import NoPriceException, ValidationException


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
            label = QLabel(field["label"])

            # Create the field widget
            if field["type"] == "text":
                field["widget"] = QLineEdit()
            elif field["type"] == "list":
                field["widget"] = QComboBox()
                # TODO: Define list of possible values
            elif field["type"] == "checkbox":
                field["widget"] = QCheckBox()

            # Add default values
            if "default" in field:
                if type(field["widget"]) == QLineEdit:
                    field["widget"].setText(field["default"])
                # elif type(field['widget']) == QComboBox:
                # TODO: Default value for Combobox
                # field['widget'].setText(field['default'])
                elif type(field["widget"]) == QCheckBox:
                    field["widget"].setChecked(field["default"])

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
