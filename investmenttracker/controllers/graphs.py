"""Displays different graphs & performance calculations for analysis

Classes
----------
PerformanceTable
    A table displaying account & share performance over time

GraphsController
    Controller for graph display - handles user interactions & children widgets
"""
import gettext
import datetime
import locale

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt

import models.share
import controllers.widgets.accountstree
import controllers.widgets.sharestree
import controllers.widgets.graphsarea
from models.base import NoPriceException, format_number

_ = gettext.gettext


class PerformanceTable(QtWidgets.QTableWidget):
    """A table displaying account & share performance over time

    Attributes
    ----------

    selected_accounts : list of int
        The list of selected account IDs
    selected_shares : list of int
        The list of selected share IDs

    start_date : datetime.date
        The first date to display in the table
    end_date : datetime.date
        The last date to display in the table

    parent_controller : GraphsController
        The controller in which this class is displayed
    database : models.database.Database
        A reference to the application database


    Methods
    -------
    __init__ (parent_controller)
        Stores provided parameters

    set_dates (start_date, end_date)
        Defines the start & end date for the table calculation & triggers reload
    set_shares (selected_shares)
        Defines which shares to display & triggers reload
    set_accounts (selected_accounts)
        Defines which accounts to display & triggers reload

    reload_data
        Recalculates the table contents
    """

    selected_shares = []
    selected_accounts = []
    start_date = None
    end_date = None

    def __init__(self, parent_controller):
        """Stores provided parameters

        Parameters
        ----------
        parent_controller : GraphsController
            The controller in which this class is displayed
        """
        super().__init__()
        self.parent_controller = parent_controller
        self.database = parent_controller.database

    def set_dates(self, start_date, end_date):
        """Defines the start & end date for the table calculation & triggers reload

        Parameters
        ----------
        start_date : datetime.date
            The first date to display in the table
        end_date : datetime.date
            The last date to display in the table
        """
        self.start_date = start_date
        self.end_date = end_date
        self.reload_data()

    def set_shares(self, selected_shares):
        """Defines which shares to display & triggers reload

        Parameters
        ----------
        selected_shares : list of int
            The list of selected share IDs
        """
        self.selected_shares = selected_shares
        self.reload_data()

    def set_accounts(self, selected_accounts):
        """Defines which accounts to display & triggers reload

        Parameters
        ----------
        selected_accounts : list of int
            The list of selected account IDs
        """
        self.selected_accounts = selected_accounts
        self.reload_data()

    def reload_data(self):
        """Recalculates the table contents"""
        table_rows = []

        # Determine dates & set headers
        all_dates = []
        table_row = [""]
        current_date = datetime.date(self.start_date.year, self.start_date.month, 1)
        while current_date <= self.end_date:
            all_dates.append(current_date)
            table_row.append(current_date.strftime("%x"))
            if current_date.month == 12:
                current_date = datetime.date(current_date.year + 1, 1, 1)
            else:
                current_date = datetime.date(
                    current_date.year, current_date.month + 1, 1
                )
        self.setColumnCount(len(table_row))
        self.setHorizontalHeaderLabels(table_row)

        for share_id in self.selected_shares:
            share = self.database.share_get_by_id(share_id)

            table_row = [share.name]
            base_price = None
            for current_date in all_dates:
                price = self.database.share_prices_get(
                    share_id=share,
                    start_date=current_date,
                    currency_id=share.base_currency,
                )
                if not price:
                    data = _("Unknown")
                else:
                    max_date = max(p.date for p in price)
                    max_price = [p for p in price if p.date == max_date][0]
                    data = format_number(max_price.price, share.base_currency.main_code)
                    if base_price:
                        evolution = (max_price.price - base_price) / base_price
                        data += "\n" + locale.format_string("%.2f %%", evolution)
                    else:
                        base_price = max_price.price

                table_row.append(data)
            table_rows.append(table_row)

        for account_id in self.selected_accounts:
            account = self.database.account_get_by_id(account_id)

            table_row = [account.name]
            base_amount = None

            for current_date in all_dates:
                prior_dates = [d for d in account.holdings if d <= current_date]
                if not prior_dates:
                    data = _("Unknown")
                else:
                    holding_date = max(prior_dates)
                    holdings = account.holdings[holding_date]
                    total_amount = holdings["cash"]
                    for share_id, share_nb in holdings["shares"].items():
                        price = self.database.share_prices_get(
                            share_id=share_id,
                            start_date=current_date,
                            currency_id=account.base_currency,
                        )
                        if not price:
                            data = _("Unknown")
                            break
                        max_date = max(p.date for p in price)
                        max_price = [p for p in price if p.date == max_date][0]
                        total_amount += share_nb * max_price.price

                    data = format_number(total_amount, account.base_currency.main_code)
                    if base_amount:
                        evolution = (total_amount - base_amount) / base_amount
                        data += "\n" + locale.format_string("%.2f %%", evolution)
                    else:
                        base_amount = total_amount
                table_row.append(data)
            table_rows.append(table_row)

        self.setRowCount(len(table_rows))

        for row, table_row in enumerate(table_rows):
            for column, value in enumerate(table_row):
                # Skip name, will be added through headers
                if column == 0:
                    continue
                item = QtWidgets.QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignRight)
                self.setItem(row, column, item)

        self.setVerticalHeaderLabels([a[0] for a in table_rows])
        self.resizeColumnsToContents()
        self.resizeRowsToContents()


class GraphsController:
    """Controller for display & interactions on transactions list

    Attributes
    ----------
    name : str
        Name of the controller - used in display
    display_hidden_accounts : bool
        Whether to display hidden accounts
    display_disabled_accounts : bool
        Whether to display disabled accounts
    display_hidden_shares : QtWidgets.QCheckBox
        The checkbox to display hidden shares

    errors : list
        Errors to display

    accounts : list of models.account.Account
        List of accounts to display in the tree
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
    left_column : QtWidgets.QWidget
        The left column of the screen
    accounts_tree : controllers.widgets.accountstree.AccountsTree
        Displays accounts so the user can choose what to display in the graph
    checkbox_hidden_accounts : bool
        The checkbox to display hidden accounts
    checkbox_disabled_accounts : bool
        The checkbox to display disabled accounts
    shares_tree : controllers.widgets.sharestree.SharesTree
        Displays shares so the user can choose what to display in the graph
    checkbox_hidden_shares : bool
        The checkbox to display hidden shares

    right_column : QtWidgets.QWidget
        The right column of the screen
    period_label : QtWidgets.QLabel
        Label 'Period' (of time to display)

    start_date = QtWidgets.QDateEdit
        The first date to display in the graph
    end_date = QtWidgets.QDateEdit
        The last date to display in the graph

    baseline_enabled = QtWidgets.QCheckBox
        Checkbox to display amounts in % of a the value on a given date
    baseline_label = QtWidgets.QLabel
        Label 'Baseline date'
    baseline_date = QtWidgets.QDateEdit
        Date used as baseline for precentage-based graph
    split_enabled = QtWidgets.QCheckBox
        Display the account composition (each share as % of the account's total)

    error_messages = QtWidgets.QLabel
        Label displaying errors
    graph = controllers.widgets.graphsarea.GraphsArea
        The main graph displaying account & share evolution
    markers_visible = QtWidgets.QCheckBox
        Checkbox to display markers
    performance_table = PerformanceTable
        A table displaying account & share performance over time

    Methods
    -------
    __init__ (parent_window)
        Stores provided parameters & sets up UI items
    get_toolbar_button
        Returns a QtWidgets.QAction for display in the main window toolbar
    get_display_widget
        Returns the main QtWidgets.QWidget for this controller
    reload_data (reload_accounts=False)
        Reloads the list of accounts/shares (if reload_accounts=True)

    render_left_column
        Renders the left column of the display
    render_right_column
        Renders the right column of the display

    on_click_hidden_accounts
        User clicks on 'display hidden accounts' checkbox => reload tree
    on_click_disabled_accounts
        User clicks on 'display disabled accounts' checkbox => reload tree
    on_change_dates
        User changes one of the dates => calculate & render graph with new dates
    on_change_account_selection (selected_accounts)
        User changes selection of accounts => display them in graph & table
    on_change_share_selection (selected_shares)
        User changes selection of shares => display them in graph & table
    on_baseline_change
        User clicks on 'Display evolution' checkbox => reload graph
    on_display_split_change
        User clicks on 'Display composition' checkbox => reload graph
    on_markers_change
        User clicks on 'Display markers' checkbox => display/hide them

    reset_errors
        Removes all errors being displayed
    add_error (exception)
        Adds an error for display
    """

    name = "Graphs"
    display_hidden_accounts = False
    display_disabled_accounts = False
    display_hidden_shares = False

    errors = []

    def __init__(self, parent_window):
        """Sets up all data required to display the screen

        Parameters
        ----------
        parent_window : QtWidgets.QMainWindow
            The window displaying this controller
        """
        self.parent_window = parent_window
        self.database = parent_window.database

        # Data
        self.accounts = []
        self.groups = []
        self.shares_without_group = []

        # Display elements
        self.display_widget = QtWidgets.QWidget()

        # Left column: select accounts & shares
        self.left_column = QtWidgets.QWidget()
        self.accounts_tree = controllers.widgets.accountstree.AccountsTree(self)
        self.checkbox_hidden_accounts = QtWidgets.QCheckBox(
            _("Display hidden accounts?")
        )
        self.checkbox_disabled_accounts = QtWidgets.QCheckBox(
            _("Display disabled accounts?")
        )
        self.shares_tree = controllers.widgets.sharestree.SharesTree(self)
        self.checkbox_hidden_shares = QtWidgets.QCheckBox(_("Display hidden shares?"))

        # Right column: parameters, graph & performance table
        self.right_column = QtWidgets.QWidget()

        self.period_label = QtWidgets.QLabel(_("Period"))
        self.start_date = QtWidgets.QDateEdit()
        self.end_date = QtWidgets.QDateEdit()

        self.baseline_enabled = QtWidgets.QCheckBox(_("Display evolution?"))
        self.baseline_label = QtWidgets.QLabel(_("Baseline date"))
        self.baseline_date = QtWidgets.QDateEdit()
        self.split_enabled = QtWidgets.QCheckBox(_("Display account composition?"))

        self.error_messages = QtWidgets.QLabel()
        self.graph = controllers.widgets.graphsarea.GraphsArea(self)

        self.markers_visible = QtWidgets.QCheckBox(_("Display markers?"))
        self.performance_table = PerformanceTable(self)

    def get_toolbar_button(self):
        """Returns a QtWidgets.QAction for display in the main window toolbar"""
        button = QtWidgets.QAction(
            QtGui.QIcon("assets/images/graphs.png"), _("Graphs"), self.parent_window
        )
        button.setStatusTip(_("Display graphs"))
        button.triggered.connect(lambda: self.parent_window.display_tab(self.name))
        return button

    def get_display_widget(self):
        """Returns the main QtWidgets.QWidget for this controller"""
        self.display_widget.layout = QtWidgets.QHBoxLayout()
        self.display_widget.setLayout(self.display_widget.layout)

        self.parent_window.setCentralWidget(self.display_widget)

        self.render_left_column()
        self.display_widget.layout.addWidget(self.left_column, 1)

        self.render_right_column()
        self.display_widget.layout.addWidget(self.right_column, 5)

        self.reload_data()
        return self.display_widget

    def render_left_column(self):
        """Renders the left column of the display"""
        self.left_column.layout = QtWidgets.QVBoxLayout()
        self.left_column.setLayout(self.left_column.layout)

        self.left_column.layout.addWidget(self.accounts_tree)

        self.checkbox_hidden_accounts.stateChanged.connect(
            self.on_click_hidden_accounts
        )
        self.left_column.layout.addWidget(self.checkbox_hidden_accounts)

        self.checkbox_disabled_accounts.stateChanged.connect(
            self.on_click_disabled_accounts
        )
        self.left_column.layout.addWidget(self.checkbox_disabled_accounts)

        self.left_column.layout.addWidget(self.shares_tree)

        self.checkbox_hidden_shares.stateChanged.connect(
            self.on_click_disabled_accounts
        )
        self.left_column.layout.addWidget(self.checkbox_hidden_shares)

    def render_right_column(self):
        """Renders the right column of the display"""
        self.right_column.layout = QtWidgets.QGridLayout()
        self.right_column.setLayout(self.right_column.layout)

        self.right_column.layout.setHorizontalSpacing(
            self.right_column.layout.horizontalSpacing() * 3
        )

        # Choose which dates to display
        self.right_column.layout.addWidget(self.period_label, 0, 0)

        self.start_date.setDate(datetime.date.today() - datetime.timedelta(6 * 30))
        self.start_date.dateChanged.connect(self.on_change_dates)
        self.right_column.layout.addWidget(self.start_date, 0, 1)
        date_width = self.start_date.sizeHint().width()
        self.start_date.setMinimumWidth(date_width * 2)

        self.end_date.setDate(datetime.date.today())
        self.end_date.dateChanged.connect(self.on_change_dates)
        self.right_column.layout.addWidget(self.end_date, 0, 2)
        self.end_date.setMinimumWidth(date_width * 2)

        # Choose whether to display baseline (= one date equals 100%)
        self.baseline_enabled.stateChanged.connect(self.on_baseline_change)
        self.right_column.layout.addWidget(self.baseline_enabled, 1, 0)
        self.right_column.layout.addWidget(self.baseline_label, 1, 1, Qt.AlignRight)

        self.baseline_date.setDate(datetime.date.today() - datetime.timedelta(6 * 30))
        self.baseline_date.dateChanged.connect(self.on_baseline_change)
        self.right_column.layout.addWidget(self.baseline_date, 1, 2)
        self.baseline_date.setMinimumWidth(date_width * 2)

        # Display account split?
        self.split_enabled.stateChanged.connect(self.on_display_split_change)
        self.right_column.layout.addWidget(self.split_enabled, 1, 3)

        # Error messages
        self.error_messages.setProperty("class", "validation_warning")
        self.right_column.layout.addWidget(self.error_messages, 2, 0, 1, 5)

        # Add the graph
        self.right_column.layout.addWidget(self.graph, 3, 0, 1, 5)

        # Choose whether to display markers
        self.markers_visible.setChecked(True)
        self.markers_visible.stateChanged.connect(self.on_markers_change)
        self.right_column.layout.addWidget(self.markers_visible, 4, 0)

        # Performance table
        self.right_column.layout.addWidget(self.performance_table, 5, 0, 1, 5)

        # Trigger date change once all dates are set
        self.on_change_dates()

    def reload_data(self):
        """Reloads the list of accounts & shares"""
        self.accounts = self.database.accounts_get(
            with_hidden=self.display_hidden_accounts,
            with_disabled=self.display_disabled_accounts,
        )

        self.accounts_tree.clear()
        self.accounts_tree.fill_tree(self.accounts)

        self.groups = self.database.share_groups_get_all()
        self.shares_without_group = self.database.shares_query().filter(
            models.share.Share.group == None
        )

        if not self.display_hidden_shares:
            self.shares_without_group.filter(models.share.Share.hidden == False)
        self.shares_without_group = self.shares_without_group.all()

        self.shares_tree.clear()
        self.shares_tree.fill_tree(self.groups, self.shares_without_group)

        self.graph.set_accounts()
        self.graph.set_shares()

        # TODO: also reload graph data

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

    def on_change_dates(self):
        """User changes one of the dates => calculate & render graph with new dates"""
        self.reset_errors()
        start_date = datetime.date.fromisoformat(
            self.start_date.date().toString(Qt.ISODate)
        )
        end_date = datetime.date.fromisoformat(
            self.end_date.date().toString(Qt.ISODate)
        )
        self.graph.set_dates(start_date, end_date)
        self.performance_table.set_dates(start_date, end_date)

    def on_change_account_selection(self, selected_accounts):
        """User changes selection of accounts => display them in graph & table

        Parameters
        ----------
        selected_accounts : list of int
            The list of selected account IDs
        """
        self.reset_errors()
        self.graph.set_accounts(selected_accounts)
        self.performance_table.set_accounts(selected_accounts)

    def on_change_share_selection(self, selected_shares):
        """User changes selection of shares => display them in graph & table

        Parameters
        ----------
        selected_shares : list of int
            The list of selected share IDs
        """
        self.reset_errors()
        self.graph.set_shares(selected_shares)
        self.performance_table.set_shares(selected_shares)

    def on_baseline_change(self):
        """User clicks on 'Display evolution' checkbox => reload graph"""
        baseline_date = datetime.date.fromisoformat(
            self.baseline_date.date().toString(Qt.ISODate)
        )
        self.split_enabled.setEnabled(not self.baseline_enabled.isChecked())

        self.graph.set_baseline(self.baseline_enabled.isChecked(), baseline_date)

    def on_display_split_change(self):
        """User clicks on 'Display composition' checkbox => reload graph"""
        self.baseline_enabled.setEnabled(not self.split_enabled.isChecked())
        self.baseline_date.setEnabled(not self.split_enabled.isChecked())
        try:
            self.graph.set_account_split(self.split_enabled.isChecked())
        except (UserWarning, NoPriceException) as exception:
            self.add_error(exception)
        if not self.split_enabled.isChecked():
            self.accounts_tree.on_select_item()
            self.shares_tree.on_select_item()
            self.on_change_dates()

    def on_markers_change(self):
        """User clicks on 'Display markers' checkbox => display/hide them"""
        self.graph.set_markers_visible(self.markers_visible.isChecked())

    def reset_errors(self):
        """Removes all errors being displayed"""
        self.errors = []
        self.error_messages.setText("")

    def add_error(self, exception):
        """Adds an error for display

        Parameters
        ----------
        exception : Exception
            The exception raised during the calculation
        """
        self.errors.append(exception)
        messages = []
        for error in self.errors:
            if isinstance(error, UserWarning):
                messages.append(str(error))
            elif isinstance(error, NoPriceException):
                messages.append(
                    _(
                        "Could not display account {account} due to missing value for {share}"
                    ).format(account=error.account.name, share=error.share.name)
                )
            else:
                raise error
        messages = set(messages)
        self.error_messages.setText("\n".join(messages))
