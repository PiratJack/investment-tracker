import gettext

import models.share
from controllers.editcontroller import EditController

_ = gettext.gettext


class ShareController(EditController):
    name = _("Share")

    fields = {
        "name": {
            "label": _("Name") + " *",  # TODO: Display the star in red
            "type": "text",
        },
        "main_code": {
            "label": _("Main code"),
            "type": "text",
        },
        "sync": {
            "label": _("Get prices online?"),
            "type": "checkbox",
        },
        "enabled": {
            "label": _("Enabled"),
            "type": "checkbox",
        },
        "base_currency": {
            "label": _("Base currency"),
            "type": "list",
        },
        "hidden": {
            "label": _("Hidden"),
            "type": "checkbox",
        },
        "group_id": {
            "label": _("Group"),
            "type": "list",
        },
    }

    error_widgets = []

    def __init__(self, parent_controller, share_id=0):
        self.parent_controller = parent_controller
        self.database = parent_controller.database
        self.share_id = int(share_id)
        self.fields["group_id"]["possible_values"] = [
            (g.name, g.id) for g in self.database.share_groups_get_all()
        ]
        if share_id:
            self.item = self.database.share_get_by_id(share_id)
            self.fields["name"]["default"] = self.item.name
            self.fields["main_code"]["default"] = self.item.main_code
            self.fields["sync"]["default"] = self.item.sync
            self.fields["enabled"]["default"] = self.item.enabled
            self.fields["base_currency"]["default"] = self.item.base_currency
            self.fields["hidden"]["default"] = self.item.base_currency
            self.fields["group_id"]["default"] = (
                self.item.group.id if self.item.group else -1
            )
        else:
            self.item = models.share.Share()
            self.fields["name"]["default"] = ""
            self.fields["main_code"]["default"] = ""
            self.fields["sync"]["default"] = True
            self.fields["enabled"]["default"] = True
            self.fields["base_currency"]["default"] = ""
            self.fields["hidden"]["default"] = False
            self.fields["group_id"]["default"] = -1

    # TODO: Add codes

    def close(self):
        self.window.close()
