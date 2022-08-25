"""Controller for creating or editing a single share group

Classes
----------
ShareGroupController
    Controller for creating or editing a single share group
"""
import gettext

import models.sharegroup
from controllers.editcontroller import EditController

_ = gettext.gettext


class ShareGroupController(EditController):
    """Controller for creating or editing a single share group

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

    group_id : int
        The ID of the share group to edit. 0 for new share groups.
    item : models.sharegroup.ShareGroup
        The share group being edited or created
    """

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
        """Sets up all data required to display the fields

        For each fields, sets up the "default" value, based on existing database data

        Parameters
        ----------
        parent_controller : QtWidgets.QMainWindow
            The main window displaying this widget
        group_id : int
            The ID of the share group to edit. 0 for new share groups.
        """
        super().__init__(parent_controller)
        self.group_id = int(group_id)
        if self.group_id:
            self.item = self.database.share_group_get_by_id(self.group_id)
        else:
            self.item = models.sharegroup.ShareGroup()
        self.fields["name"]["default"] = self.item.name
