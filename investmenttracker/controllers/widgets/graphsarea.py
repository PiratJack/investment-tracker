"""Displays a graph for analysis of performance

Classes
----------
GraphsArea
    The graph displaying the evolution of share & account price over time
"""

import logging
import gettext
import datetime

import pyqtgraph

from models.base import NoPriceException, ValidationException, format_number
from controllers.widgets import percentageaxisitem

_ = gettext.gettext
logger = logging.getLogger(__name__)


class GraphsArea(pyqtgraph.PlotWidget):
    """The graph displaying the evolution of share & account price over time

    Attributes
    ----------

    graph_types : dict
        The different graph formats
    graph_type : str
        The selected graph format
    display_markers : bool
        Whether to display the markers on the graph

    all_accounts : list of models.account.Account
        All accounts from the database
    all_shares : list of models.share.Share
        All shares from the database
    selected_accounts : list of int
        List of selected account IDs
    selected_shares : list of int
        List of selected share IDs

    accounts_holdings : dict
        The shares & cash held in an account over time (at key dates)

    shares_raw_values : dict
        The share values calculated. Converted to shares_graph_values for display
    accounts_raw_values : dict
        The account values calculated. Converted to accounts_graph_values for display
    shares_graph_values : dict
        The share values to display in the graph
    accounts_graph_values : dict
        The account values to display in the graph

    start_date : datetime.date
        The first date to display in the graph
    end_date : datetime.date
        The last date to display in the graph
    baseline_date : datetime.date
        Date used as baseline for precentage-based graph

    color_set : list
        A list of colors to use in the graph
    color_set_split : list
        A list of colors to use in the graph (for split mode)

    plots : dict of pyqtgraph.Plot
        The different elements plotted on the graph
    markers : list of pyqtgraph.TextItem
        The markers displayed on the graph

    parent_controller : SharesController
        The controller in which this class is displayed
    database : models.database.Database
        A reference to the application database


    Methods
    -------
    __init__ (parent_controller)
        Stores provided parameters & sets up the calculation variables

    set_accounts (selected_accounts)
        Defines which accounts to display & triggers reload
    set_shares (selected_shares)
        Defines which shares to display & triggers reload
    set_dates (start_date, end_date)
        Defines the start & end date for the graph calculation & triggers reload
    set_baseline (enabled, baseline_date)
        Defines the baseline date for the graph calculation & triggers reload
    set_account_split (enabled=-1)
        Recalculates value for 'split' graph (if enabled)
    set_markers_visible (visible)
        Displays or hides markers

    calculate_shares (shares)
        Calculates the raw values for a list of shares
    calculate_accounts (accounts)
        Calculates the raw values for a list of accounts

    plot_graph
        Plots all shares & accounts in the graph
    add_markers
        Adds the markers on the graph
    convert_raw_to_graph (element_type, element_id)
        Converts raw values to graph-usable values
    clear_plots (element_type, element_id)
        Clears all plots
    set_axis_range
        Defines the displayed range of both axis

    find_missing_date_ranges (raw_values, element_id, first_date=None)
        Given a share or account, finds which dates are missing from calculation

    get_share_value_as_of (share_id, start_date, currency)
        Returns the price of a share on a given date and in a given currency
    get_share_value_in_range (share_id, start_date, end_date, currency)
        Returns the prices of a share on a given date range and in a given currency

    add_error (exception)
        Adds an error for display (calls parent controller's method)
    """

    graph_types = {
        "value": {
            "min": 0,
        },
        "split": {
            "min": 0,
            "max": 1.1,
        },
        "baseline": {
            "min": 0,
        },
        "baseline_net": {
            "min": 0,
        },
    }
    graph_type = "value"
    display_markers = True

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
    # One date element per transaction or price date
    # Goal: store values on correct dates
    accounts_holdings = {}

    shares_raw_values = {}
    accounts_raw_values = {}

    shares_graph_values = {}
    accounts_graph_values = {}

    start_date = None
    end_date = None

    baseline_date = None

    color_set = [
        (166, 206, 227),
        (31, 120, 180),
        (178, 223, 138),
        (51, 160, 44),
        (251, 154, 153),
        (227, 26, 28),
        (253, 191, 111),
        (255, 127, 0),
    ]

    color_set_split = [
        (166, 206, 227, 150),
        (31, 120, 180, 150),
        (178, 223, 138, 150),
        (51, 160, 44, 150),
        (251, 154, 153, 150),
        (227, 26, 28, 150),
        (253, 191, 111, 150),
        (255, 127, 0, 150),
    ]

    plots = {}
    markers = []

    def __init__(self, parent_controller):
        """Stores provided parameters & sets up the calculation variables

        Parameters
        ----------
        parent_controller : QtWidgets.QMainWindow
            The main window displaying this widget
        """
        logger.debug("GraphsArea.__init__")
        super().__init__()
        self.setAxisItems({"bottom": pyqtgraph.DateAxisItem()})
        self.setAxisItems({"left": percentageaxisitem.PercentageAxisItem("left")})
        self.parent_controller = parent_controller
        self.database = parent_controller.database

        self.setMouseEnabled(x=True, y=False)
        self.enableAutoRange(axis="x")
        self.showGrid(x=True, y=True)

        self.plots["legend"] = self.addLegend()

    def reload_data(self):
        logger.debug("GraphsArea.reload_data")
        self.all_accounts = {a.id: a for a in self.database.accounts_get(True, True)}
        self.accounts_graph_values = {a: {} for a in self.all_accounts}
        self.all_shares = {s.id: s for s in self.database.shares_get(True)}
        self.shares_graph_values = {s: {} for s in self.all_shares}

        self.accounts_holdings = {}
        self.shares_raw_values = {}
        self.accounts_raw_values = {}

    def set_accounts(self, selected_accounts=None):
        """Defines which accounts to display & triggers reload

        Parameters
        ----------
        selected_accounts : list of int
            List of selected account IDs
        """
        logger.info(f"GraphsArea.set_accounts {selected_accounts}")
        self.selected_accounts = selected_accounts if selected_accounts else []
        if selected_accounts:
            self.calculate_accounts(selected_accounts)
        try:
            self.set_account_split()
        except (UserWarning, NoPriceException) as exception:
            self.add_error(exception)
        # Split graphs are rendered in self.set_account_split already
        if not self.graph_type == "split":
            self.plot_graph()

    def set_shares(self, selected_shares=None):
        """Defines which shares to display & triggers reload

        Parameters
        ----------
        selected_shares : list of int
            List of selected share IDs
        """
        logger.info(f"GraphsArea.set_shares {selected_shares}")
        self.selected_shares = selected_shares if selected_shares else []
        if selected_shares:
            self.calculate_shares(selected_shares)
        if not self.graph_type == "split":
            self.plot_graph()

    def set_dates(self, start_date, end_date):
        """Defines the start & end date for the graph calculation & triggers reload

        Parameters
        ----------
        start_date : datetime.date
            The first date to display in the graph
        end_date : datetime.date
            The last date to display in the graph
        """
        logger.info(f"GraphsArea.set_dates {start_date} to {end_date}")
        if start_date and end_date and start_date > end_date:
            exception = ValidationException(
                _("Start date must be before end date"), None, None, None
            )
            self.add_error(exception)
            return
        self.start_date = start_date
        self.end_date = end_date

        if self.graph_type == "split":
            try:
                self.set_account_split()
            except (UserWarning, NoPriceException) as exception:
                self.add_error(exception)
        else:
            self.calculate_accounts(self.selected_accounts)
            self.calculate_shares(self.selected_shares)
            self.plot_graph()

    def set_baseline(self, enabled, baseline_date, baseline_net):
        """Defines the baseline date for the graph calculation & triggers reload

        Parameters
        ----------
        enabled : bool
            Whether the percentage-based graph is enabled
        baseline_date : datetime.date
            Date used as baseline for precentage-based graph
        baseline_net : bool
            Whether the baseline changes after each entry/exit out of the account
        """
        logger.info(
            f"GraphsArea.set_baseline {enabled} at {baseline_date} - Net? {baseline_net}"
        )
        self.calculate_accounts(self.selected_accounts)
        self.calculate_shares(self.selected_shares)
        if enabled:
            self.baseline_date = baseline_date
            self.graph_type = "baseline"
            if baseline_net:
                self.graph_type = "baseline_net"
        else:
            self.baseline_date = None
            self.graph_type = "value"
        # The actual conversion is done by convert_raw_to_graph (called by plot_graph)

        self.plot_graph()

    def set_account_split(self, enabled=-1):
        """Recalculates value for 'split' graph (if enabled)

        Parameters
        ----------
        enabled : bool
            Whether the graph should display the composition of an account
        """
        logger.info(f"GraphsArea.set_account_split {enabled}")
        if enabled != -1:
            self.graph_type = "split" if enabled else "value"

        if not self.graph_type == "split":
            return
        if len(self.selected_accounts) == 0:
            self.clear_plots()
            return
        if len(self.selected_accounts) > 1:
            raise UserWarning("Only 1 account can be displayed in this mode")

        # Get raw calculations for everything we need
        self.calculate_accounts(self.selected_accounts)
        account_id = self.selected_accounts[0]
        account = self.all_accounts[account_id]
        if account_id not in self.accounts_holdings:
            # Error is already displayed by self.calculate_accounts
            return
        holdings = self.accounts_holdings[account_id]

        # Convert values to percentages
        key_dates = [d for d in holdings if self.start_date <= d <= self.end_date]
        self.shares_graph_values = {}
        self.accounts_graph_values[account_id] = {d: 1 for d in key_dates}
        all_shares = set()
        for date in holdings:
            all_shares.update(holdings[date]["shares"])

        if not all_shares:
            self.add_error(UserWarning(f"Account {account.name} has no holding"))
            return

        for share_id in sorted(all_shares):
            if share_id not in self.shares_graph_values:
                self.shares_graph_values[share_id] = {}
            self.shares_graph_values[share_id] = {
                date: (
                    holdings[date]["shares"].get(share_id, 0)
                    * holdings[date]["share_value"][share_id]
                    / self.accounts_raw_values[account_id][date]
                    + max(
                        [0]
                        + [
                            self.shares_graph_values[s].get(date, 0)
                            for s in self.shares_graph_values
                        ]
                    )
                )
                for date in key_dates
            }

        self.selected_shares = list(self.shares_graph_values.keys()) + [
            account.base_currency.id
        ]
        self.calculate_shares([account.base_currency.id])

        # This should yield 1 for each date (because it contains the sum of everything)
        self.shares_graph_values[account.base_currency.id] = {
            date: (
                holdings[date]["cash"] / self.accounts_raw_values[account_id][date]
                if "cash" in holdings[date]
                else 0
            )
            + (self.shares_graph_values[share_id][date] if share_id else 0)
            # share_id contains the last share from the loop, thus everything except cash
            # This is because the % of a given share is actually the percentage of that share in the total + all the "previous" shares' %
            # Otherwise, it's not a stacked area chart, but each share would have its percentage
            for date in key_dates
        }

        self.plot_graph()

    def set_markers_visible(self, visible):
        """Displays or hides markers

        Parameters
        ----------
        visible : bool
            Whether to display markers
        """
        logger.info(f"GraphsArea.set_markers_visible {visible}")
        self.display_markers = visible

        if visible:
            for share_id in reversed(self.selected_shares):
                self.add_markers(self.shares_graph_values[share_id])

            for account_id in self.selected_accounts:
                self.add_markers(self.accounts_graph_values[account_id])
        else:
            for marker in self.markers:
                self.removeItem(marker)
            self.markers = []

    def calculate_shares(self, shares):
        """Calculates the raw values for a list of shares

        Parameters
        ----------
        shares : list of int
            The list of shares to calculate
        """
        logger.info(f"GraphsArea.calculate_shares {shares}")
        if not shares:
            return

        for share_id in shares:
            share = self.all_shares[share_id]
            if share_id not in self.shares_raw_values:
                self.shares_raw_values[share_id] = {p.date: p for p in share.prices}
            logger.debug(
                f"GraphsArea.calculate_shares - {len(self.shares_raw_values[share_id])} values for {share.name}"
            )

    def calculate_accounts(self, accounts):
        """Calculates the raw values for a list of accounts

        The goal of this function is to calculate the account's value for the graph
        There are several challenges:
        - We don't want to calculate outside of what's needed (to improve performance)
        - At each transaction, the holdings (= of shares & cash) changes
        - Each share held may change value multiple times
        - We can't assume any of those dates align with others
        However, there are a couple rules we can use:
        - Accounts do not exist before their first transaction (they have nothing before)
        - Between 2 transactions, there is no change in holdings
          This means we can take those holdings until the next transaction
        - There are more share price than transaction, so we loop on transactions first

        Parameters
        ----------
        accounts : list of int
            The list of shares to calculate
        """
        logger.info(f"GraphsArea.calculate_accounts {accounts}")
        if not accounts:
            return
        # Evaluate the value from the start date until the end date
        for account_id in accounts:
            try:
                account = self.all_accounts[account_id]
                if not account.holdings:
                    self.add_error(
                        UserWarning(f"Account {account.name} has no holding")
                    )
                    continue
                if account_id not in self.accounts_raw_values:
                    self.accounts_holdings[account_id] = {}
                    self.accounts_raw_values[account_id] = {}
                else:
                    continue

                # Get share prices when they're held in the account
                # Also, find all key dates when the account value changes
                all_shares = set(
                    t.share
                    for t in account.transactions
                    if t.type.value["impact_asset"]
                )
                key_dates = set(account.holdings.keys())
                share_prices = {}
                for share in all_shares:
                    # Get dates in which share is held (= and in which prices should be known)
                    date_acquired = min(
                        t.date for t in account.transactions if t.share == share
                    )
                    date_sold = max(
                        t.date for t in account.transactions if t.share == share
                    )
                    # If share is still held today, date_sold should be None
                    if share.id in account.shares and account.shares[share.id] != 0:
                        date_sold = None

                    # Get prices when share is held
                    prices = {
                        p.date: p.price
                        for p in share.prices
                        if p.date >= date_acquired
                        and (date_sold is None or p.date <= date_sold)
                        and p.currency == account.base_currency
                    }
                    if not share.prices:
                        if date_sold is not None:
                            raise NoPriceException(
                                _(
                                    "No price when share is held: from {date_acquired}"
                                ).format(date_acquired=date_acquired),
                                share,
                            )
                        else:
                            raise NoPriceException(
                                _(
                                    "No price when share is held: {date_acquired} to {date_sold}"
                                ).format(
                                    date_acquired=date_acquired, date_sold=date_sold
                                ),
                                share,
                            )

                    # If share not valued upon acquisition, find the most recent price
                    if date_acquired not in prices:
                        dates_before = [
                            p.date for p in share.prices if p.date <= date_acquired
                        ]
                        if not dates_before:
                            raise NoPriceException(
                                _(
                                    "No price upon share acquisition on {date_acquired}"
                                ).format(date_acquired=date_acquired),
                                share,
                            )
                        most_recent_date = max(dates_before)
                        prices[date_acquired] = [
                            p.price for p in share.prices if p.date == most_recent_date
                        ][0]
                    share_prices[share.id] = prices
                    key_dates.update(prices.keys())

                # For each key date, evaluate the values
                holdings_now = account.holdings[account.start_date]
                holdings_now["share_value"] = {}
                for date in sorted(key_dates):
                    # Copy previous value, to avoid overwriting it
                    holdings_now = holdings_now.copy()
                    for i in holdings_now:
                        if not isinstance(holdings_now[i], float):
                            holdings_now[i] = holdings_now[i].copy()
                    # If there's a transaction on that date, update cash & shares held
                    if date in account.holdings:
                        holdings_now["cash"] = account.holdings[date]["cash"]
                        holdings_now["shares"] = account.holdings[date]["shares"].copy()

                    # Determine value of the account : cash + shares
                    self.accounts_raw_values[account_id][date] = holdings_now["cash"]
                    for share_id in holdings_now["shares"]:
                        # Update value if there is a new share price. Otherwise, the previous value is used thanks to the logic above
                        if date in share_prices[share_id]:
                            holdings_now["share_value"][share_id] = share_prices[
                                share_id
                            ][date]
                        self.accounts_raw_values[account_id][date] += (
                            holdings_now["shares"][share_id]
                            * holdings_now["share_value"][share_id]
                        )
                    self.accounts_holdings[account_id][date] = holdings_now

                # Start date of graph: use most recent value
                if self.start_date not in self.accounts_raw_values[account_id]:
                    found = [
                        date
                        for date in self.accounts_raw_values[account_id]
                        if date < self.start_date
                    ]
                    if found:
                        self.accounts_raw_values[account_id][self.start_date] = (
                            self.accounts_raw_values[account_id][max(found)]
                        )
            except NoPriceException as exception:
                exception.account = self.all_accounts[account_id]
                self.add_error(exception)

    def plot_graph(self):
        """Calculates the raw values for a list of accounts"""
        logger.debug("GraphsArea.plot_graph")
        self.clear_plots()
        color_set = (
            self.color_set_split if self.graph_type == "split" else self.color_set
        )
        # Need to plot from the top to bottom (for splits), otherwise areas get overwritten
        for share_id in reversed(self.selected_shares):
            # Convert values
            self.convert_raw_to_graph("share", share_id)

            # Prepare legend and plot
            share = self.all_shares[share_id]
            share_color = color_set[share_id % len(color_set)]

            # For splits, the first share to display will fill via "fillLevel" and "brush"
            brush = share_color if self.graph_type == "split" else None

            x_values = list(
                map(
                    lambda d: datetime.datetime(d.year, d.month, d.day).timestamp(),
                    self.shares_graph_values[share_id].keys(),
                )
            )
            y_values = list(self.shares_graph_values[share_id].values())
            self.plots["share_" + str(share_id)] = self.plot(
                x=x_values,
                y=y_values,
                name=share.graph_label,
                pen=share_color,
                fillLevel=0,
                brush=brush,
            )

            # Add markers
            self.add_markers(self.shares_graph_values[share_id])

        for account_id in self.selected_accounts:
            # Convert values
            self.convert_raw_to_graph("account", account_id)

            # Prepare legend and plot
            account = self.all_accounts[account_id]
            x_values = list(
                map(
                    lambda d: datetime.datetime(d.year, d.month, d.day).timestamp(),
                    self.accounts_graph_values[account_id].keys(),
                )
            )
            y_values = list(self.accounts_graph_values[account_id].values())
            self.plots["account_" + str(account_id)] = self.plot(
                x=x_values,
                y=y_values,
                name=account.graph_label,
                pen=pyqtgraph.mkPen(
                    width=2, color=color_set[account_id % len(color_set)]
                ),
            )

            # Add markers
            self.add_markers(self.accounts_graph_values[account_id])

        self.set_axis_range()

    def add_markers(self, values):
        """Adds the markers on the graph

        To avoid overload, it'll display at most 30 values

        Parameters
        ----------
        values : dict of format {x:y}
            All the graph values
        """
        logger.info(f"GraphsArea.add_markers: {len(values)} items")
        if not self.display_markers:
            return

        x_values = list(
            map(
                lambda d: datetime.datetime(d.year, d.month, d.day).timestamp(),
                values.keys(),
            )
        )
        y_values = list(values.values())
        markers = list(zip(x_values, y_values))
        markers = markers[:: len(markers) // 20] if len(markers) > 30 else markers
        for marker_x, marker_y in markers:
            if self.graph_type == "split":
                # It would always be 100%
                break
            if self.graph_type == "value":
                marker = pyqtgraph.TextItem(format_number(marker_y))
            else:
                marker = pyqtgraph.TextItem(f"{marker_y:.1%}")
            self.addItem(marker)
            marker.setPos(marker_x, marker_y)
            self.markers.append(marker)

    def convert_raw_to_graph(self, element_type, element_id):
        """Converts raw values to graph-usable values

        The goal is to calculate self.*_graph_values
        For split-based graph, this conversion is already done

        Parameters
        ----------
        element_type : str (either 'share' or 'account')
            The element type (share or account) to calculate
        element_id : int
            The ID of the element to calculate
        """
        logger.info(f"GraphsArea.convert_raw_to_graph {element_type} {element_id}")
        # in "split" mode, the graph values are already calculated
        # Therefore, only the date filtering is needed
        if element_type == "share":
            if self.graph_type == "split":
                raw, converted = self.shares_graph_values, self.shares_graph_values
            else:
                raw, converted = self.shares_raw_values, self.shares_graph_values
        else:
            if self.graph_type == "split":
                raw, converted = self.accounts_graph_values, self.accounts_graph_values
            else:
                raw, converted = (
                    self.accounts_raw_values.copy(),
                    self.accounts_graph_values,
                )

        if element_id not in raw:
            return

        baseline_value = 1
        if self.graph_type == "baseline" or self.graph_type == "baseline_net":
            # If there is a date before the baseline, take it. Otherwise, take the first available.
            dates_before = [d for d in raw[element_id] if d <= self.baseline_date]
            if dates_before:
                real_baseline_date = max(dates_before)
            elif raw[element_id]:
                real_baseline_date = min(raw[element_id].keys())
            else:
                raise ValueError(f"No value to graph for {element_type} {element_id}")
            baseline_value = raw[element_id][real_baseline_date]
            baseline_value = (
                baseline_value
                if isinstance(baseline_value, (float, int))
                else baseline_value.price
            )

            # For "Net baseline" graphs, we need to "zero out" unwanted transactions
            if self.graph_type == "baseline_net" and element_type == "account":
                start_date = min([d for d in raw[element_id]])
                end_date = max([d for d in raw[element_id]])
                # Find all transactions to exclude in date range
                transactions = self.all_accounts[element_id].transactions
                transactions = [
                    t
                    for t in transactions
                    if t.date >= start_date and t.date <= end_date
                    if t.type.value["exclude_from_net_baseline"]
                ]
                # Transactions before the baseline should be reversed and impact what happened before them
                # Otherwise, the baseline_value will move
                raw[element_id] = {
                    graph_date: raw[element_id][graph_date]
                    + sum(
                        [
                            transaction.cash_total
                            + transaction.asset_total * transaction.unit_price
                            for transaction in transactions
                            if transaction.date < real_baseline_date
                            and graph_date <= transaction.date
                        ]
                    )
                    - sum(
                        [
                            transaction.cash_total
                            + transaction.asset_total * transaction.unit_price
                            for transaction in transactions
                            if transaction.date > real_baseline_date
                            and graph_date >= transaction.date
                        ]
                    )
                    for graph_date in raw[element_id]
                }

        converted[element_id] = {
            d: (
                raw[element_id][d]
                if isinstance(raw[element_id][d], (float, int))
                else raw[element_id][d].price
            )
            / baseline_value
            for d in sorted(raw[element_id])
            if self.start_date <= d <= self.end_date
        }

    def clear_plots(self):
        """Clears all plots"""
        logger.debug("GraphsArea.clear_plots")
        for plot_id, plot in self.plots.items():
            if plot_id == "legend":
                continue
            self.removeItem(plot)
            plot.clear()
        self.plots = {"legend": self.plots["legend"]}

        for marker in self.markers:
            self.removeItem(marker)
        self.markers = []

    def set_axis_range(self):
        """Defines the displayed range of both axis"""
        logger.debug("GraphsArea.set_axis_range")
        start, end = (
            datetime.datetime(d.year, d.month, d.day).timestamp()
            for d in (self.start_date, self.end_date)
        )
        self.setXRange(start, end, padding=0)

        self.enableAutoRange(axis="y")
        self.setAutoVisible(y=True)

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

    def get_share_value_as_of(self, share_id, start_date, currency):
        """Returns the price of a share on a given date and in a given currency

        Parameters
        ----------
        share_id : int
            The ID of the share to find
        start_date : datetime.date
            The date to find
        currency : models.share.Share
            In which currency the share price should be
        """
        logger.info(
            f"GraphsArea.get_share_value_as_of {share_id} starting on {start_date} with currency {currency}"
        )
        self.calculate_shares([share_id])
        # If no value known at all, we can't proceed
        if share_id not in self.shares_raw_values:
            raise NoPriceException("No value found at all", self.all_shares[share_id])
        share_values = [
            d
            for d, price in self.shares_raw_values[share_id].items()
            if d <= start_date and price.currency == currency
        ]
        # If no value known before the start, we can't proceed
        if not share_values:
            raise NoPriceException(
                "No value found on date", self.all_shares[share_id], None, start_date
            )

        return self.shares_raw_values[share_id][max(share_values)]

    def add_error(self, exception):
        """Adds an error for display (calls parent controller's method)

        Parameters
        ----------
        exception : Exception
            The exception raised during the calculation
        """
        logger.info(f"GraphsArea.add_error {exception}")
        self.parent_controller.add_error(exception)
