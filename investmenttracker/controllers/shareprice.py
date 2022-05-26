import gettext

import models.shareprice
from controllers.editcontroller import EditController

_ = gettext.gettext


class SharePriceController(EditController):
    name = _("Share Price")

    fields = {
        "share": {
            "label": _("Share"),  # TODO: Display a star in red
            "type": "sharelist",
            "include_all_choice": False,
        },
        "date": {
            "label": _("Date"),
            "type": "date",
        },
        "price": {
            "label": _("Price"),
            "type": "float",
        },
        "currency": {
            "label": _("Currency"),
            "type": "sharelist",
            "include_all_choice": False,
        },
        "source": {
            "label": _("Source"),
            "type": "text",
        },
    }

    error_widgets = []

    def __init__(self, parent_controller, share_price_id=0):
        self.parent_controller = parent_controller
        self.database = parent_controller.database
        self.share_price_id = int(share_price_id)
        if self.share_price_id:
            self.item = self.database.share_price_get_by_id(share_price_id)
            self.fields["share"]["default"] = self.item.share
            self.fields["date"]["default"] = self.item.date
            self.fields["price"]["default"] = self.item.price
            self.fields["currency_id"]["excluded"] = (
                self.item.share.id if self.item.share else 0
            )
            self.fields["source"]["default"] = self.item.source
        else:
            self.item = models.shareprice.SharePrice()
            self.fields["share"]["default"] = ""
            self.fields["date"]["default"] = ""
            self.fields["price"]["default"] = 0
            self.fields["currency_id"]["default"] = 0
            self.fields["source"]["default"] = ""

    def close(self):
        self.window.close()
