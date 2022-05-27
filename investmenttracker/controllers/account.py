import gettext

import models.account
from controllers.editcontroller import EditController

_ = gettext.gettext


class AccountController(EditController):
    name = _("Account")

    fields = {
        "name": {
            "label": _("Name"),  # TODO: Display a star in red
            "type": "text",
        },
        "code": {
            "label": _("Code"),
            "type": "text",
        },
        "base_currency_id": {
            "label": _("Currency"),
            "type": "sharelist",
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
        self.parent_controller = parent_controller
        self.database = parent_controller.database
        self.account_id = int(account_id)
        if account_id:
            self.item = self.database.accounts_get_by_id(account_id)
            self.fields["name"]["default"] = self.item.name
            self.fields["code"]["default"] = self.item.code
            self.fields["base_currency_id"]["default"] = (
                self.item.base_currency.id if self.item.base_currency else 0
            )
            self.fields["enabled"]["default"] = self.item.enabled
        else:
            self.item = models.account.Account()
            self.fields["enabled"]["default"] = True

    def close(self):
        self.window.close()
