import gettext

import models.transaction
from controllers.editcontroller import EditController

_ = gettext.gettext


class TransactionController(EditController):
    name = _("Transaction")

    fields = {
        "account_id": {
            "label": _("Account"),
            "type": "list",
        },
        "date": {
            "label": _("Date"),
            "type": "date",
        },
        "label": {
            "label": _("Label"),
            "type": "text",
        },
        "type": {
            "label": _("Type"),
            "type": "list",
        },
        "quantity": {
            "label": _("Asset delta"),
            "type": "float",
        },
        "share_id": {
            "label": _("Share"),
            "type": "sharelist",
        },
        "unit_price": {
            "label": _("Rate"),
            "type": "float",
        },
        "currency_delta": {
            "label": _("Currency delta"),
            "type": "float",
        },
    }

    error_widgets = []

    def __init__(self, parent_controller, transaction_id=0):
        self.parent_controller = parent_controller
        self.database = parent_controller.database
        self.transaction_id = int(transaction_id)
        self.fields["account_id"]["possible_values"] = [
            (g.name, g.id) for g in self.database.accounts_get()
        ]
        self.fields["type"]["possible_values"] = [
            (g.value["name"], g.name) for g in models.transaction.TransactionTypes
        ]
        if transaction_id:
            self.item = self.database.transaction_get_by_id(transaction_id)
            self.fields["account_id"]["default"] = self.item.account_id
            self.fields["date"]["default"] = self.item.date
            self.fields["label"]["default"] = self.item.label
            self.fields["type"]["default"] = self.item.type.name
            self.fields["quantity"]["default"] = self.item.quantity
            self.fields["share_id"]["default"] = self.item.share_id
            self.fields["unit_price"]["default"] = self.item.unit_price

        else:
            self.item = models.transaction.Transaction()

    def close(self):
        self.window.close()
