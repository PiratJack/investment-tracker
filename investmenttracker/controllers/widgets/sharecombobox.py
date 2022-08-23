"""QComboBox for list of shares, grouped by their groups

Classes
----------
ShareComboBox
    QComboBox for list of shares, grouped by their groups
"""
import gettext

from PyQt5 import QtWidgets

import models.share

_ = gettext.gettext


class ShareComboBox(QtWidgets.QComboBox):
    """QComboBox for list of shares, grouped by their groups

    Attributes
    ----------
    database : models.database.Database
        A reference to the application database
    """

    def __init__(self, database, parent=None, include_choice_all=0):
        """Defines the QComboBox contents

        Parameters
        ----------
        database : models.database.Database
            A reference to the application database
        parent : QtWidgets.QWidget (or child classes)
            The parent of this combobox
        include_choice_all : bool
            Whether value "All" should be included

        Returns
        -------
        None"""
        super().__init__(parent)
        self.database = database

        values = []
        if include_choice_all:
            values.append((_("All"), -1, True))

        # Shared in groups
        groups = self.database.share_groups_get_all()
        for group in groups:
            values.append((group.name, -1, False))
            for share in group.shares:
                values.append((share.short_name, share.id, True))

        # Shares without group
        shares_without_group = (
            self.database.shares_query().filter(models.share.Share.group is None).all()
        )
        values.append((_("Shares without group"), -1, False))
        for share in shares_without_group:
            values.append((share.short_name, share.id, True))

        # Actually add to the dropdown
        for index, value in enumerate(values):
            self.addItem(value[0], value[1])
            if not value[2]:
                self.model().item(index).setEnabled(False)

        # Make placeholder unselectable
        if not include_choice_all:
            self.model().item(0).setEnabled(False)

        self.resize(self.sizeHint())
