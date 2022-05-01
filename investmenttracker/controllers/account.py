import gettext

from PyQt5.QtGui import QIcon, QRegExpValidator, QValidator
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QFormLayout,
    QLineEdit,
    QLabel,
    QCheckBox,
    QComboBox,
)
import PyQt5.QtCore

from models.base import NoPriceException
import models.shareprice
from models.base import ValidationException


_ = gettext.gettext


class AccountController:
    name = "Account"

    fields = {
        "name": {
            "label": _("Name") + " *",  # TODO: Display the star in red
            "type": "text",
        },
        "code": {
            "label": _("Code"),
            "type": "text",
        },
        "base_currency": {
            "label": _("Currency"),
            "type": "list",
        },
        "enabled": {
            "label": _("Active"),
            "type": "checkbox",
            "default": True,
        },
    }

    error_widgets = []

    def __init__(self, parent_window, database, account_id=0):
        self.parent_window = parent_window
        self.database = database
        self.account_id = int(account_id)
        if account_id:
            self.account = self.database.accounts_get_by_id(account_id)
            self.fields["name"]["default"] = self.account.name
            self.fields["code"]["default"] = self.account.code
            self.fields["base_currency"]["default"] = self.account.base_currency
            self.fields["name"]["enabled"] = self.account.enabled

    def show_window(self):
        # Discard previous ones
        if hasattr(self, "window"):
            self.window.close()
            self.window = None

        self.window = QDialog()
        self.window.setAttribute(PyQt5.QtCore.Qt.WA_DeleteOnClose)

        # Display content
        self.window.layout = QVBoxLayout()
        self.window.setWindowTitle(_("Account"))
        self.window.setLayout(self.window.layout)

        # Size & Move to center
        self.window.setMinimumSize(300, 200)
        self.window.resize(500, 300)
        # TODO: Center the dialog compared to its parent
        # TODO: Ensure this dialog is closed once its parent is closed
        # print ('#######')
        # print ('before')
        # print ('window', self.window.geometry())
        # print ('window x', self.window.pos().x())
        # print ('window y', self.window.pos().y())
        # print ('parent', self.parent.geometry())
        # print ('parent', self.parent.geometry().center())
        # qtRectangle = self.window.geometry()
        # centerPoint = self.parent.geometry().center()
        # qtRectangle.moveCenter(centerPoint)
        # self.window.move(qtRectangle.topLeft())
        # print ('after')
        # print ('qtRectangle', qtRectangle.topLeft())
        # print ('qtRectangle', self.window.geometry().topLeft())
        # print ('window', self.window.geometry())

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
                # TODO: Default value for currency
                # field['widget'].setText(field['default'])
                elif type(field["widget"]) == QCheckBox:
                    field["widget"].setChecked(field["default"])

            # Add to layout
            self.form_layout.addRow(label, field["widget"])

        # Create the validation buttons
        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        buttonBox = QDialogButtonBox(buttons)
        buttonBox.accepted.connect(self.save_account)
        buttonBox.rejected.connect(self.close)

        self.window.layout.addWidget(buttonBox)

        self.window.show()

    def save_account(self):
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
                setattr(self.account, field_id, value)

                field_widget.setStyleSheet("")
            except ValidationException as e:
                field_widget.setStyleSheet(
                    "QLineEdit {{ background-color: {color} }}".format(color="#f6989d")
                )

                error_widget = QLabel(e.message)
                self.error_widgets.append(error_widget)
                field_row = self.form_layout.getWidgetPosition(field_widget)
                self.form_layout.insertRow(field_row[0] + 1, "", error_widget)
                has_error = True

        if not has_error:
            self.database.session.add(self.account)
            self.database.session.commit()

            self.window.close()

    def close(self):
        self.window.close()
