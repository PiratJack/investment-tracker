"""Displays shares the user can select

Classes
----------
SharesTree
    Displays shares the user can select
"""

import logging
import gettext

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from controllers.widgets import basetreecontroller

_ = gettext.gettext
logger = logging.getLogger(__name__)


class SharesTree(basetreecontroller.BaseTreeController):
    """Displays shares the user can select

    Attributes
    ----------
    columns : list of dicts
        Columns to display. Each column should have a name and size key
    parent_controller : AccountsController
        The controller in which this class is displayed
    database : models.database.Database
        A reference to the application database

    selected_accounts : list of int
        The list of selected account IDs

    Methods
    -------
    __init__ (parent_controller)
        Stores parameters for future use & loads data to display

    fill_tree (accounts)
        Fills the tree with accounts data
    add_group (name, group_id)
        Adds a single share group to the tree
    add_share (data, parent_widget=None)
        Adds a single share to the tree
    on_select_item
        Handler for user selection: triggers controller's handler
    get_selected_items
        Returns a list of selected share IDs
    """

    columns = [
        {
            "name": _("Name"),
            "size": 1,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": _("Type"),
            "size": 0,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("ID"),
            "size": 0,
            "alignment": Qt.AlignRight,
        },
    ]
    selected_shares = []

    def __init__(self, parent_controller):
        """Stores parameters for future use & loads data to display

        Parameters
        ----------
        parent_controller : QtWidgets.QMainWindow
            The main window displaying this widget
        """
        logger.debug("SharesTree.__init__")
        super().__init__(parent_controller)
        self.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.itemSelectionChanged.connect(self.on_select_item)

    def fill_tree(self, groups, shares_without_group):
        """Fills the tree based on provided share groups and shares without a group

        The items are directly added to the tree

        Parameters
        ----------
        groups : list of models.sharegroup.ShareGroup
            The list of share groups to display
        shares_without_group : list of models.share.Share
            The list of shares without a group to display
        """
        logger.info(
            f"SharesTree.fill_tree {groups} - Ungrouped: {shares_without_group}"
        )
        # Add shares within a group
        for group in groups:
            group_widget = self.add_group(group.name, group.id)
            for share in group.shares:
                if share.hidden and not self.parent_controller.display_hidden_shares:
                    continue
                group_widget.addChild(
                    self.add_share([share.name, "Share", share.id], group_widget)
                )

        # Add shares without group
        group_widget = self.add_group(_("Shares without group"), -1)
        for share in shares_without_group:
            group_widget.addChild(
                self.add_share([share.name, "Share", share.id], group_widget)
            )

    def add_group(self, name, group_id):
        """Adds a single share group (& its children) to the tree

        Parameters
        ----------
        name : str
            The name of the share group
        group_id : int
            The ID of the group to add

        Returns
        -------
        QtWidgets.QTreeWidgetItem
            The share group to add in the tree
        """
        logger.debug(f"SharesTree.add_group {name} - {group_id}")
        group_widget = QtWidgets.QTreeWidgetItem([name, "Group", str(group_id)])
        self.addTopLevelItem(group_widget)

        for column, field in enumerate(self.columns):
            group_widget.setTextAlignment(column, field["alignment"] | Qt.AlignVCenter)

        # Shares not grouped
        if group_id <= 0:
            font = group_widget.font(0)
            font.setItalic(True)
            group_widget.setFont(0, font)

        return group_widget

    def add_share(self, data, parent_item=None):
        """Formats a single share for display in the tree

        Parameters
        ----------
        share : models.share.Share
            The share to format
        parent_item : QtWidgets.QTreeWidgetItem
            If present, the share item returned will use it as parent

        Returns
        -------
        QtWidgets.QTreeWidgetItem
            Share item for inclusion in the tree"""
        logger.debug(f"SharesTree.add_share {data}")
        share_widget = QtWidgets.QTreeWidgetItem([str(field) for field in data])
        share_widget.setFlags(share_widget.flags() & ~Qt.ItemIsUserCheckable)
        if parent_item:
            parent_item.addChild(share_widget)
        else:
            self.addTopLevelItem(share_widget)

        for column, field in enumerate(self.columns):
            share_widget.setTextAlignment(column, field["alignment"] | Qt.AlignVCenter)

        return share_widget

    def get_selected_items(self):
        """Returns a list of selected share IDs

        Returns
        -------
        list of int
            A list of share IDs
        """
        logger.debug("SharesTree.get_selected_items")
        role = Qt.DisplayRole

        self.selected_shares = [
            int(i.data(2, role)) for i in self.selectedItems() if i.parent()
        ]

        return self.selected_shares

    def on_select_item(self):
        """Handler for user selection: triggers controller's handler"""
        logger.debug("SharesTree.on_select_item")
        self.parent_controller.on_change_share_selection(self.get_selected_items())
