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
import models.share
import models.shareprice
import controllers.sharegroup
import controllers.share

_ = gettext.gettext


class SharesTree(QTreeWidget):
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
            "name": _("Main code"),
            "size": 0.2,
            "alignment": PyQt5.QtCore.Qt.AlignLeft,
        },
        {
            "name": _("Price"),
            "size": 0.2,
            "alignment": PyQt5.QtCore.Qt.AlignRight,
        },
        {
            "name": _("Price date"),
            "size": 0.2,
            "alignment": PyQt5.QtCore.Qt.AlignRight,
        },
        {
            "name": _("Synced?"),
            "size": 100,
            "alignment": PyQt5.QtCore.Qt.AlignCenter,
        },
        {
            "name": _("Hidden?"),
            "size": 100,
            "alignment": PyQt5.QtCore.Qt.AlignCenter,
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
        self.setHeaderLabels([col["name"] for col in self.columns])
        self.setSortingEnabled(True)
        self.database = parent_controller.database

    def fill_groups(self, groups, shares_without_group):
        edit_button = QPushButton()
        edit_button.setIcon(QIcon("assets/images/modify.png"))
        edit_button.setProperty("class", "imagebutton")
        # Fill in the data
        for group in groups:
            group_widget = QTreeWidgetItem(
                [group.name, str(group.id), "", "", "", "", "", ""]
            )
            self.addTopLevelItem(group_widget)

            for i in range(len(self.columns)):
                group_widget.setTextAlignment(i, self.columns[i]["alignment"])

            edit_button.clicked.connect(
                lambda _, name=("group", group.id): self.on_click_edit_button(name)
            )
            self.setItemWidget(group_widget, self.column_edit_button, edit_button)

            # Add shares
            for share in group.shares:
                if share.hidden and self.parent_controller.display_hidden == False:
                    continue
                # Try to display the last price
                try:
                    child = [
                        share.name,
                        share.id,
                        share.main_code,
                        str(share.last_price.price) + " " + share.last_price.currency,
                        str(
                            share.last_price.date
                        ),  # TODO: display date in system format
                        share.sync,
                        share.hidden,
                        "",
                    ]
                except NoPriceException:
                    child = [
                        share.name,
                        share.id,
                        share.main_code,
                        "",
                        "",
                        share.sync,
                        share.hidden,
                        "",
                    ]

                child_widget = QTreeWidgetItem(child)
                for i in range(len(self.columns)):
                    child_widget.setTextAlignment(i, self.columns[i]["alignment"])
                group_widget.addChild(child_widget)

                edit_button.clicked.connect(
                    lambda _, name=("share", child.id): self.on_click_edit_button(name)
                )
                self.setItemWidget(child_widget, self.column_edit_button, edit_button)

        # Add a group for shares without one
        group_widget = QTreeWidgetItem(
            [_("Shares without group"), "0", "", "", "", "", "", ""]
        )
        self.addTopLevelItem(group_widget)

        # Apply style
        font = group_widget.font(0)
        font.setItalic(True)
        group_widget.setFont(0, font)
        self.addTopLevelItem(group_widget)
        for i in range(len(self.columns)):
            group_widget.setTextAlignment(i, self.columns[i]["alignment"])

        # Add shares without group
        for share in shares_without_group:
            # Try to display the last price
            try:
                child = [
                    share.name,
                    share.id,
                    share.main_code,
                    str(share.last_price.price) + " " + share.last_price.currency,
                    str(share.last_price.date),  # TODO: display date in system format
                    share.sync,
                    share.hidden,
                    "",
                ]
            except NoPriceException:
                child = [
                    share.name,
                    share.id,
                    share.main_code,
                    "",
                    "",
                    share.sync,
                    share.hidden,
                    "",
                ]

            child_widget = QTreeWidgetItem(child)
            for i in range(len(self.columns)):
                child_widget.setTextAlignment(i, self.columns[i]["alignment"])
            group_widget.addChild(child_widget)

            edit_button.clicked.connect(
                lambda _, name=("share", child.id): self.on_click_edit_button(name)
            )
            self.setItemWidget(child_widget, self.column_edit_button, edit_button)

        # Add new elements
        add_new = ("group", _("Add new group")), ("share", _("Add new share"))
        for item, label in add_new:
            new_item_widget = QTreeWidgetItem([label, "0", "", "", "", "", "", ""])

            # Apply style
            font = new_item_widget.font(0)
            font.setItalic(True)
            new_item_widget.setFont(0, font)
            new_item_widget.setForeground(0, QBrush(QColor("#A0A0A0")))
            new_item_widget.setIcon(0, QIcon("assets/images/add.png"))
            self.addTopLevelItem(new_item_widget)

            # Add Create buttons
            create_button = QPushButton()
            create_button.setProperty("class", "imagebutton align_left")
            create_button.clicked.connect(
                lambda _, name=(item, 0): self.on_click_edit_button(name)
            )
            self.setItemWidget(new_item_widget, 0, create_button)

        # Overall elements
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

    def on_click_edit_button(self, item):
        print("DEBUG clicked", item)
        if item[0] == "group":
            self.group_details = controllers.sharegroup.ShareGroupController(
                self.parent_controller, item[1]
            )
            self.group_details.show_window()
        elif item[0] == "share":
            self.group_details = controllers.share.ShareController(
                self.parent_controller, item[1]
            )
            self.group_details.show_window()


class SharesController:
    name = "Shares"
    display_hidden = False

    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.database = parent_window.database
        self.groups = self.database.share_groups_get_all()

    def get_toolbar_button(self):
        button = QAction(
            QIcon("assets/images/shares.png"), _("Shares"), self.parent_window
        )
        button.setStatusTip(_("Display shares"))
        button.triggered.connect(lambda: self.parent_window.display_tab(self.name))
        return button

    def get_display_widget(self):
        self.display_widget = QWidget()
        self.display_widget.layout = QVBoxLayout()
        self.display_widget.setLayout(self.display_widget.layout)

        self.tree = SharesTree(self)
        self.display_widget.layout.addWidget(self.tree)
        self.reload_data()

        self.display_hidden_widget = QCheckBox(_("Display hidden accounts?"))
        self.display_hidden_widget.stateChanged.connect(self.on_click_display_hidden)
        self.display_widget.layout.addWidget(self.display_hidden_widget)

        self.parent_window.setCentralWidget(self.display_widget)

        return self.display_widget

    def reload_data(self):
        self.groups = self.database.share_groups_get_all()
        self.shares_without_group = self.database.shares_query().filter(
            models.share.Share.group == None
        )

        if not self.display_hidden:
            self.shares_without_group.filter(models.share.Share.hidden == False)
        self.shares_without_group = self.shares_without_group.all()

        self.tree.clear()
        self.tree.fill_groups(self.groups, self.shares_without_group)

    def on_click_display_hidden(self):
        self.display_hidden = self.display_hidden_widget.isChecked()
        self.reload_data()
        self.tree.setFocus()
