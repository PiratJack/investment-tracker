import gettext

from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import Qt

import controllers.transaction

_ = gettext.gettext


class AccountsSharesTree(QtWidgets.QTreeWidget):
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
        super().__init__()
        self.parent_controller = parent_controller
        self.database = parent_controller.database

        self.setColumnCount(len(self.columns))
        self.setHeaderLabels([_(col["name"]) for col in self.columns])
        self.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.itemSelectionChanged.connect(self.on_select_item)

    def fill_tree(self, accounts):
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

            # Add held shares
            for share_id in account.shares:
                share = self.database.share_get_by_id(share_id)
                account_item.addChild(self.add_share(share, account_item))

        # Hide technical columns
        self.hideColumn(1)
        self.hideColumn(2)

    def resizeEvent(self, event):
        QtWidgets.QMainWindow.resizeEvent(self, event)
        self.set_column_sizes(event)

    def set_column_sizes(self, event):
        grid_width = (
            self.width() - sum([x["size"] for x in self.columns if x["size"] > 1]) - 10
        )
        for i, column in enumerate(self.columns):
            if self.columns[i]["size"] < 1:
                self.setColumnWidth(i, int(grid_width * self.columns[i]["size"]))
            else:
                self.setColumnWidth(i, self.columns[i]["size"])

    def add_account(self, account):
        account_item = QtWidgets.QTreeWidgetItem(
            [account.name, "account", str(account.id)]
        )
        account_item.setFlags(account_item.flags() | Qt.ItemIsAutoTristate)
        for i in range(len(self.columns)):
            account_item.setTextAlignment(i, self.columns[i]["alignment"])

        if not account.enabled or account.hidden:
            font = account_item.font(0)
            font.setItalic(True)
            account_item.setFont(0, font)

        if account.hidden:
            account_item.setForeground(0, QtGui.QBrush(QtGui.QColor("#A0A0A0")))

        return account_item

    def add_share(self, share, parent_item=None):
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

        for i in range(len(self.columns)):
            share_item.setTextAlignment(i, self.columns[i]["alignment"])

        return share_item

    def on_select_item(self):
        self.parent_controller.on_change_selection(*self.get_selected_items())

    def store_item_selection(self):
        self.selected_accounts, self.selected_shares = self.get_selected_items()

    def get_selected_items(self):
        role = Qt.DisplayRole
        selected_accounts = [
            int(i.data(2, role)) for i in self.selectedItems() if not i.parent()
        ]

        share_accounts = set(
            int(i.parent().data(2, role))
            for i in self.selectedItems()
            if i.parent() and i.parent().data(2, role) not in self.selected_accounts
        )
        selected_shares = {
            account_id: [
                int(i.data(2, role))
                for i in self.selectedItems()
                if i.parent() and i.parent().data(2, role) == str(account_id)
            ]
            for account_id in share_accounts
        }

        return (selected_accounts, selected_shares)

    def restore_item_selection(self):
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
    def __init__(self, database, columns):
        super().__init__()
        self.columns = columns
        self.database = database
        self.accounts = []
        self.transactions = []

    def columnCount(self, index):
        return len(self.columns)

    def rowCount(self, index):
        return len(self.transactions) + 1

    def data(self, index, role):
        # TODO: Sort the data by date, descending. Or allow sorting by headers
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
            currency_total = (
                transaction.quantity
                * transaction.unit_price
                * transaction.type.value["impact_currency"]
            )
            asset_total = ""
            if transaction.type.value["impact_asset"]:
                asset_total = (
                    transaction.quantity * transaction.type.value["impact_asset"]
                )
            return [
                transaction.account.name,
                transaction.id,
                str(transaction.date),
                transaction.type.value["name"],
                transaction.label,
                asset_total,
                transaction.share.short_name() if transaction.share else "",
                transaction.account.balance_after_transaction(transaction)[1],
                transaction.unit_price if transaction.unit_price != 1 else "",
                currency_total,  # Total in currency
                transaction.account.balance_after_transaction(transaction)[0],
                QtCore.QVariant(),
                QtCore.QVariant(),
            ][col]

        if (
            role == Qt.DecorationRole
            and col == len(self.columns) - 2
            and index.row() != len(self.transactions)
        ):
            return QtCore.QVariant(QtGui.QIcon("assets/images/modify.png"))
        if (
            role == Qt.DecorationRole
            and col == len(self.columns) - 1
            and index.row() != len(self.transactions)
        ):
            return QtCore.QVariant(QtGui.QIcon("assets/images/delete.png"))

        if role == Qt.TextAlignmentRole:
            return self.columns[index.column()]["alignment"]

    def headerData(self, column, orientation, role):
        if role != Qt.DisplayRole:
            return QtCore.QVariant()

        if orientation == Qt.Horizontal:
            return QtCore.QVariant(_(self.columns[column]["name"]))
        return QtCore.QVariant()

    def set_filters(self, selected_accounts=None, selected_shares=None):
        self.transactions = self.database.transaction_get_by_account_and_shares(
            selected_accounts, selected_shares
        )
        self.transactions = sorted(self.transactions, key=lambda t: (t.date, t.id))

    def get_transaction(self, index):
        return self.transactions[index.row()]


class TransactionsTableView(QtWidgets.QTableView):
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
            "size": 0.2,
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
            "size": 0.1,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Rate"),
            "size": 0.05,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Currency delta"),
            "size": 0.05,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Cash balance"),
            "size": 0.1,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Edit"),
            "size": 80,
            "alignment": Qt.AlignCenter,
        },
        {
            "name": _("Delete"),
            "size": 80,
            "alignment": Qt.AlignCenter,
        },
    ]

    def __init__(self, parent_controller):
        super().__init__()
        self.parent_controller = parent_controller
        self.database = parent_controller.database

        self.model = TransactionsTableModel(self.database, self.columns)
        self.setModel(self.model)
        self.hideColumn(1)

        self.clicked.connect(self.on_table_clicked)

    def set_filters(self, selected_accounts=None, selected_shares=None):
        self.model.set_filters(selected_accounts, selected_shares)
        self.model.layoutChanged.emit()
        self.viewport().update()

    def resizeEvent(self, event):
        QtWidgets.QMainWindow.resizeEvent(self, event)
        self.set_column_sizes(event)

    def set_column_sizes(self, event):
        grid_width = (
            self.width() - sum([x["size"] for x in self.columns if x["size"] > 1]) - 10
        )
        for i, column in enumerate(self.columns):
            if self.columns[i]["size"] < 1:
                self.setColumnWidth(i, int(grid_width * self.columns[i]["size"]))
            else:
                self.setColumnWidth(i, self.columns[i]["size"])

    def on_table_clicked(self, index):
        self.parent_controller.store_tree_item_selection()
        # New transaction
        if index.row() == len(self.model.transactions):
            self.transaction_details = controllers.transaction.TransactionController(
                self.parent_controller
            )
            self.transaction_details.show_window()

        else:
            transaction = self.model.get_transaction(index)
            # Edit button
            if index.column() == len(self.columns) - 2:
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
                        self.database.transaction_delete(transaction)
                    self.model.beginRemoveRows(index, index.row(), index.row())
                    self.set_filters()  # Reload the data
                    self.model.endRemoveRows()

        self.parent_controller.restore_tree_item_selection()


class TransactionsController:
    name = "Transactions"
    display_hidden_accounts = False
    display_disabled_accounts = False

    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.database = parent_window.database

    def get_toolbar_button(self):
        button = QtWidgets.QAction(
            QtGui.QIcon("assets/images/transactions.png"),
            _("Transactions"),
            self.parent_window,
        )
        button.setStatusTip(_("Display transactions"))
        button.triggered.connect(lambda: self.parent_window.display_tab(self.name))
        return button

    def get_display_widget(self):
        self.display_widget = QtWidgets.QWidget()
        self.display_widget.layout = QtWidgets.QHBoxLayout()
        self.display_widget.setLayout(self.display_widget.layout)

        self.parent_window.setCentralWidget(self.display_widget)

        self.left_column = QtWidgets.QWidget()
        self.left_column.layout = QtWidgets.QVBoxLayout()
        self.left_column.setLayout(self.left_column.layout)
        self.display_widget.layout.addWidget(self.left_column, 1)

        self.tree = AccountsSharesTree(self)
        self.left_column.layout.addWidget(self.tree)

        self.checkbox_hidden_accounts = QtWidgets.QCheckBox(
            _("Display hidden accounts?")
        )
        self.checkbox_hidden_accounts.stateChanged.connect(
            self.on_click_hidden_accounts
        )
        self.left_column.layout.addWidget(self.checkbox_hidden_accounts)

        self.checkbox_disabled_accounts = QtWidgets.QCheckBox(
            _("Display disabled accounts?")
        )
        self.checkbox_disabled_accounts.stateChanged.connect(
            self.on_click_disabled_accounts
        )
        self.left_column.layout.addWidget(self.checkbox_disabled_accounts)

        self.right_column = QtWidgets.QWidget()
        self.right_column.layout = QtWidgets.QVBoxLayout()
        self.right_column.setLayout(self.right_column.layout)
        self.display_widget.layout.addWidget(self.right_column, 4)

        self.table = TransactionsTableView(self)
        self.right_column.layout.addWidget(self.table)

        self.reload_data()
        return self.display_widget

    def reload_data(self):
        self.accounts = self.database.accounts_get(
            with_hidden=self.display_hidden_accounts,
            with_disabled=self.display_disabled_accounts,
        )

        self.tree.clear()
        self.tree.fill_tree(self.accounts)

        self.table.set_filters(None, None)

    def on_click_hidden_accounts(self):
        self.display_hidden_accounts = self.checkbox_hidden_accounts.isChecked()
        self.reload_data()
        self.checkbox_hidden_accounts.clearFocus()

    def on_click_disabled_accounts(self):
        self.display_disabled_accounts = self.checkbox_disabled_accounts.isChecked()
        self.reload_data()
        self.checkbox_disabled_accounts.clearFocus()

    def on_change_selection(self, selected_accounts, selected_shares):
        self.table.set_filters(selected_accounts, selected_shares)

    def store_tree_item_selection(self):
        self.tree.store_item_selection()

    def restore_tree_item_selection(self):
        self.tree.restore_item_selection()
        self.table.set_filters(self.tree.selected_accounts, self.tree.selected_shares)
