"""Controller for creating or editing a single share

Classes
----------
AccountController
    Controller for creating or editing a single share
"""

import logging
import gettext

import models.share
import models.sharecode
from controllers.widgets.editcontroller import EditController
from models.base import ValidationException

_ = gettext.gettext
logger = logging.getLogger(__name__)


class ShareController(EditController):
    """Controller for creating or editing a single share

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

    share_id : int
        The ID of the share to edit. 0 for new shares.
    item : models.share.Share
        The share being edited or created

    Methods
    ----------
    __init__ (parent_controller, share_id=0)
        Sets up all data required to display the screen
    after_item_save
        Saves the share codes & ensures we have a code for the selected sync origin
    """

    name = _("Share")

    fields = {
        "name": {
            "label": _("Name"),
            "type": "text",
            "mandatory": True,
        },
        "main_code": {
            "label": _("Main code"),
            "type": "text",
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
        "sync_origin": {
            "label": _("Get prices online from?"),
            "type": "list",
        },
    }

    error_widgets = []

    def __init__(self, parent_controller, share_id=0):
        """Sets up all data required to display the screen

        For each fields, sets up the "default" value, based on existing database data
        If needed, set up the "possible_values" for dropdowns.


        Parameters
        ----------
        parent_controller : QtWidgets.QMainWindow
            The main window displaying this widget
        share_id : int
            The ID of the share to edit. 0 for new shares.
        """
        logger.info(f"ShareController.__init__ {share_id}")
        super().__init__(parent_controller)
        self.share_id = int(share_id)
        self.fields["group_id"]["possible_values"] = [
            (g.name, g.id) for g in self.database.share_groups_get_all()
        ]
        self.fields["base_currency_id"]["excluded"] = self.share_id
        if self.share_id:
            self.item = self.database.share_get_by_id(self.share_id)
        else:
            self.item = models.share.Share()
        self.fields["name"]["default"] = self.item.name
        self.fields["main_code"]["default"] = self.item.main_code
        self.fields["sync_origin"]["possible_values"] = [
            (g.value["name"], g.name) for g in models.share.ShareDataOrigin
        ]
        if self.item.sync_origin:
            self.fields["sync_origin"]["default"] = self.item.sync_origin.name
        else:
            if "default" in self.fields["sync_origin"]:
                del self.fields["sync_origin"]["default"]
        self.fields["base_currency_id"]["default"] = (
            self.item.base_currency.id if self.item.base_currency else 0
        )
        self.fields["hidden"]["default"] = self.item.hidden
        self.fields["group_id"]["default"] = (
            self.item.group.id if self.item.group else 0
        )

        for origin in models.sharecode.ShareDataOrigin:
            self.fields["code_" + origin.name] = {
                "label": _("Code for {origin}").format(origin=origin.value["name"]),
                "type": "text",
                "default": "",
            }
        if self.item.codes:
            for code in self.item.codes:
                self.fields["code_" + code.origin.name]["default"] = code.value

    def after_item_save(self):
        """Saves the share codes & ensures we have a code for the selected sync origin

        As share codes are a separate model, EditController won't handle it

        Raises
        ----------
        ValidationException
            If the sync origin is defined, but there is no corresponding code
            (Therefore any syncing will fail)
        """
        logger.debug("ShareController.after_item_save")
        # This refreshes the data from DB, so that self.item.id is set
        self.database.session.flush()

        # Get each code value
        for origin in models.sharecode.ShareDataOrigin:
            user_input = getattr(self.item, "code_" + origin.name)
            existing_code = [code for code in self.item.codes if code.origin == origin]
            if user_input:
                if existing_code:
                    existing_code[0].value = user_input
                else:
                    new_code = models.sharecode.ShareCode(
                        share_id=self.item.id, origin=origin.name, value=user_input
                    )
                    self.item.codes.append(new_code)
                    self.database.session.add(new_code)
                    self.database.session.flush()
                    self.database.session.refresh(new_code)
            else:
                if existing_code:
                    self.item.codes.remove(existing_code[0])
                    self.database.delete(existing_code[0])

        # Ensure we have a code for the origin of syncing
        if self.item.sync_origin:
            sync_origin = [
                v
                for v in models.share.ShareDataOrigin
                if self.item.sync_origin in (v, v.name)
            ]
            if not sync_origin:
                self.item.sync_origin = None
            else:
                self.item.sync_origin = sync_origin[0]

                existing_code = [
                    code
                    for code in self.item.codes
                    if code.origin == self.item.sync_origin
                ]
                if not existing_code:
                    raise ValidationException(
                        _("Missing code for sync"),
                        self.item,
                        "code_" + self.item.sync_origin.name,
                        None,
                    )
