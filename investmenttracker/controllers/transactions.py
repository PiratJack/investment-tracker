import gettext

from PyQt5.QtGui import QIcon, QBrush, QColor
from PyQt5.QtWidgets import (
    QAction,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QAbstractItemView,
    QTableView,
    QMessageBox,
)
import PyQt5.QtCore
from PyQt5.QtCore import QVariant, Qt

_ = gettext.gettext


class AccountsSharesTree(QTreeWidget):
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

    def __init__(self, parent_controller):
        super().__init__()
        self.parent_controller = parent_controller
        self.database = parent_controller.database

        self.setColumnCount(len(self.columns))
        self.setHeaderLabels([_(col["name"]) for col in self.columns])
        self.setSelectionMode(QAbstractItemView.MultiSelection)
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
        PyQt5.QtWidgets.QMainWindow.resizeEvent(self, event)
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
        account_item = QTreeWidgetItem([account.name, "account", str(account.id)])
        account_item.setFlags(account_item.flags() | Qt.ItemIsAutoTristate)
        for i in range(len(self.columns)):
            account_item.setTextAlignment(i, self.columns[i]["alignment"])

        if not account.enabled or account.hidden:
            font = account_item.font(0)
            font.setItalic(True)
            account_item.setFont(0, font)

        if account.hidden:
            account_item.setForeground(0, QBrush(QColor("#A0A0A0")))

        return account_item

    def add_share(self, share, parent_item=None):
        share_item = QTreeWidgetItem(
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
        role = Qt.DisplayRole
        selected_accounts = [
            int(i.data(2, role)) for i in self.selectedItems() if not i.parent()
        ]

        share_accounts = set(
            i.parent().data(2, role)
            for i in self.selectedItems()
            if i.parent() and i.parent().data(2, role) not in selected_accounts
        )
        selected_shares = {
            account_id: [
                int(i.data(2, role))
                for i in self.selectedItems()
                if i.parent() and i.parent().data(2, role) == account_id
            ]
            for account_id in share_accounts
        }

        self.parent_controller.on_change_selection(selected_accounts, selected_shares)


class TransactionsTableModel(PyQt5.QtCore.QAbstractTableModel):
    def __init__(self, database, columns):
        super().__init__()
        self.columns = columns
        self.database = database
        self.accounts = []
        self.transactions = []

    def columnCount(self, index):
        return len(self.columns)

    def rowCount(self, index):
        return len(self.transactions)

    def data(self, index, role):
        if not index.isValid():
            return False

        col = index.column()
        if role == Qt.DisplayRole:
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
                transaction.label,
                asset_total,
                transaction.unit_price if transaction.unit_price != 1 else "",
                currency_total,  # Total in currency
                transaction.account.balance_as_of_transaction(transaction)[0],
                transaction.account.balance_as_of_transaction(transaction)[1],
                QVariant(),
            ][col]

        if role == Qt.DecorationRole and col == len(self.columns) - 1:
            return QVariant(QIcon("assets/images/delete.png"))

        if role == Qt.TextAlignmentRole:
            return self.columns[index.column()]["alignment"]

    def headerData(self, column, orientation, role):
        if role != Qt.DisplayRole:
            return QVariant()

        if orientation == Qt.Horizontal:
            return PyQt5.QtCore.QVariant(_(self.columns[column]["name"]))
        return QVariant()

    def set_filters(self, selected_accounts=None, selected_shares=None):
        self.transactions = self.database.transaction_get_by_account_and_shares(
            selected_accounts, selected_shares
        )

    def on_table_clicked(self, index):
        if index.column() == len(self.columns) - 1:
            self.on_click_delete_button(index)

    def on_click_delete_button(self, index):
        transaction = self.transactions[index.row()]
        messagebox = QMessageBox.critical(
            self.parent(),
            _("Please confirm"),
            _("Are you sure you want to delete this transaction?"),
            buttons=QMessageBox.Yes | QMessageBox.No,
            defaultButton=QMessageBox.No,
        )

        if messagebox == QMessageBox.Yes:
            if transaction.id:
                self.database.transaction_delete(transaction)
            self.beginRemoveRows(index, index.row(), index.row())
            self.set_filters()  # Reload the data
            self.endRemoveRows()


class TransactionsTableView(QTableView):
    columns = [
        {
            "name": _("Account"),
            "size": 0.2,
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
            "name": _("Label"),
            "size": 0.2,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": _("Asset delta"),
            "size": 0.1,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Rate"),
            "size": 0.1,
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
            "name": _("Asset balance"),
            "size": 0.1,
            "alignment": Qt.AlignRight,
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
        # self.setItemDelegateForColumn(0, ShareDelegate(self, self.database))
        # self.setItemDelegateForColumn(2, DateDelegate(self))
        # self.setItemDelegateForColumn(4, ShareDelegate(self, self.database))

        self.clicked.connect(self.on_table_clicked)

    def set_filters(self, selected_accounts, selected_shares):
        self.model.set_filters(selected_accounts, selected_shares)
        self.model.layoutChanged.emit()
        self.viewport().update()

    def resizeEvent(self, event):
        PyQt5.QtWidgets.QMainWindow.resizeEvent(self, event)
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
        self.model.on_table_clicked(index)


class TransactionsController:
    name = "Transactions"
    display_hidden_accounts = False
    display_disabled_accounts = False

    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.database = parent_window.database

    def get_toolbar_button(self):
        button = QAction(
            QIcon("assets/images/transactions.png"),
            _("Transactions"),
            self.parent_window,
        )
        button.setStatusTip(_("Display transactions"))
        button.triggered.connect(lambda: self.parent_window.display_tab(self.name))
        return button

    def get_display_widget(self):
        self.display_widget = QWidget()
        self.display_widget.layout = QHBoxLayout()
        self.display_widget.setLayout(self.display_widget.layout)

        self.parent_window.setCentralWidget(self.display_widget)

        self.left_column = QWidget()
        self.left_column.layout = QVBoxLayout()
        self.left_column.setLayout(self.left_column.layout)
        self.display_widget.layout.addWidget(self.left_column, 1)

        self.tree = AccountsSharesTree(self)
        self.left_column.layout.addWidget(self.tree)

        self.checkbox_hidden_accounts = QCheckBox(_("Display hidden accounts?"))
        self.checkbox_hidden_accounts.stateChanged.connect(
            self.on_click_hidden_accounts
        )
        self.left_column.layout.addWidget(self.checkbox_hidden_accounts)

        self.checkbox_disabled_accounts = QCheckBox(_("Display disabled accounts?"))
        self.checkbox_disabled_accounts.stateChanged.connect(
            self.on_click_disabled_accounts
        )
        self.left_column.layout.addWidget(self.checkbox_disabled_accounts)

        self.right_column = QWidget()
        self.right_column.layout = QVBoxLayout()
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
