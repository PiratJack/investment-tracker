import gettext

from PyQt5.QtWidgets import (
    QComboBox,
)

import models.share


class ShareComboBox(QComboBox):
    def __init__(self, database, include_choice_all=0):
        super().__init__()
        self.database = database

        values = []
        if include_choice_all:
            values.append((_("All"), -1, True))
        else:
            values.append((_("Select a value"), -1, True))

        # Shared in groups
        groups = self.database.share_groups_get_all()
        for group in groups:
            values.append((group.name, group.id, False))
            for share in group.shares:
                values.append((share.short_name(), share.id, True))

        # Shares without group
        shares_without_group = (
            self.database.shares_query().filter(models.share.Share.group == None).all()
        )
        values.append((_("Shares without group"), -1, False))
        for share in shares_without_group:
            values.append((share.short_name(), share.id, True))

        # Actually add to the dropdown
        for i, value in enumerate(values):
            self.addItem(value[0], value[1])
            if not value[2]:
                self.model().item(i).setEnabled(False)

        # Make placeholder unselectable
        if not include_choice_all:
            self.model().item(0).setEnabled(False)

        self.resize(self.sizeHint())
