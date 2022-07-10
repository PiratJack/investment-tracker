import gettext
import datetime

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt

import pyqtgraph

import models.share
from models.base import NoPriceException

_ = gettext.gettext

# TODO: Have different colors for each share / account (accounts should have a stronger shade)
# TODO: Display value on markers
# TODO: Move X axis based on the selected range


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

    def on_select_item(self):
        self.parent_controller.on_change_account_selection(self.get_selected_items())

    def store_item_selection(self):
        self.selected_accounts = self.get_selected_items()

    def get_selected_items(self):
        role = Qt.DisplayRole
        self.selected_accounts = [
            int(i.data(2, role)) for i in self.selectedItems() if not i.parent()
        ]

        return self.selected_accounts

    def restore_item_selection(self):
        for account_id in self.selected_accounts:
            items = self.findItems(str(account_id), Qt.MatchExactly, 2)
            for item in items:
                item.setSelected(True)


class SharesTree(QtWidgets.QTreeWidget):
    columns = [
        {
            "name": _("Name"),
            "size": 1,
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
        self.setSortingEnabled(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.itemSelectionChanged.connect(self.on_select_item)

    def fill_tree(self, groups, shares_without_group):
        # Add shares within a group
        for group in groups:
            group_widget = self.add_group(group.name, group.id)
            for share in group.shares:
                if (
                    share.hidden
                    and self.parent_controller.display_hidden_shares == False
                ):
                    continue
                group_widget.addChild(
                    self.add_share([share.name, "Share", share.id], group_widget)
                )

        # Add shares without group
        group_widget = self.add_group(_("Shares without group"), -1)
        for share in shares_without_group:
            group_widget.addChild(
                self.add_share([share.name, "Share", share.id], group_widget)
            )

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
        group_widget = QtWidgets.QTreeWidgetItem([name, "Group", str(group_id)])
        self.addTopLevelItem(group_widget)

        for i in range(len(self.columns)):
            group_widget.setTextAlignment(i, self.columns[i]["alignment"])

        # Shares not grouped
        if group_id <= 0:
            font = group_widget.font(0)
            font.setItalic(True)
            group_widget.setFont(0, font)

        return group_widget

    def add_share(self, data, parent_widget=None):
        share_widget = QtWidgets.QTreeWidgetItem([str(field) for field in data])
        share_widget.setFlags(share_widget.flags() & ~Qt.ItemIsUserCheckable)
        if parent_widget:
            parent_widget.addChild(share_widget)
        else:
            self.addTopLevelItem(share_widget)

        for i in range(len(self.columns)):
            share_widget.setTextAlignment(i, self.columns[i]["alignment"])

        return share_widget

    def get_selected_items(self):
        role = Qt.DisplayRole

        self.selected_shares = [
            int(i.data(2, role)) for i in self.selectedItems() if i.parent()
        ]

        return self.selected_shares

    def on_select_item(self):
        self.parent_controller.on_change_share_selection(self.get_selected_items())


class GraphsArea(pyqtgraph.PlotWidget):
    graph_types = {
        "value": {
            "min": 0,
        },
        "split": {
            "min": 0,
            "max": 1,
        },
        "base_100": {
            "min": 0,
        },
    }

    all_accounts = {}
    all_shares = {}

    selected_accounts = []
    selected_shares = []

    # Structure: {
    # date (as datetime.date): {
    #     'shares': {
    #         share_id: count
    #     },
    #     'cash': cash_value
    # }
    # One date element per transaction date
    accounts_holdings = {}

    shares_raw_values = {}
    accounts_raw_values = {}

    shares_graph_values = {}
    accounts_graph_values = {}

    start_date = None
    end_date = None

    plots = {}

    def __init__(self, parent_controller):
        super().__init__(axisItems={"bottom": pyqtgraph.DateAxisItem()})
        self.parent_controller = parent_controller
        self.database = parent_controller.database

        self.all_accounts = {a.id: a for a in self.database.accounts_get(True, True)}
        self.accounts_graph_values = {a: {} for a in self.all_accounts}
        self.all_shares = {s.id: s for s in self.database.shares_get(True)}
        self.shares_graph_values = {s: {} for s in self.all_shares}

        self.axisItems = {"bottom": pyqtgraph.DateAxisItem(orientation="bottom")}

        self.setMouseEnabled(x=True, y=False)
        self.enableAutoRange(axis="x")

        self.plots["legend"] = self.addLegend()

        # TODO: different types of graphs:
        #  TODO: - Account split (with total = 100%) - should display % in vertical axis
        #  TODO: - Value of each element, with base 100 at a given date
        self.graph_type = "value"

    def set_accounts(self, selected_accounts=[]):
        self.selected_accounts = selected_accounts
        if selected_accounts:
            self.calculate_accounts(selected_accounts)
        self.plot_graph()

    def set_shares(self, selected_shares=[]):
        self.selected_shares = selected_shares
        if selected_shares:
            self.calculate_shares(selected_shares)
        self.plot_graph()

    def set_dates(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date

        self.calculate_accounts(self.selected_accounts)
        self.calculate_shares(self.selected_shares)
        self.plot_graph()

    def calculate_shares(self, shares):
        if not self.start_date or not self.end_date or not shares:
            return

        for share_id in shares:
            share = self.all_shares[share_id]
            ranges_missing = self.find_missing_date_ranges(
                self.shares_raw_values, share_id
            )
            if share_id not in self.shares_raw_values:
                self.shares_raw_values[share_id] = {}

            for range_missing in ranges_missing:
                values = self.database.share_price_get(
                    share, share.base_currency, *range_missing
                )
                self.shares_raw_values[share_id] |= {v.date: v.price for v in values}

    # The goal of this function is to calculate the account's value for the graph
    # There are several challenges:
    # - We don't want to calculate outside of what's needed (to improve performance)
    # - At each transaction, the holdings (= # of shares & cash) changes
    # - Each share held may change value multiple times
    # - We can't assume any of those dates align with others
    # However, there are a couple rules we can use:
    # - Accounts do not exist before their first transaction (that's an assumption)
    # - Between 2 transactions, there is no change in holdings
    #   This means we can take those holdings until the next transaction
    # - There are more share price than transaction, so we should loop on transactions first
    def calculate_accounts(self, accounts):
        if not self.start_date or not self.end_date or not accounts:
            return
        # TODO: determine how to handle NoPriceException - display nothing?
        # Evaluate the value from the start date until the end date
        for account_id in accounts:
            account = self.all_accounts[account_id]
            if not account.holdings:
                continue
            account_holdings = account.holdings.copy()

            if account_id not in self.accounts_raw_values:
                self.accounts_raw_values[account_id] = {}

            # Find missing ranges - improves performance
            ranges_missing = self.find_missing_date_ranges(
                self.accounts_raw_values, account_id, account.start_date
            )
            for range_missing in ranges_missing:
                new_raw_values = {}

                # Get holdings at start of range
                holdings_at_start = account_holdings[
                    max([d for d in account_holdings.keys() if d <= range_missing[0]])
                ]
                account_holdings[range_missing[0]] = {
                    "cash": holdings_at_start["cash"],
                    "shares": holdings_at_start["shares"].copy(),
                }

                for transaction_date in account_holdings.keys():
                    # Outside of requested range
                    if (
                        transaction_date < range_missing[0]
                        or transaction_date > range_missing[1]
                    ):
                        continue

                    # Get next transaction, because holdings are stable until then
                    # range_missing[1] is here to guarantee there is a value + to limit the range of transactions
                    next_transaction_date = min(
                        [x for x in account_holdings.keys() if x > transaction_date]
                        + [range_missing[1]]
                    )

                    holdings = account_holdings[transaction_date]
                    new_raw_values[transaction_date] = holdings["cash"]
                    for share_id in holdings["shares"]:
                        # Get values from the DB
                        share_values = self.get_share_value_in_range(
                            share_id,
                            transaction_date,
                            next_transaction_date,
                            account.base_currency,
                        )

                        # Add all dates of this share to the list
                        previous_share_value = 0
                        for share_value_date in share_values:
                            # If date doesn't exist, take previous one and remove this share's value
                            if not share_value_date in new_raw_values:
                                previous_value_date = max(
                                    d for d in new_raw_values if d < share_value_date
                                )
                                new_raw_values[share_value_date] = (
                                    new_raw_values[previous_value_date]
                                    - previous_share_value
                                )
                            # Add the share value as of share_value_date
                            previous_share_value = (
                                holdings["shares"][share_id]
                                * share_values[share_value_date]
                            )
                            new_raw_values[share_value_date] += previous_share_value

                        # Add dates from other shares (they're not in account_holdings)
                        missing_dates = [
                            d
                            for d in new_raw_values
                            if d not in share_values
                            and d not in account_holdings
                            and d > transaction_date
                            and d < next_transaction_date
                        ]
                        for missing_date in missing_dates:
                            share_value = self.get_share_value_as_of(
                                share_id, missing_date, account.base_currency
                            )
                            new_raw_values[missing_date] += (
                                holdings["shares"][share_id] * share_value
                            )

                self.accounts_raw_values[account_id] |= new_raw_values

    def plot_graph(self):
        self.clear_plots()
        for share_id in self.selected_shares:
            # Convert values
            x = self.convert_raw_to_graph("share", share_id)

            # Prepare legend and plot
            share = self.all_shares[share_id]
            share_label = share.name + " (" + share.base_currency.name + ")"
            self.plots["share_" + str(share_id)] = self.plot(
                x=list(self.shares_graph_values[share_id].keys()),
                y=list(self.shares_graph_values[share_id].values()),
                name=share_label,
            )

            self.set_axis_range()

        for account_id in self.selected_accounts:
            # Convert values
            self.convert_raw_to_graph("account", account_id)

            # Prepare legend and plot
            account = self.all_accounts[account_id]
            account_label = account.name + " (" + account.base_currency.name + ")"
            self.plots["account_" + str(account_id)] = self.plot(
                x=list(self.accounts_graph_values[account_id].keys()),
                y=list(self.accounts_graph_values[account_id].values()),
                name=account_label,
            )

            self.set_axis_range()

    def convert_raw_to_graph(self, element_type, element_id):
        if element_type == "share":
            raw, converted = self.shares_raw_values, self.shares_graph_values
        else:
            raw, converted = self.accounts_raw_values, self.accounts_graph_values
        # pyqtgraph accepts only timestamps for date axis
        converted[element_id] = {
            datetime.datetime(d.year, d.month, d.day).timestamp(): raw[element_id][d]
            for d in sorted(raw[element_id])
            if d >= self.start_date and d <= self.end_date
        }

    def clear_plots(self):
        for plot in self.plots:
            if plot == "legend":
                continue

            self.removeItem(self.plots[plot])
            self.plots[plot].clear()
        self.plots = {"legend": self.plots["legend"]}

    def set_axis_range(self):
        self.enableAutoRange(axis="y")

        if (
            "min" in self.graph_types[self.graph_type]
            and "max" in self.graph_types[self.graph_type]
        ):
            ymin = self.graph_types[self.graph_type]["min"]
            ymax = self.graph_types[self.graph_type]["max"]
        elif "min" in self.graph_types[self.graph_type]:
            ymin = self.graph_types[self.graph_type]["min"]
            ymax = self.getAxis("left").range[1]
        elif "max" in self.graph_types[self.graph_type]:
            ymin = self.getAxis("left").range[0]
            ymax = self.graph_types[self.graph_type]["max"]
        self.setYRange(ymin, ymax, padding=0)

    # First date is the "start of the world" so nothing can be before
    def find_missing_date_ranges(self, raw_values, element_id, first_date=None):
        ranges_missing = []
        if not first_date:
            first_date = datetime.date(1, 1, 1)
        elif first_date > self.end_date:
            return []

        start = max(self.start_date, first_date)
        if raw_values and element_id in raw_values and raw_values[element_id]:
            existing_dates = list(raw_values[element_id].keys())
            if min(existing_dates) > start:
                ranges_missing.append((start, min(existing_dates + [self.end_date])))

            if max(existing_dates) < self.end_date:
                ranges_missing.append(
                    (max(existing_dates + [self.start_date]), self.end_date)
                )
        else:
            ranges_missing.append((start, self.end_date))

        return ranges_missing

    def get_share_value_as_of(self, share_id, start_date, currency):
        # TODO: Take into account foreign exchange
        if share_id not in self.shares_raw_values:
            self.calculate_shares([share_id])
        # If no value known at all, we can't proceed
        if share_id not in self.shares_raw_values:
            raise NoPriceException("No value found", share_id)
        share_values = [d for d in self.shares_raw_values[share_id] if d <= start_date]
        # If no value known before the start, we can't proceed
        if not share_values:
            raise NoPriceException("No value found", share_id)

        return self.shares_raw_values[share_id][max(share_values)]

    def get_share_value_in_range(self, share_id, start_date, end_date, currency):
        # TODO: Take into account foreign exchange
        if share_id not in self.shares_raw_values:
            self.calculate_shares([share_id])
        # If no value known at all, we can't proceed
        if share_id not in self.shares_raw_values:
            raise NoPriceException("No value found", share_id)

        first_date = [d for d in self.shares_raw_values[share_id] if d <= start_date]
        if not first_date:
            raise NoPriceException("No value found", share_id)
        share_values = {start_date: self.shares_raw_values[share_id][max(first_date)]}
        share_values |= {
            d: self.shares_raw_values[share_id][d]
            for d in self.shares_raw_values[share_id]
            if d > start_date and d < end_date
        }

        return share_values


class GraphsController:
    name = "Graphs"
    display_hidden_accounts = False
    display_disabled_accounts = False
    display_hidden_shares = False

    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.database = parent_window.database

    def get_toolbar_button(self):
        button = QtWidgets.QAction(
            QtGui.QIcon("assets/images/graphs.png"), _("Graphs"), self.parent_window
        )
        button.setStatusTip(_("Display graphs"))
        button.triggered.connect(lambda: self.parent_window.display_tab(self.name))
        return button

    def get_display_widget(self):
        self.display_widget = QtWidgets.QWidget()
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
        self.left_column = QtWidgets.QWidget()
        self.left_column.layout = QtWidgets.QVBoxLayout()
        self.left_column.setLayout(self.left_column.layout)

        self.accounts_tree = AccountsSharesTree(self)
        self.left_column.layout.addWidget(self.accounts_tree)

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

        self.shares_tree = SharesTree(self)
        self.left_column.layout.addWidget(self.shares_tree)

        self.checkbox_hidden_shares = QtWidgets.QCheckBox(_("Display hidden shares?"))
        self.checkbox_hidden_shares.stateChanged.connect(
            self.on_click_disabled_accounts
        )
        self.left_column.layout.addWidget(self.checkbox_hidden_shares)

    def render_right_column(self):
        self.right_column = QtWidgets.QWidget()
        self.right_column.layout = QtWidgets.QGridLayout()
        self.right_column.setLayout(self.right_column.layout)

        self.period_label = QtWidgets.QLabel(_("Period"))
        self.right_column.layout.addWidget(self.period_label, 0, 0)

        self.start_date = QtWidgets.QDateEdit()
        self.start_date.dateChanged.connect(self.on_change_dates)
        self.right_column.layout.addWidget(self.start_date, 0, 1)

        self.end_date = QtWidgets.QDateEdit()
        self.end_date.dateChanged.connect(self.on_change_dates)
        self.right_column.layout.addWidget(self.end_date, 0, 2)

        self.graph = GraphsArea(self)
        self.right_column.layout.addWidget(self.graph, 1, 0, 1, 3)

        delta = datetime.timedelta(6 * 30)
        self.start_date.setDate(datetime.date.today() - delta)
        self.end_date.setDate(datetime.date.today())

    def reload_data(self):
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

    def on_click_hidden_accounts(self):
        self.display_hidden_accounts = self.checkbox_hidden_accounts.isChecked()
        self.reload_data()
        self.checkbox_hidden_accounts.clearFocus()

    def on_click_disabled_accounts(self):
        self.display_disabled_accounts = self.checkbox_disabled_accounts.isChecked()
        self.reload_data()
        self.checkbox_disabled_accounts.clearFocus()

    def on_change_dates(self):
        start_date = datetime.date.fromisoformat(
            self.start_date.date().toString(Qt.ISODate)
        )
        end_date = datetime.date.fromisoformat(
            self.end_date.date().toString(Qt.ISODate)
        )
        self.graph.set_dates(start_date, end_date)

    def on_change_account_selection(self, selected_accounts):
        self.graph.set_accounts(selected_accounts)

    def on_change_share_selection(self, selected_shares):
        self.graph.set_shares(selected_shares)
