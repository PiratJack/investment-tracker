import gettext

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

from models.base import NoPriceException, format_number
import controllers.account
from controllers.widgets import basetreecontroller

_ = gettext.gettext


class AccountsTree(basetreecontroller.BaseTreeController):
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
        {
            "name": _("Edit"),
            "size": 50,
            "alignment": Qt.AlignLeft,
        },
    ]

    column_edit_button = 7

    def fill_accounts(self, accounts):
        tree_items = []

        # Fill in the data
        for account in accounts:
            try:
                value = format_number(
                    account.total_value, account.base_currency.main_code
                )
            except:
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
                        "",
                    ]

                children.append(child)

            for child in children:
                child_widget = QtWidgets.QTreeWidgetItem(child)
                for i in range(len(self.columns)):
                    child_widget.setTextAlignment(i, self.columns[i]["alignment"])
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

        # Add Edit buttons
        for i, account in enumerate(accounts):
            tree_item = tree_items[i]
            account_id = account.id

            edit_button = QtWidgets.QPushButton()
            edit_button.setIcon(QtGui.QIcon("assets/images/modify.png"))
            edit_button.setProperty("class", "imagebutton")
            edit_button.clicked.connect(
                lambda _, name=account_id: self.on_click_edit_button(name)
            )

            self.setItemWidget(tree_item, self.column_edit_button, edit_button)

        create_button = QtWidgets.QPushButton()
        create_button.setProperty("class", "imagebutton align_left")
        create_button.clicked.connect(lambda _, name=0: self.on_click_edit_button(name))
        self.setItemWidget(new_account_widget, 0, create_button)

    def on_click_edit_button(self, tree_item):
        self.account_details = controllers.account.AccountController(
            self.parent_controller, tree_item.text(1)
        )
        self.account_details.show_window()


class AccountsController:
    name = "Accounts"
    display_hidden = False
    display_disabled = False

    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.database = parent_window.database
        self.accounts = self.database.accounts_get()

    def get_toolbar_button(self):
        button = QtWidgets.QAction(
            QtGui.QIcon("assets/images/accounts.png"), _("Accounts"), self.parent_window
        )
        button.setStatusTip(_("Display your accounts"))
        button.triggered.connect(lambda: self.parent_window.display_tab(self.name))
        return button

    def get_display_widget(self):
        self.display_widget = QtWidgets.QWidget()
        self.display_widget.layout = QtWidgets.QVBoxLayout()
        self.display_widget.setLayout(self.display_widget.layout)

        self.tree = AccountsTree(self)
        self.tree.fill_accounts(self.accounts)
        self.display_widget.layout.addWidget(self.tree)

        self.checkbox_hidden = QtWidgets.QCheckBox(_("Display hidden accounts?"))
        self.checkbox_hidden.stateChanged.connect(self.on_click_checkbox_hidden)
        self.display_widget.layout.addWidget(self.checkbox_hidden)

        self.checkbox_disabled = QtWidgets.QCheckBox(_("Display disabled accounts?"))
        self.checkbox_disabled.stateChanged.connect(self.on_click_checkbox_disabled)
        self.display_widget.layout.addWidget(self.checkbox_disabled)

        self.parent_window.setCentralWidget(self.display_widget)

        return self.display_widget

    def reload_data(self):
        self.accounts = self.database.accounts_get(
            with_hidden=self.display_hidden, with_disabled=self.display_disabled
        )
        self.tree.clear()
        self.tree.fill_accounts(self.accounts)

    def on_click_checkbox_hidden(self):
        self.display_hidden = self.checkbox_hidden.isChecked()
        self.reload_data()
        self.checkbox_hidden.clearFocus()

    def on_click_checkbox_disabled(self):
        self.display_disabled = self.checkbox_disabled.isChecked()
        self.reload_data()
        self.checkbox_disabled.clearFocus()
