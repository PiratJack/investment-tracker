"""Controller for creating or editing a single account

Classes
----------
AccountController
    Controller for creating or editing a single account
"""
import gettext

import models.account
from controllers.editcontroller import EditController

_ = gettext.gettext


class AccountController(EditController):
    """Controller for creating or editing a single transaction

    Attributes
    ----------
    name : str
        Name of the controller - used in display
    fields : dict of fields
        Which fields to display for edition.
        Refer to widgets.EditController for the dict format

    parent_controller : QtWidgets.QMainWindow
        The main window displaying this widget
    error_widgets : dict
        Which fields have errors
        Format: {field_id: "error message"}

    account_id : int
        The ID of the account to edit. 0 for new accounts.
    item : models.account.Account
        The account being edited or created
    """

    name = _("Account")

    fields = {
        "name": {
            "label": _("Name"),
            "type": "text",
            "mandatory": True,
        },
        "code": {
            "label": _("Code"),
            "type": "text",
        },
        "base_currency_id": {
            "label": _("Currency"),
            "type": "sharelist",
            "mandatory": True,
        },
        "enabled": {
            "label": _("Active"),
            "type": "checkbox",
        },
        "hidden": {
            "label": _("Hidden"),
            "type": "checkbox",
        },
    }

    error_widgets = []

    def __init__(self, parent_controller, account_id=0):
        """Sets up all data required to display the screen

        For each fields, sets up the "default" value, based on existing database data

        Parameters
        ----------
        parent_controller : controllers.TransactionsController
            The controller displaying this class
        account_id : int
            The ID of the account to edit. 0 for creating a new one.
        """
        super().__init__(parent_controller)
        self.account_id = int(account_id) if account_id else 0

        if self.account_id:
            self.item = self.database.account_get_by_id(account_id)
        else:
            self.item = models.account.Account()

        self.fields["name"]["default"] = self.item.name
        self.fields["code"]["default"] = self.item.code
        self.fields["base_currency_id"]["default"] = (
            self.item.base_currency.id if self.item.base_currency else 0
        )
        self.fields["enabled"]["default"] = self.item.enabled
