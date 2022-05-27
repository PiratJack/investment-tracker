import gettext

from PyQt5.QtGui import QIcon, QBrush, QColor
from PyQt5.QtWidgets import (
    QAction,
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QCheckBox,
)
import PyQt5.QtCore

from models.base import NoPriceException
import controllers.account

_ = gettext.gettext
# TODO: Double-click on tree opens edit window


class AccountsTree(QTreeWidget):
    columns = [
        {
            "name": _("Name"),
            "size": 0.4,
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
            "size": 0.1,
            "alignment": PyQt5.QtCore.Qt.AlignRight,
        },
        {
            "name": _("Edit"),
            "size": 50,
            "alignment": PyQt5.QtCore.Qt.AlignLeft,
        },
    ]

    column_edit_button = 7

    def __init__(self, parent_controller):
        super().__init__()
        self.parent_controller = parent_controller
        self.setColumnCount(len(self.columns))
        self.setHeaderLabels([_(col["name"]) for col in self.columns])
        self.setSortingEnabled(True)
        self.database = parent_controller.database

    def fill_accounts(self, accounts):
        tree_items = []

        # Fill in the data
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
                    "",
                ]
            )
            for i in range(len(self.columns)):
                account_widget.setTextAlignment(i, self.columns[i]["alignment"])

            if not account.enabled:
                font = account_widget.font(0)
                font.setItalic(True)
                account_widget.setFont(0, font)

            if account.hidden:
                font = account_widget.font(0)
                font.setItalic(True)
                account_widget.setFont(0, font)
                account_widget.setForeground(0, QBrush(QColor("#A0A0A0")))

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
                        str(account.shares[share.id]),
                        str(account.shares[share.id] * last_price.price),
                        str(last_price.date),  # TODO: display date in system format
                        "",
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
                        "",
                    ]

                children.append(child)

            for child in children:
                child_widget = QTreeWidgetItem(child)
                for i in range(len(self.columns)):
                    child_widget.setTextAlignment(i, self.columns[i]["alignment"])
                account_widget.addChild(child_widget)

            tree_items.append(account_widget)

        # Add new account
        new_account_widget = QTreeWidgetItem(
            [
                _("Add new account"),
                "0",
                "",
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
        new_account_widget.setForeground(0, QBrush(QColor("#A0A0A0")))
        new_account_widget.setIcon(0, QIcon("assets/images/add.png"))
        tree_items.append(new_account_widget)

        # Put everything in the tree
        self.insertTopLevelItems(0, tree_items)
        self.hideColumn(1)

        # Add Edit buttons
        for i, account in enumerate(accounts):
            tree_item = tree_items[i]
            account_id = account.id

            edit_button = QPushButton()
            edit_button.setIcon(QIcon("assets/images/modify.png"))
            edit_button.setProperty("class", "imagebutton")
            edit_button.clicked.connect(
                lambda _, name=account_id: self.on_click_edit_button(name)
            )

            self.setItemWidget(tree_item, self.column_edit_button, edit_button)

        create_button = QPushButton()
        create_button.setProperty("class", "imagebutton align_left")
        create_button.clicked.connect(lambda _, name=0: self.on_click_edit_button(name))
        self.setItemWidget(new_account_widget, 0, create_button)

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

    def on_click_edit_button(self, account_id):
        self.account_details = controllers.account.AccountController(
            self.parent_controller, account_id
        )
        self.account_details.show_window()


class AccountsController:
    name = "Accounts"
    display_hidden = False

    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.database = parent_window.database
        self.accounts = self.database.accounts_get_all()

    def get_toolbar_button(self):
        button = QAction(
            QIcon("assets/images/accounts.png"), _("Accounts"), self.parent_window
        )
        button.setStatusTip(_("Display your accounts"))
        button.triggered.connect(lambda: self.parent_window.display_tab(self.name))
        return button

    def get_display_widget(self):
        self.display_widget = QWidget()
        self.display_widget.layout = QVBoxLayout()
        self.display_widget.setLayout(self.display_widget.layout)

        self.tree = AccountsTree(self)
        self.tree.fill_accounts(self.accounts)
        self.display_widget.layout.addWidget(self.tree)

        self.display_hidden_widget = QCheckBox(_("Display hidden accounts?"))
        self.display_hidden_widget.stateChanged.connect(self.on_click_display_hidden)
        self.display_widget.layout.addWidget(self.display_hidden_widget)

        self.parent_window.setCentralWidget(self.display_widget)

        return self.display_widget

    def reload_data(self):
        self.accounts = self.database.accounts_get(with_hidden=self.display_hidden)
        self.tree.clear()
        self.tree.fill_accounts(self.accounts)

    def on_click_display_hidden(self):
        self.display_hidden = self.display_hidden_widget.isChecked()
        self.reload_data()
        self.tree.setFocus()
