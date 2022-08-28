"""Displays transactions, with filtering by account and/or share held

Classes
----------
AccountsSharesTree
    Widget to display accounts and their held shares.
    Updates the list of transactions upon selection.

TransactionsTableModel
    Model for transactions display

TransactionsTableView
    View for transactions display

TransactionsController
    Handles user interactions and links all displayed widgets
"""
import gettext

from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import Qt

import controllers.transaction
from models.base import format_number
from controllers.widgets import basetreecontroller, autoresize

_ = gettext.gettext
# TODO (?): Link transactions ==> what would be the impacts?


class AccountsSharesTree(basetreecontroller.BaseTreeController):
    """Display of accounts & shares for user selection

    Attributes
    ----------
    columns : list of dicts
        Columns to display. Each column should have a name and size key
    parent_controller : TransactionsController
        The controller in which this class is displayed
    selected_accounts : list of int
        The account IDs for filtering the list of transactions
    account_shares : dict of dict of int
        The shares for filtering, in the form {account_id:[share_id]}

    Methods
    -------
    __init__ (parent_controller)
        Initial setup (mostly through inherited __init__)
    fill_tree (accounts)
        Fills the tree with accounts data (& their children)
    add_account (account)
        Adds a single account to the tree
    add_share (share, parent_item=None)
        Adds a single share to the tree

    on_select_item
        Handler for user selection: triggers controller's handler
    store_item_selection
        Stores selected accounts/shares (for re-selection after refresh)
    get_selected_items
        Returns a list of selected accounts and a dict of selected shares
    restore_item_selection
        Restores previous selection of accounts/shares (used after tree refresh)
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
    selected_shares = {}

    def __init__(self, parent_controller):
        """Initial setup (mostly through inherited __init__)

        Parameters
        ----------
        parent_controller : QtWidgets.QMainWindow
            The main window displaying this widget
        """
        super().__init__(parent_controller)
        self.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.itemSelectionChanged.connect(self.on_select_item)

    def fill_tree(self, accounts):
        """Fills the tree based on provided accounts & held shares

        The items are directly added to the tree

        Parameters
        ----------
        accounts : list of models.account.Account
            The list of accounts to display
        """
        for account in sorted(accounts, key=lambda a: a.name):
            if account.hidden and not self.parent_controller.display_hidden_accounts:
                continue
            if (
                not account.enabled
                and not self.parent_controller.display_disabled_accounts
            ):
                continue
            account_item = self.add_account(account)
            self.addTopLevelItem(account_item)

            # Add held shares
            shares = []
            for share_id in account.shares:
                shares.append(self.database.share_get_by_id(share_id))
            for share in sorted(shares, key=lambda a: a.name):
                account_item.addChild(self.add_share(share, account_item))

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
            account_item.setTextAlignment(column, field["alignment"])

        if not account.enabled or account.hidden:
            font = account_item.font(0)
            font.setItalic(True)
            account_item.setFont(0, font)

        if account.hidden:
            account_item.setForeground(0, QtGui.QBrush(QtGui.QColor("#A0A0A0")))

        return account_item

    def add_share(self, share, parent_item=None):
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
        share_item = QtWidgets.QTreeWidgetItem(
            [
                share.name,
                "share",
                str(share.id),
            ]
        )
        if parent_item:
            parent_item.addChild(share_item)
        else:
            self.addTopLevelItem(share_item)

        for column, field in enumerate(self.columns):
            share_item.setTextAlignment(column, field["alignment"])

        return share_item

    def on_select_item(self):
        """Handler for user selection: triggers controller's handler"""
        self.parent_controller.on_change_selection(*self.get_selected_items())

    def store_item_selection(self):
        """Stores selected accounts/shares (for re-selection after refresh)"""
        self.selected_accounts, self.selected_shares = self.get_selected_items()

    def get_selected_items(self):
        """Returns a list of selected accounts and a dict of selected shares

        Returns
        -------
        selected_accounts : list of int
            A list of account IDs
        selected_shares : dict of list of int
            A dict of the format {account_id:[share_id]}
        """
        role = Qt.DisplayRole
        self.selected_accounts = [
            int(i.data(2, role)) for i in self.selectedItems() if not i.parent()
        ]

        share_accounts = set(
            int(i.parent().data(2, role))
            for i in self.selectedItems()
            if i.parent()
            and int(i.parent().data(2, role)) not in self.selected_accounts
        )
        self.selected_shares = {
            account_id: [
                int(i.data(2, role))
                for i in self.selectedItems()
                if i.parent() and i.parent().data(2, role) == str(account_id)
            ]
            for account_id in share_accounts
        }

        return (self.selected_accounts, self.selected_shares)

    def restore_item_selection(self):
        """Restores previous selection of accounts/shares (used after tree refresh)"""
        role = Qt.DisplayRole
        # Restore selected accounts
        for account_id in self.selected_accounts:
            items = self.findItems(str(account_id), Qt.MatchExactly, 2)
            for item in items:
                item.setSelected(True)

        # Restore selected shares
        for account_id, shares_ids in self.selected_shares.items():
            share_items = [
                i
                for share_id in shares_ids
                for i in self.findItems(
                    str(share_id), Qt.MatchExactly | Qt.MatchRecursive, 2
                )
                if i.data(1, role) == "share"
                and i.parent()
                and i.parent().data(2, role) == str(account_id)
            ]

            for share_item in share_items:
                share_item.setSelected(True)


class TransactionsTableModel(QtCore.QAbstractTableModel):
    """Model for display of transactions, based on user selection

    Attributes
    ----------
    columns : list of dicts
        Columns to display. Each column needs a name key (alignment & size are optional)
    database : models.database.Database
        A reference to the application database
    accounts : list of models.account.Account
        The accounts for filtering
    transactions : list of models.transaction.Transaction
        The list of transactions to display

    Methods
    -------
    __init__ (database, columns)
        Stores the provided parameters for future use

    columnCount (index)
        Returns the number of columns
    rowCount (index)
        Returns the number of rows
    data (index)
        Returns which data to display (or how to display it) for the corresponding cell
    headerData (index)
        Returns the table headers

    set_filters (index)
        Applies the filters on the list of transactions
    get_transaction (index)
        Returns a models.transaction.Transaction object for the corresponding index
    """

    def __init__(self, database, columns):
        """Stores the provided parameters for future use

        Parameters
        ----------
        database : models.database.Database
            A reference to the application database
        columns : list of dicts
            Columns to display.
            Each column needs a name key (alignment & size are optional)
        """
        super().__init__()
        self.columns = columns
        self.database = database
        self.accounts = []
        self.transactions = []

    def columnCount(self, index):
        """Returns the number of columns

        Parameters
        ----------
        index : QtCore.QModelIndex
            A reference to the cell to display (not used in this method)
        """
        return len(self.columns)

    def rowCount(self, index):
        """Returns the number of rows

        Parameters
        ----------
        index : QtCore.QModelIndex
            A reference to the cell to display (not used in this method)
        """
        return len(self.transactions) + 1

    def data(self, index, role):
        """Returns the data or formatting to display in table contents

        Parameters
        ----------
        index : QtCore.QModelIndex
            A reference to the cell to display
        role : Qt.DisplayRole
            The required role (display, decoration, ...)

        Returns
        -------
        QtCore.QVariant
            If role = Qt.DisplayRole: the data to display or "Add a transaction"
            If role = Qt.DecorationRole: the images for edit / delete actions
            If role = Qt.TextAlignmentRole: the proper alignment
        """
        if not index.isValid():
            return False

        col = index.column()
        if role == Qt.DisplayRole:
            # New item row
            if index.row() == len(self.transactions):
                if index.column() == 0:
                    return _("Add a transaction")
                return QtCore.QVariant()

            transaction = self.transactions[index.row()]
            currency_code = transaction.account.base_currency.main_code
            balance = transaction.account.balance_after_transaction(transaction)
            return [
                transaction.account.name,
                transaction.id,
                QtCore.QDate(transaction.date),
                transaction.type.value["name"],
                transaction.label,
                format_number(transaction.asset_total),
                transaction.share.short_name if transaction.share else "-",
                format_number(balance[1])
                if transaction.type.value["has_asset"]
                else "-",
                format_number(transaction.unit_price, currency_code)
                if transaction.unit_price != 1
                else "-",
                format_number(transaction.cash_total, currency_code),
                format_number(balance[0], currency_code),
                QtCore.QVariant(),
                QtCore.QVariant(),
            ][col]

        if role == Qt.DecorationRole and index.row() != len(self.transactions):
            if col == len(self.columns) - 2:
                return QtCore.QVariant(QtGui.QIcon("assets/images/add.png"))
            if col == len(self.columns) - 1:
                return QtCore.QVariant(QtGui.QIcon("assets/images/delete.png"))

        if role == Qt.TextAlignmentRole:
            return self.columns[index.column()]["alignment"]

        return QtCore.QVariant()

    def headerData(self, column, orientation, role):
        """Returns the data or formatting to display in headers

        Parameters
        ----------
        column : int
            The column number
        orientation : Qt.Orientation
            Whether headers are horizontal or vertical
        role : Qt.DisplayRole
            The required role (display, decoration, ...)

        Returns
        -------
        QtCore.QVariant
            If role = Qt.DisplayRole and orientation == Qt.Horizontal: the header name
            Else: QtCore.QVariant
        """
        if role != Qt.DisplayRole:
            return QtCore.QVariant()

        if orientation == Qt.Horizontal:
            return QtCore.QVariant(_(self.columns[column]["name"]))
        return QtCore.QVariant()

    def set_filters(self, selected_accounts=None, selected_shares=None):
        """Updates self.transactions based on user selection of accounts/shares

        Parameters
        ----------
        selected_accounts : list of int
            The account IDs for filtering the list of transactions
        account_shares : dict of dict of int
            The shares for filtering, in the form {account_id:[share_id]}
        """
        self.transactions = self.database.transactions_get_by_account_and_shares(
            selected_accounts, selected_shares
        )
        self.transactions = sorted(self.transactions, key=lambda t: (t.date, t.id))

    def get_transaction(self, index):
        """Returns the transaction displayed in a given position (index/row)

        Parameters
        ----------
        index : QtCore.QModelIndex
            A reference to the cell to display

        Returns
        -------
        models.transaction.Transaction
            The transaction to display for the provided index/row
        """
        return self.transactions[index.row()]


class TransactionsTableView(QtWidgets.QTableView, autoresize.AutoResize):
    """Table for display of transactions, based on user selection

    Attributes
    ----------
    columns : list of dicts
        Columns to display. Each column should have a name and size key
    parent_controller : TransactionsController
        The controller in which this class is displayed
    database : models.database.Database
        A reference to the application database
    model : TransactionsTableModel
        The model for interaction with the database

    transaction_details : controllers.transaction.TransactionController
        The controller for creating/editing a single transaction

    Methods
    -------
    __init__ (parent_controller)
        Stores parameters & connects with the model & user interactions
    set_filters (selected_accounts=None, selected_shares=None)
        Applies the corresponding filters on the list of transactions
    on_table_clicked (index)
        User click handler - either create a new transaction, copy or delete it
    """

    columns = [
        {
            "name": _("Account"),
            "size": 0.1,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": _("ID"),
            "size": 0,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Date"),
            "size": 0.1,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": _("Type"),
            "size": 0.15,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": _("Label"),
            "size": 0.17,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": _("Asset delta"),
            "size": 0.05,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Share"),
            "size": 0.1,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Asset balance"),
            "size": 0.05,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Rate"),
            "size": 0.08,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Currency delta"),
            "size": 0.1,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Cash balance"),
            "size": 0.1,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Copy"),
            "size": 80,
            "alignment": Qt.AlignCenter,
        },
        {
            "name": _("Delete"),
            "size": 80,
            "alignment": Qt.AlignCenter,
        },
    ]
    transaction_details = None

    def __init__(self, parent_controller):
        """Stores parameters & connects with the model & user interactions

        Parameters
        ----------
        parent_controller : TransactionsController
            The controller in which this table is displayed
        """
        super().__init__()
        self.parent_controller = parent_controller
        self.database = parent_controller.database

        self.model = TransactionsTableModel(self.database, self.columns)
        self.setModel(self.model)

        self.clicked.connect(self.on_table_clicked)
        self.doubleClicked.connect(self.on_table_double_clicked)

    def set_filters(self, selected_accounts=None, selected_shares=None):
        """Applies the filters on the list of transactions to display

        Parameters
        ----------
        selected_accounts : list of int
            The account IDs for filtering the list of transactions
        account_shares : dict of dict of int
            The shares for filtering, in the form {account_id:[share_id]}
        """
        self.model.set_filters(selected_accounts, selected_shares)
        self.model.layoutChanged.emit()
        self.viewport().update()

    def on_table_clicked(self, index):
        """User click handler - either create a new transaction, copy or delete it

        Will trigger a reload of the table once the action is complete

        Parameters
        ----------
        index : QtCore.QModelIndex
            A reference to the cell clicked
        """
        self.parent_controller.store_tree_item_selection()
        # New transaction
        if index.row() == len(self.model.transactions):
            self.transaction_details = controllers.transaction.TransactionController(
                self.parent_controller
            )
            self.transaction_details.show_window()

        else:
            # Clicked on random column
            if index.column() < len(self.columns) - 2:
                return

            transaction = self.model.get_transaction(index)
            # Duplicate button
            if index.column() == len(self.columns) - 2:
                transaction = transaction.copy()
                self.database.session.add(transaction)
                self.database.session.commit()

                self.transaction_details = (
                    controllers.transaction.TransactionController(
                        self.parent_controller, transaction.id
                    )
                )
                self.transaction_details.show_window()

            # Delete button
            elif index.column() == len(self.columns) - 1:
                messagebox = QtWidgets.QMessageBox.critical(
                    self.parent(),
                    _("Please confirm"),
                    _("Are you sure you want to delete this transaction?"),
                    buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    defaultButton=QtWidgets.QMessageBox.No,
                )

                if messagebox == QtWidgets.QMessageBox.Yes:
                    if transaction.id:
                        self.database.delete(transaction)
                    self.model.beginRemoveRows(index, index.row(), index.row())
                    self.set_filters()  # Reload the data
                    self.model.endRemoveRows()

        self.parent_controller.restore_tree_item_selection()

    def on_table_double_clicked(self, index):
        """User double-click handler - edit existing transaction

        Will trigger a reload of the table once the action is complete

        Parameters
        ----------
        index : QtCore.QModelIndex
            A reference to the cell clicked
        """
        self.parent_controller.store_tree_item_selection()
        # New transaction
        if index.row() == len(self.model.transactions):
            self.on_table_clicked(index)
        else:
            transaction = self.model.get_transaction(index)
            self.transaction_details = controllers.transaction.TransactionController(
                self.parent_controller, transaction.id
            )
            self.transaction_details.show_window()

        self.parent_controller.restore_tree_item_selection()


class TransactionsController:
    """Controller for display & interactions on transactions list

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
    left_column : QtWidgets.QWidget
        The left column of the screen
    tree : controllers.widgets.AccountsSharesTree
        A tree displaying the accounts & shares
    checkbox_hidden_accounts : bool
        The checkbox to display hidden accounts
    checkbox_disabled_accounts : bool
        The checkbox to display disabled accounts

    right_column : QtWidgets.QWidget
        The right column of the screen
    table : TransactionsTableView
        The table displaying all transactions matching the filters

    Methods
    -------
    __init__ (parent_window)
        Stores provided parameters & sets up UI items
    get_toolbar_button
        Returns a QtWidgets.QAction for display in the main window toolbar
    get_display_widget
        Returns the main QtWidgets.QWidget for this controller
    reload_data ()
        Reloads the list of accounts/shares

    on_click_hidden_accounts
        User clicks on 'display hidden accounts' checkbox => reload tree
    on_click_disabled_accounts
        User clicks on 'display disabled accounts' checkbox => reload tree
    on_change_selection (selected_accounts, selected_shares)
        User selects accounts or share => reload transations accordingly

    store_tree_item_selection
        Stores selected accounts/shares (for re-selection after refresh)
    restore_tree_item_selection
        Restores selected accounts/shares (used after tree refresh)
    """

    name = "Transactions"
    accounts = []
    display_hidden_accounts = False
    display_disabled_accounts = False

    def __init__(self, parent_window):
        """Stores parameters & creates all UI elements

        Parameters
        ----------
        parent_window : QtWidgets.QMainWindow
            The main window displaying this controller
        """
        self.parent_window = parent_window
        self.database = parent_window.database

        # Define GUI widgets
        self.display_widget = QtWidgets.QWidget()
        self.display_widget.layout = QtWidgets.QHBoxLayout()

        self.left_column = QtWidgets.QWidget()
        self.left_column.layout = QtWidgets.QVBoxLayout()

        self.tree = AccountsSharesTree(self)

        self.checkbox_hidden_accounts = QtWidgets.QCheckBox(
            _("Display hidden accounts?")
        )
        self.checkbox_disabled_accounts = QtWidgets.QCheckBox(
            _("Display disabled accounts?")
        )

        self.right_column = QtWidgets.QWidget()
        self.right_column.layout = QtWidgets.QVBoxLayout()

        self.table = TransactionsTableView(self)

    def get_toolbar_button(self):
        """Returns a QtWidgets.QAction for display in the main window toolbar"""
        button = QtWidgets.QAction(
            QtGui.QIcon("assets/images/transactions.png"),
            _("Transactions"),
            self.parent_window,
        )
        button.setStatusTip(_("Display transactions"))
        button.triggered.connect(lambda: self.parent_window.display_tab(self.name))
        return button

    def get_display_widget(self):
        """Returns the main QtWidgets.QWidget for this controller"""
        self.parent_window.setCentralWidget(self.display_widget)

        self.display_widget.setLayout(self.display_widget.layout)

        self.left_column.setLayout(self.left_column.layout)
        self.display_widget.layout.addWidget(self.left_column, 1)

        self.left_column.layout.addWidget(self.tree)

        self.checkbox_hidden_accounts.stateChanged.connect(
            self.on_click_hidden_accounts
        )
        self.left_column.layout.addWidget(self.checkbox_hidden_accounts)

        self.checkbox_disabled_accounts.stateChanged.connect(
            self.on_click_disabled_accounts
        )
        self.left_column.layout.addWidget(self.checkbox_disabled_accounts)

        self.right_column.setLayout(self.right_column.layout)
        self.display_widget.layout.addWidget(self.right_column, 6)

        self.right_column.layout.addWidget(self.table)

        self.reload_data()
        return self.display_widget

    def reload_data(self):
        """Reloads the list of accounts/shares"""
        self.accounts = self.database.accounts_get(
            with_hidden=self.display_hidden_accounts,
            with_disabled=self.display_disabled_accounts,
        )

        self.tree.clear()
        self.tree.fill_tree(self.accounts)

        self.table.set_filters(None, None)

    def on_click_hidden_accounts(self):
        """User clicks on 'display hidden accounts' checkbox => reload tree"""
        self.display_hidden_accounts = self.checkbox_hidden_accounts.isChecked()
        self.reload_data()
        self.checkbox_hidden_accounts.clearFocus()

    def on_click_disabled_accounts(self):
        """User clicks on 'display disabled accounts' checkbox => reload tree"""
        self.display_disabled_accounts = self.checkbox_disabled_accounts.isChecked()
        self.reload_data()
        self.checkbox_disabled_accounts.clearFocus()

    def on_change_selection(self, selected_accounts, selected_shares):
        """User selects accounts or share => reload transations accordingly

        Parameters
        ----------
        selected_accounts : list of int
            The account IDs for filtering the list of transactions
        account_shares : dict of dict of int
            The shares for filtering, in the form {account_id:[share_id]}
        """
        self.table.set_filters(selected_accounts, selected_shares)

    def store_tree_item_selection(self):
        """Stores selected accounts/shares (for re-selection after refresh)"""
        self.tree.store_item_selection()

    def restore_tree_item_selection(self):
        """Restores selected accounts/shares (used after tree refresh)"""
        self.tree.restore_item_selection()
        self.table.set_filters(self.tree.selected_accounts, self.tree.selected_shares)
