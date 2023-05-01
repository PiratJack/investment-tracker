"""Displays accounts, held shares & various metrics

Classes
----------
AccountsTree
    The tree displaying the accounts

AccountsController
    Handles user interactions and links all displayed widgets
"""
import gettext

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

from models.base import NoPriceException, format_number
import controllers.account
from controllers.widgets import basetreecontroller

_ = gettext.gettext


class AccountsTree(basetreecontroller.BaseTreeController):
    """Displays accounts & held shares

    Attributes
    ----------
    columns : list of dicts
        Columns to display. Each column should have a name and size key
    parent_controller : AccountsController
        The controller in which this class is displayed
    database : models.database.Database
        A reference to the application database

    account_details : controllers.account.AccountController
        The controller for creating/editing a single account

    Methods
    -------
    fill_accounts (accounts)
        Fills the tree with accounts data (& their children)

    on_double_click (tree_item)
        User double-clicks: opens the account create/edit dialog
    """

    columns = [
        {
            "name": _("Name"),
            "size": 0.4,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": _("ID"),
            "size": 0,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Code"),
            "size": 0.2,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": _("Quantity"),
            "size": 0.1,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Value"),
            "size": 0.1,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("As of date"),
            "size": 0.1,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Total invested"),
            "size": 0.1,
            "alignment": Qt.AlignRight,
        },
    ]
    account_details = None

    def fill_accounts(self, accounts):
        """Fills the tree based on provided accounts & held shares

        The items are directly added to the tree

        Parameters
        ----------
        accounts : list of models.account.Account
            The list of accounts to display
        """
        tree_items = []

        # Fill in the data
        for account in accounts:
            try:
                value = format_number(
                    account.total_value, account.base_currency.main_code
                )
            except (AttributeError, NoPriceException):
                value = _("Unknown or too old")
            account_widget = QtWidgets.QTreeWidgetItem(
                [
                    account.name,
                    str(account.id),
                    account.code,
                    "",
                    value,
                    "",
                    format_number(account.total_invested),
                ]
            )
            for column, field in enumerate(self.columns):
                account_widget.setTextAlignment(column, field["alignment"])

            if not account.enabled:
                font = account_widget.font(0)
                font.setItalic(True)
                account_widget.setFont(0, font)

            if account.hidden:
                font = account_widget.font(0)
                font.setItalic(True)
                account_widget.setFont(0, font)
                account_widget.setForeground(0, QtGui.QBrush(QtGui.QColor("#A0A0A0")))

            # Add held shares
            children = []
            for share_id in account.shares:
                share = self.database.share_get_by_id(share_id)
                # Try to display the last price
                try:
                    last_price = share.last_price
                    child = [
                        share.name,
                        "",
                        share.main_code,
                        format_number(account.shares[share.id]),
                        format_number(
                            account.shares[share.id] * last_price.price,
                            last_price.currency.main_code,
                        ),
                        QtCore.QDate(last_price.date).toString(
                            Qt.SystemLocaleShortDate
                        ),
                        "",
                    ]
                except NoPriceException:
                    child = [
                        share.name,
                        "",
                        share.main_code,
                        format_number(account.shares[share.id]),
                        _("Unknown or too old"),
                        "",
                        "",
                    ]

                children.append(child)

            # Add cash
            child = [
                _("Cash ({currency})").format(currency=account.base_currency.main_code),
                "",
                share.main_code,
                format_number(account.balance),
                format_number(
                    account.balance,
                    account.base_currency.main_code,
                ),
                "",
                "",
            ]
            children.append(child)

            for child in children:
                child_widget = QtWidgets.QTreeWidgetItem(child)
                for column, field in enumerate(self.columns):
                    child_widget.setTextAlignment(column, field["alignment"])
                account_widget.addChild(child_widget)

            tree_items.append(account_widget)

        # Add new account
        new_account_widget = QtWidgets.QTreeWidgetItem(
            [
                _("Add new account"),
                "0",
                "",
                "",
                "",
                "",
                "",
            ]
        )
        font = new_account_widget.font(0)
        font.setItalic(True)
        new_account_widget.setFont(0, font)
        new_account_widget.setForeground(0, QtGui.QBrush(QtGui.QColor("#A0A0A0")))
        new_account_widget.setIcon(0, QtGui.QIcon("assets/images/add.png"))
        tree_items.append(new_account_widget)

        # Put everything in the tree
        self.insertTopLevelItems(0, tree_items)

    def on_double_click(self, tree_item):
        """User double-clicks: opens the account create/edit dialog

        Parameters
        ----------
        tree_item : QtWidgets.QTreeWidgetItem
            The tree item being modified
        """
        if tree_item.parent():
            return
        self.account_details = controllers.account.AccountController(
            self.parent_controller, tree_item.text(1)
        )
        self.account_details.show_window()


class AccountsController:
    """Controller for display & interactions on accounts list

    Attributes
    ----------
    name : str
        Name of the controller - used in display
    display_hidden_accounts : bool
        Whether to display hidden accounts
    display_disabled_accounts : bool
        Whether to display disabled accounts

    accounts : list of models.account.Account
        List of accounts to display in the tree

    parent_window : QtWidgets.QMainWindow
        The parent window
    database : models.database.Database
        A reference to the application database

    display_widget : QtWidgets.QWidget
        The main display for this controller
    tree : controllers.widgets.AccountsSharesTree
        A tree displaying the accounts & shares
    checkbox_hidden_accounts : QtWidgets.QCheckBox
        The checkbox to display hidden accounts
    checkbox_disabled_accounts : QtWidgets.QCheckBox
        The checkbox to display disabled accounts

    Methods
    -------
    __init__ (parent_window)
        Sets up all data required to display the screen

    get_toolbar_button
        Returns a QtWidgets.QAction for display in the main window toolbar
    get_display_widget
        Returns the main QtWidgets.QWidget for this controller
    reload_data
        Reloads the list of accounts/shares (& triggers tree refresh)

    on_click_checkbox_hidden
        User clicks on 'display hidden accounts' checkbox => reload tree
    on_click_checkbox_disabled
        User clicks on 'display disabled accounts' checkbox => reload tree
    """

    name = "Accounts"
    display_hidden_accounts = False
    display_disabled_accounts = False

    def __init__(self, parent_window):
        """Sets up all data required to display the screen

        Parameters
        ----------
        parent_window : QtWidgets.QMainWindow
            The window displaying this controller
        """
        self.parent_window = parent_window
        self.database = parent_window.database
        self.accounts = self.database.accounts_get()

        self.display_widget = QtWidgets.QWidget()
        self.tree = AccountsTree(self)
        self.checkbox_hidden_accounts = QtWidgets.QCheckBox(
            _("Display hidden accounts?")
        )
        self.checkbox_disabled_accounts = QtWidgets.QCheckBox(
            _("Display disabled accounts?")
        )

    def get_toolbar_button(self):
        """Returns a QtWidgets.QAction for display in the main window toolbar"""
        button = QtWidgets.QAction(
            QtGui.QIcon("assets/images/accounts.png"), _("Accounts"), self.parent_window
        )
        button.setStatusTip(_("Display your accounts"))
        button.triggered.connect(lambda: self.parent_window.display_tab(self.name))
        return button

    def get_display_widget(self):
        """Returns the main QtWidgets.QWidget for this controller"""
        self.display_widget.layout = QtWidgets.QVBoxLayout()
        self.display_widget.setLayout(self.display_widget.layout)

        self.tree.fill_accounts(self.accounts)
        self.display_widget.layout.addWidget(self.tree)

        self.checkbox_hidden_accounts.stateChanged.connect(
            self.on_click_checkbox_hidden
        )
        self.display_widget.layout.addWidget(self.checkbox_hidden_accounts)

        self.checkbox_disabled_accounts.stateChanged.connect(
            self.on_click_checkbox_disabled
        )
        self.display_widget.layout.addWidget(self.checkbox_disabled_accounts)

        self.parent_window.setCentralWidget(self.display_widget)

        return self.display_widget

    def reload_data(self):
        """Reloads the list of accounts/shares (& triggers tree refresh)"""
        self.accounts = self.database.accounts_get(
            with_hidden=self.display_hidden_accounts,
            with_disabled=self.display_disabled_accounts,
        )
        self.tree.clear()
        self.tree.fill_accounts(self.accounts)

    def on_click_checkbox_hidden(self):
        """User clicks on 'display hidden accounts' checkbox => reload tree"""
        self.display_hidden_accounts = self.checkbox_hidden_accounts.isChecked()
        self.reload_data()
        self.checkbox_hidden_accounts.clearFocus()

    def on_click_checkbox_disabled(self):
        """User clicks on 'display disabled accounts' checkbox => reload tree"""
        self.display_disabled_accounts = self.checkbox_disabled_accounts.isChecked()
        self.reload_data()
        self.checkbox_disabled_accounts.clearFocus()
