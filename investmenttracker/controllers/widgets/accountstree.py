"""Displays accounts the user can select

Classes
----------
AccountsTree
    Displays accounts so the user can select
"""

import gettext

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt

from controllers.widgets import basetreecontroller

_ = gettext.gettext


class AccountsTree(basetreecontroller.BaseTreeController):
    """Displays accounts so the user can select

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
    add_account (account)
        Adds a single account to the tree
    on_select_item
        Handler for user selection: triggers controller's handler
    get_selected_items
        Returns a list of selected account IDs
    """

    columns = [
        {
            "name": _("Name"),
            "size": 0.4,
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
    selected_accounts = []

    def __init__(self, parent_controller):
        """Stores parameters for future use & loads data to display

        Parameters
        ----------
        parent_controller : DashboardController
            The controller in which this table is displayed
        """
        super().__init__(parent_controller)
        self.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.itemSelectionChanged.connect(self.on_select_item)

    def fill_tree(self, accounts):
        """Fills the tree based on provided accounts

        The items are directly added to the tree

        Parameters
        ----------
        accounts : list of models.account.Account
            The list of accounts to display
        """
        for account in accounts:
            if account.hidden and not self.parent_controller.display_hidden_accounts:
                continue
            if (
                not account.enabled
                and not self.parent_controller.display_disabled_accounts
            ):
                continue
            account_item = self.add_account(account)
            self.addTopLevelItem(account_item)

    def add_account(self, account):
        """Formats a single account for display in the tree

        Parameters
        ----------
        account : models.account.Account
            The account to format

        Returns
        -------
        QtWidgets.QTreeWidgetItem
            Account item for inclusion in the tree"""
        account_item = QtWidgets.QTreeWidgetItem(
            [account.name, "account", str(account.id)]
        )
        account_item.setFlags(account_item.flags() | Qt.ItemIsAutoTristate)
        for column, field in enumerate(self.columns):
            account_item.setTextAlignment(column, field["alignment"] | Qt.AlignVCenter)

        if not account.enabled or account.hidden:
            font = account_item.font(0)
            font.setItalic(True)
            account_item.setFont(0, font)

        if account.hidden:
            account_item.setForeground(0, QtGui.QBrush(QtGui.QColor("#A0A0A0")))

        return account_item

    def on_select_item(self):
        """Handler for user selection: triggers controller's handler"""
        self.parent_controller.on_change_account_selection(self.get_selected_items())

    def get_selected_items(self):
        """Returns a list of selected account IDs

        Returns
        -------
        list of int
            A list of account IDs
        """
        role = Qt.DisplayRole
        self.selected_accounts = [
            int(i.data(2, role)) for i in self.selectedItems() if not i.parent()
        ]

        return self.selected_accounts
