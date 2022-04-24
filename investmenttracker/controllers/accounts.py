import gettext

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QTreeWidget, QTreeWidgetItem, QPushButton
import PyQt5.QtCore

from models.base import NoPriceException
import models.shareprice

_ = gettext.gettext


class AccountsTree(QTreeWidget):
    columns = [
        {
            "name": _("Name"),
            "size": 0.3,
            "alignment": PyQt5.QtCore.Qt.AlignLeft,
        },
        {
            "name": _("ID"),
            "size": 0,
            "alignment": PyQt5.QtCore.Qt.AlignRight,
        },
        {
            "name": _("Code"),
            "size": 0.2,
            "alignment": PyQt5.QtCore.Qt.AlignLeft,
        },
        {
            "name": _("Quantity"),
            "size": 0.1,
            "alignment": PyQt5.QtCore.Qt.AlignRight,
        },
        {
            "name": _("Value"),
            "size": 0.1,
            "alignment": PyQt5.QtCore.Qt.AlignRight,
        },
        {
            "name": _("As of date"),
            "size": 0.1,
            "alignment": PyQt5.QtCore.Qt.AlignRight,
        },
        {
            "name": _("Total invested"),
            "size": 0.2,
            "alignment": PyQt5.QtCore.Qt.AlignRight,
        },
    ]

    def __init__(self, database):
        super().__init__()
        self.setColumnCount(len(self.columns))
        self.setHeaderLabels([col["name"] for col in self.columns])
        self.setSortingEnabled(True)
        self.database = database

    def fill_accounts(self, accounts):
        tree_items = []

        for account in accounts:
            account_widget = QTreeWidgetItem(
                [
                    account.name,
                    str(account.id),
                    account.code,
                    "",
                    str(account.total_value),
                    "",
                    str(account.total_invested),
                ]
            )
            for i in range(len(self.columns)):
                account_widget.setTextAlignment(i, self.columns[i]["alignment"])

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
                        str(account.shares[share.id]),
                        str(account.shares[share.id] * last_price.price),
                        str(last_price.date),  # TODO: display date in system format
                        "",
                    ]
                except NoPriceException:
                    child = [
                        share.name,
                        "",
                        share.main_code,
                        str(account.shares[share.id]),
                        _("Unknown"),
                        _("Unknown"),
                        "",
                    ]

                children.append(child)

            for child in children:
                child_widget = QTreeWidgetItem(child)
                for i in range(len(self.columns)):
                    child_widget.setTextAlignment(i, self.columns[i]["alignment"])
                account_widget.addChild(child_widget)

            tree_items.append(account_widget)

        self.insertTopLevelItems(0, tree_items)
        self.hideColumn(1)

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


class AccountsController:
    name = "Accounts"

    def __init__(self, parent):
        self.parent = parent
        self.database = parent.database
        self.accounts = self.database.accounts_get_all()

    def get_toolbar_button(self, window):
        button = QAction(QIcon("assets/images/accounts.png"), _("Accounts"), window)
        button.setStatusTip(_("Display your accounts"))
        button.triggered.connect(lambda: window.display_tab(self.name))
        return button

    def get_window(self, window):
        self.tree = AccountsTree(self.database)
        self.tree.fill_accounts(self.accounts)
        window.setCentralWidget(self.tree)

        return self.tree
