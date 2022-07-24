import gettext

import models.sharegroup
from controllers.editcontroller import EditController

_ = gettext.gettext


class ShareGroupController(EditController):
    name = _("Group")

    fields = {
        "name": {
            "label": _("Name"),  # TODO (cosmetic): Display a star in red
            "type": "text",
        },
    }

    error_widgets = []

    def __init__(self, parent_controller, group_id=0):
        self.parent_controller = parent_controller
        self.database = parent_controller.database
        self.group_id = int(group_id)
        if group_id:
            self.item = self.database.share_group_get_by_id(group_id)
        else:
            self.item = models.sharegroup.ShareGroup()
        self.fields["name"]["default"] = self.item.name

    def close(self):
        self.window.close()
