import gettext

import models.share
import models.sharecode
from controllers.editcontroller import EditController

_ = gettext.gettext


class ShareController(EditController):
    name = _("Share")

    fields = {
        "name": {
            "label": _("Name"),  # TODO (cosmetic): Display a star in red
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
        "base_currency_id": {
            "label": _("Base currency"),
            "type": "sharelist",
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
        self.fields["base_currency_id"]["excluded"] = self.share_id
        if share_id:
            self.item = self.database.share_get_by_id(share_id)
        else:
            self.item = models.share.Share()
        self.fields["name"]["default"] = self.item.name
        self.fields["main_code"]["default"] = self.item.main_code
        self.fields["sync"]["default"] = self.item.sync
        self.fields["enabled"]["default"] = self.item.enabled
        self.fields["base_currency_id"]["default"] = (
            self.item.base_currency.id if self.item.base_currency else 0
        )
        self.fields["hidden"]["default"] = self.item.hidden
        self.fields["group_id"]["default"] = (
            self.item.group.id if self.item.group else 0
        )

        print(self.item.codes)
        print(self.fields)

        for origin in models.sharecode.ShareCodeOrigin:
            self.fields["code_" + origin.name] = {
                "label": _("Code for {origin}").format(origin=origin.value["name"]),
                "type": "text",
                "default": "",
            }
        if self.item.codes:
            for code in self.item.codes:
                self.fields["code_" + code.origin.name]["default"] = code.value

    def validate_data(self):
        super().validate_data()
        for origin in models.sharecode.ShareCodeOrigin:
            value = getattr(self.item, "code_" + origin.name)
            existing_code = [code for code in self.item.codes if code.origin == origin]
            if value:
                if existing_code:
                    existing_code[0].value = value
                else:
                    new_code = models.sharecode.ShareCode(
                        share_id=self.item.id, origin=origin.name, value=value
                    )
                    self.item.codes.append(new_code)
            else:
                if existing_code:
                    self.database.delete(existing_code[0])

    def close(self):
        self.window.close()
