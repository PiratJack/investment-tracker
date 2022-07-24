import gettext

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

from models.base import NoPriceException
import models.share
import models.shareprice
import controllers.sharegroup
import controllers.share

_ = gettext.gettext
# TODO: Double-click on tree opens edit window


class SharesTree(QtWidgets.QTreeWidget):
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
            "name": _("Main code"),
            "size": 0.2,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": _("Price"),
            "size": 0.2,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Price date"),
            "size": 0.2,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Get prices online?"),
            "size": 100,
            "alignment": Qt.AlignCenter,
        },
        {
            "name": _("Hidden?"),
            "size": 100,
            "alignment": Qt.AlignCenter,
        },
        {
            "name": _("Edit"),
            "size": 50,
            "alignment": Qt.AlignLeft,
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

    def fill_groups(self, groups, shares_without_group):
        # Fill in the data
        for group in groups:
            group_widget = self.add_group(group.name, group.id)

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
                        str(share.last_price.price)
                        + " "
                        + share.last_price.currency.main_code,
                        QtCore.QDate(share.last_price.date).toString(
                            Qt.SystemLocaleShortDate
                        ),
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

                group_widget.addChild(self.add_share(child, group_widget))

        # Add a group for shares without one
        group_widget = self.add_group(_("Shares without group"), -1)

        # Add shares without group
        for share in shares_without_group:
            # Try to display the last price
            try:
                child = [
                    share.name,
                    share.id,
                    share.main_code,
                    str(share.last_price.price)
                    + " "
                    + share.last_price.currency.main_code,
                    QtCore.QDate(share.last_price.date).toString(
                        Qt.SystemLocaleShortDate
                    ),
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

            group_widget.addChild(self.add_share(child, group_widget))

        # Add new elements
        self.add_group(_("Add new group"), 0)
        share_data = [_("Add new share"), 0, "", "", "", "", "", ""]
        self.add_share(share_data)

    def resizeEvent(self, event):
        QtWidgets.QMainWindow.resizeEvent(self, event)
        self.set_column_sizes(event)

    def set_column_sizes(self, event):
        grid_width = (
            self.width() - sum([x["size"] for x in self.columns if x["size"] > 1]) - 10
        )

        for i, column in enumerate(self.columns):
            if self.columns[i]["size"] == 0:
                self.hideColumn(i)
            elif self.columns[i]["size"] < 1:
                self.setColumnWidth(i, int(grid_width * self.columns[i]["size"]))
            else:
                self.setColumnWidth(i, self.columns[i]["size"])

    def add_group(self, name, group_id):
        group_widget = QtWidgets.QTreeWidgetItem(
            [name, str(group_id), "", "", "", "", "", ""]
        )
        self.addTopLevelItem(group_widget)

        for i in range(len(self.columns)):
            group_widget.setTextAlignment(i, self.columns[i]["alignment"])

        # Existing group that can be changed
        if group_id > 0:
            action_button = QtWidgets.QPushButton()
            action_button.setIcon(QtGui.QIcon("assets/images/modify.png"))
            action_button.setProperty("class", "imagebutton")
            action_button.clicked.connect(
                lambda _, name=("group", group_id): self.on_click_edit_button(name)
            )
            self.setItemWidget(group_widget, self.column_edit_button, action_button)

        # Shares not grouped
        if group_id <= 0:
            font = group_widget.font(0)
            font.setItalic(True)
            group_widget.setFont(0, font)

        # Add new group
        if group_id == 0:
            # Apply style
            group_widget.setForeground(0, QtGui.QBrush(QtGui.QColor("#A0A0A0")))
            group_widget.setIcon(0, QtGui.QIcon("assets/images/add.png"))

            # Add Create buttons
            create_button = QtWidgets.QPushButton()
            create_button.setProperty("class", "imagebutton align_left")
            create_button.clicked.connect(
                lambda _, name=("group", 0): self.on_click_edit_button(name)
            )
            self.setItemWidget(group_widget, 0, create_button)

        return group_widget

    def add_share(self, data, parent_widget=None):
        share_widget = QtWidgets.QTreeWidgetItem([str(field) for field in data])
        share_widget.setFlags(share_widget.flags() & ~Qt.ItemIsUserCheckable)
        if parent_widget:
            parent_widget.addChild(share_widget)
        else:
            self.addTopLevelItem(share_widget)
        # Add checkboxes
        for col, field in enumerate(data):
            if type(field) != bool:
                continue

            val = Qt.Checked if field else Qt.Unchecked
            share_widget.setCheckState(col, val)
            share_widget.setText(col, "")

        for i in range(len(self.columns)):
            share_widget.setTextAlignment(i, self.columns[i]["alignment"])

        if data[1] > 0:
            # Add share edit button
            edit_button = QtWidgets.QPushButton()
            edit_button.setIcon(QtGui.QIcon("assets/images/modify.png"))
            edit_button.setProperty("class", "imagebutton")
            edit_button.clicked.connect(
                lambda _, name=("share", data[1]): self.on_click_edit_button(name)
            )
            self.setItemWidget(share_widget, self.column_edit_button, edit_button)
        else:
            # Apply style
            font = share_widget.font(0)
            font.setItalic(True)
            share_widget.setFont(0, font)
            share_widget.setForeground(0, QtGui.QBrush(QtGui.QColor("#A0A0A0")))
            share_widget.setIcon(0, QtGui.QIcon("assets/images/add.png"))

            # Add Create buttons
            create_button = QtWidgets.QPushButton()
            create_button.setProperty("class", "imagebutton align_left")
            create_button.clicked.connect(
                lambda _, name=("share", 0): self.on_click_edit_button(name)
            )
            self.setItemWidget(share_widget, 0, create_button)

        return share_widget

    def on_click_edit_button(self, item):
        if item[0] == "group":
            self.group_details = controllers.sharegroup.ShareGroupController(
                self.parent_controller, item[1]
            )
            self.group_details.show_window()
            del self.group_details
        elif item[0] == "share":
            self.share_details = controllers.share.ShareController(
                self.parent_controller, item[1]
            )
            self.share_details.show_window()
            del self.share_details


class SharesController:
    name = "Shares"
    display_hidden = False

    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.database = parent_window.database
        self.groups = self.database.share_groups_get_all()

    def get_toolbar_button(self):
        button = QtWidgets.QAction(
            QtGui.QIcon("assets/images/shares.png"), _("Shares"), self.parent_window
        )
        button.setStatusTip(_("Display shares"))
        button.triggered.connect(lambda: self.parent_window.display_tab(self.name))
        return button

    def get_display_widget(self):
        self.display_widget = QtWidgets.QWidget()
        self.display_widget.layout = QtWidgets.QVBoxLayout()
        self.display_widget.setLayout(self.display_widget.layout)

        self.tree = SharesTree(self)
        self.display_widget.layout.addWidget(self.tree)
        self.reload_data()

        self.display_hidden_widget = QtWidgets.QCheckBox(_("Display hidden shares?"))
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
