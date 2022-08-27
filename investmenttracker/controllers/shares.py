"""Displays shares, their group, most recent price & codes

Classes
----------
SharesTree
    The tree displaying the shares

SharesController
    Handles user interactions and links all displayed widgets
"""
import gettext

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

from models.base import NoPriceException, format_number
import models.share
import models.shareprice
import controllers.sharegroup
import controllers.share
from controllers.widgets import basetreecontroller

_ = gettext.gettext


class SharesTree(basetreecontroller.BaseTreeController):
    """Display of shares in tree form

    Attributes
    ----------
    columns : list of dicts
        Columns to display. Each column should have a name and size key
    selected_accounts : list of int
        The account IDs for filtering the list of transactions
    parent_controller : SharesController
        The controller in which this class is displayed
    group_details : controllers.sharegroup.ShareGroupController
        The controller for creating/editing a single share group
    share_details : controllers.share.ShareController
        The controller for creating/editing a single share

    Methods
    -------
    fill_groups (groups, shares_without_group)
        Fills the tree with the groups & shares without group
    add_group (name, group_id)
        Adds a single group (& its children) to the tree
    add_share (data, parent_widget=None)
        Adds a single share to the tree

    on_double_click
        User double-clicks: opens the share group or share create/edit dialog
    """

    columns = [
        {
            "name": _("Name"),
            "size": 0.3,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": _("ID"),
            "size": 0,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("type"),
            "size": 0,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Main code"),
            "size": 0.1,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": _("Price"),
            "size": 0.1,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Price date"),
            "size": 0.1,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Codes"),
            "size": 0.2,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": _("Get prices online from?"),
            "size": 0.1,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": _("Hidden?"),
            "size": 100,
            "alignment": Qt.AlignCenter,
        },
    ]
    group_details = None
    share_details = None

    def fill_groups(self, groups, shares_without_group):
        """Fills the tree based on provided share groups and shares without a group

        The items are directly added to the tree

        Parameters
        ----------
        groups : list of models.sharegroup.ShareGroup
            The list of share groups to display
        shares_without_group : list of models.share.Share
            The list of shares without a group to display
        """
        # Fill in the different groups
        for group in groups:
            group_widget = self.add_group(group.name, group.id)

            # Add shares
            for share in group.shares:
                if share.hidden and not self.parent_controller.display_hidden:
                    continue
                # Try to display the last price
                codes = ", ".join(
                    [
                        code.origin.value["name"] + ": " + code.value
                        for code in share.codes
                    ]
                )
                try:
                    child = [
                        share.name,
                        share.id,
                        "share",
                        share.main_code,
                        format_number(
                            share.last_price.price, share.last_price.currency.main_code
                        ),
                        QtCore.QDate(share.last_price.date).toString(
                            Qt.SystemLocaleShortDate
                        ),
                        codes,
                        share.sync_origin.value["name"] if share.sync_origin else "",
                        share.hidden,
                    ]
                except NoPriceException:
                    child = [
                        share.name,
                        share.id,
                        "share",
                        share.main_code,
                        "",
                        "",
                        codes,
                        share.sync_origin.value["name"] if share.sync_origin else "",
                        share.hidden,
                    ]

                group_widget.addChild(self.add_share(child, group_widget))

        # Add a group for shares without one
        group_widget = self.add_group(_("Shares without group"), -1)

        # Add shares without group
        for share in shares_without_group:
            # Try to display the last price
            codes = ", ".join(
                [code.origin.value["name"] + ": " + code.value for code in share.codes]
            )
            try:
                child = [
                    share.name,
                    share.id,
                    "share",
                    share.main_code,
                    format_number(
                        share.last_price.price, share.last_price.currency.main_code
                    ),
                    QtCore.QDate(share.last_price.date).toString(
                        Qt.SystemLocaleShortDate
                    ),
                    codes,
                    share.sync_origin.value["name"] if share.sync_origin else "",
                    share.hidden,
                ]
            except NoPriceException:
                child = [
                    share.name,
                    share.id,
                    "share",
                    share.main_code,
                    "",
                    "",
                    codes,
                    share.sync_origin.value["name"] if share.sync_origin else "",
                    share.hidden,
                ]

            group_widget.addChild(self.add_share(child, group_widget))

        # Add new elements
        self.add_group(_("Add new group"), 0)
        share_data = [_("Add new share"), 0, "share", "", "", "", "", "", ""]
        self.add_share(share_data)

    def add_group(self, name, group_id):
        """Adds a single share group (& its children) to the tree

        Parameters
        ----------
        data : list of fields for each column
            The share data to display
        group_id : int
            The ID of the group to add (0 for "add group")

        Returns
        -------
        QtWidgets.QTreeWidgetItem
            The share group to add in the tree
        """
        group_widget = QtWidgets.QTreeWidgetItem(
            [name, str(group_id), "group", "", "", "", "", "", ""]
        )
        self.addTopLevelItem(group_widget)

        for column, field in enumerate(self.columns):
            group_widget.setTextAlignment(column, field["alignment"])

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
            create_button.setProperty("class", "imagebutton")
            create_button.clicked.connect(
                lambda: self.on_click_edit_button(group_widget)
            )
            self.setItemWidget(group_widget, 0, create_button)

        return group_widget

    def add_share(self, data, parent_widget=None):
        """Adds a single share to the tree

        Parameters
        ----------
        data : list of fields for each column
            The share data to display
        parent_widget : QtWidgets.QTreeWidgetItem
            The parent group, if any

        Returns
        -------
        QtWidgets.QTreeWidgetItem
            The share to add in the tree
        """
        share_widget = QtWidgets.QTreeWidgetItem([str(field) for field in data])
        share_widget.setFlags(share_widget.flags() & ~Qt.ItemIsUserCheckable)
        if parent_widget:
            parent_widget.addChild(share_widget)
        else:
            self.addTopLevelItem(share_widget)
        # Add checkboxes
        for col, field in enumerate(data):
            if not isinstance(field, bool):
                continue

            val = Qt.Checked if field else Qt.Unchecked
            share_widget.setCheckState(col, val)
            share_widget.setText(col, "")

        for column, field in enumerate(self.columns):
            share_widget.setTextAlignment(column, field["alignment"])

        if data[1] == 0:
            # Apply style
            font = share_widget.font(0)
            font.setItalic(True)
            share_widget.setFont(0, font)
            share_widget.setForeground(0, QtGui.QBrush(QtGui.QColor("#A0A0A0")))
            share_widget.setIcon(0, QtGui.QIcon("assets/images/add.png"))

            # Add Create buttons
            create_button = QtWidgets.QPushButton()
            create_button.setProperty("class", "imagebutton")
            create_button.clicked.connect(
                lambda: self.on_click_edit_button(share_widget)
            )
            self.setItemWidget(share_widget, 0, create_button)

        return share_widget

    def on_double_click(self, tree_item):
        """User double-clicks: opens the share group or share create/edit dialog

        Parameters
        ----------
        tree_item : QtWidgets.QTreeWidgetItem
            The tree item being modified
        """
        if tree_item.text(2) == "group":
            self.group_details = controllers.sharegroup.ShareGroupController(
                self.parent_controller, tree_item.text(1)
            )
            self.group_details.show_window()
            del self.group_details
        elif tree_item.text(2) == "share":
            self.share_details = controllers.share.ShareController(
                self.parent_controller, tree_item.text(1)
            )
            self.share_details.show_window()
            del self.share_details


class SharesController:
    """Controller for display & interactions on accounts list

    Attributes
    ----------
    name : str
        Name of the controller - used in display
    display_hidden : bool
        Whether to display hidden shares

    groups : list of models.sharegroup.ShareGroup
        List of share groups to display in the tree
    shares_without_group : list of models.share.Share
        List of shares that do not belong to a group

    parent_window : QtWidgets.QMainWindow
        The parent window
    database : models.database.Database
        A reference to the application database

    display_widget : QtWidgets.QWidget
        The main display for this controller
    tree : SharesTree
        A tree displaying the shares
    display_hidden_widget : QtWidgets.QCheckBox
        The checkbox to display hidden shares

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

    on_click_display_hidden
        User clicks on 'display hidden shares' checkbox => reload tree
    """

    name = "Shares"
    display_hidden = False

    def __init__(self, parent_window):
        """Sets up all data required to display the screen

        Parameters
        ----------
        parent_window : QtWidgets.QMainWindow
            The window displaying this controller
        """
        self.parent_window = parent_window
        self.database = parent_window.database
        self.groups = self.database.share_groups_get_all()
        self.shares_without_group = self.database.shares_query().filter(
            models.share.Share.group == None
        )

        self.display_widget = QtWidgets.QWidget()
        self.tree = SharesTree(self)
        self.display_hidden_widget = QtWidgets.QCheckBox(_("Display hidden shares?"))

    def get_toolbar_button(self):
        """Returns a QtWidgets.QAction for display in the main window toolbar"""
        button = QtWidgets.QAction(
            QtGui.QIcon("assets/images/shares.png"), _("Shares"), self.parent_window
        )
        button.setStatusTip(_("Display shares"))
        button.triggered.connect(lambda: self.parent_window.display_tab(self.name))
        return button

    def get_display_widget(self):
        """Returns the main QtWidgets.QWidget for this controller"""
        self.display_widget.layout = QtWidgets.QVBoxLayout()
        self.display_widget.setLayout(self.display_widget.layout)

        self.display_widget.layout.addWidget(self.tree)
        self.reload_data()

        self.display_hidden_widget.stateChanged.connect(self.on_click_display_hidden)
        self.display_widget.layout.addWidget(self.display_hidden_widget)

        self.parent_window.setCentralWidget(self.display_widget)

        return self.display_widget

    def reload_data(self):
        """Reloads the list of accounts/shares (& triggers tree refresh)"""
        self.groups = self.database.share_groups_get_all()
        self.shares_without_group = self.database.shares_query().filter(
            models.share.Share.group == None
        )

        if not self.display_hidden:
            self.shares_without_group.filter(models.share.Share.hidden.is_(False))
        self.shares_without_group = self.shares_without_group.all()

        self.tree.clear()
        self.tree.fill_groups(self.groups, self.shares_without_group)

    def on_click_display_hidden(self):
        """User clicks on 'display hidden shares' checkbox => reload tree"""
        self.display_hidden = self.display_hidden_widget.isChecked()
        self.reload_data()
        self.tree.setFocus()
