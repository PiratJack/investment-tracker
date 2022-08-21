import gettext

import models.sharegroup
from controllers.editcontroller import EditController

_ = gettext.gettext


class ShareGroupController(EditController):
    name = _("Group")

    fields = {
        "name": {
            "label": _("Name"),
            "type": "text",
            "mandatory": True,
        },
    }

    error_widgets = []

    def __init__(self, parent_controller, group_id=0):
        super().__init__(parent_controller)
        self.group_id = int(group_id)
        if self.group_id:
            self.item = self.database.share_group_get_by_id(self.group_id)
        else:
            self.item = models.sharegroup.ShareGroup()
        self.fields["name"]["default"] = self.item.name
