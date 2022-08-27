"""Displays shares prices, with filter on share & date

Classes
----------
SharePricesTableModel
    The model for the table displaying the prices

SharePricesTableView
    The table displaying the prices

SharePricesController
    Handles user interactions and links all displayed widgets
"""
import gettext
import datetime

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
import sqlalchemy.exc

from controllers.widgets.sharecombobox import ShareComboBox
from controllers.widgets.delegates import DateDelegate, ShareDelegate
from controllers.widgets import autoresize
from models.base import ValidationException, format_number
from models.shareprice import SharePrice as SharePriceDatabaseModel

_ = gettext.gettext


class SharePricesTableModel(QtCore.QAbstractTableModel):
    """Model for display of share prices, based on user selection

    The date filter is meant as 'any price after this date'

    Attributes
    ----------
    row_batch_count : int
        The number of rows to load (as batch size)
    columns : list of dicts
        Columns to display. Each column should have a name and size key
    database : models.database.Database
        A reference to the application database
    base_query : sqlalchemy.database.session.query
        The query to use as basis for filtering
    share_prices : list of models.shareprice.SharePrice
        The list of share prices to display

    share : models.share.Share
        The share selected by the user for filtering
    date : datetime.date
        The date selected by the user for filtering

    query : sqlalchemy.database.session.query
        The query used for actual fetching (with filters applied)
    count_values : int
        The total number of share prices matching the filters

    Methods
    -------
    __init__ (database, columns)
        Sets up all data required to display the screen
    columnCount (index)
        Returns the number of columns
    rowCount (index)
        Returns the number of rows
    canFetchMore (index)
        Returns True if further data can be loaded, False otherwise
    fetchMore (index)
        Gets additional data from the database
    data (index)
        Returns which data to display (or how to display it) for the corresponding cell
    setData (index, value, role)
        Handler of user entries in the table
    flags (index)
        Returns whether items are selectable, enabled or editable
    headerData (index)
        Returns the table headers

    set_filters (index)
        Applies the filters on the list of transactions
    on_table_clicked (index)
        Handles user click (on delete button)
    on_click_delete_button (index)
        Displays a confirmation dialog for deletion of share prices
    """

    # Will load values 20 by 20
    row_batch_count = 20
    count_values = 0

    def __init__(self, database, columns):
        """Sets up all data required to display the screen

        Parameters
        ----------
        database : models.database.Database
            A reference to the application database
        columns : list of dicts
            Columns to display. Each column should have a name and size key
        """
        super().__init__()
        self.columns = columns
        self.database = database
        self.base_query = self.database.share_price_query()
        self.query = self.base_query
        self.share_prices = []
        self.share = None
        self.date = None

    def columnCount(self, index):
        """Returns the number of columns

        Parameters
        ----------
        index : QtCore.QModelIndex
            A reference to the cell to display (not used in this method)
        """
        return len(self.columns)

    def rowCount(self, index):
        """Returns the number of rows

        Parameters
        ----------
        index : QtCore.QModelIndex
            A reference to the cell to display (not used in this method)
        """
        return len(self.share_prices) + 1

    def canFetchMore(self, index):
        """Returns whether more rows can be displayed

        Parameters
        ----------
        index : QtCore.QModelIndex
            A reference to the cell to display (not used in this method)
        """
        return len(self.share_prices) < self.count_values

    def fetchMore(self, index):
        """Gets additional data from the database

        Parameters
        ----------
        index : QtCore.QModelIndex
            A reference to the cell to display (not used in this method)
        """
        # Determine what to fetch
        items_left = self.count_values - len(self.share_prices)
        items_to_fetch = min(items_left, self.row_batch_count)

        # Prepare query to load data
        new_prices = self.query.slice(
            len(self.share_prices), len(self.share_prices) + items_to_fetch
        ).all()

        # Update table
        self.beginInsertRows(
            QtCore.QModelIndex(),
            len(self.share_prices),
            len(self.share_prices) + items_to_fetch - 1,
        )
        self.share_prices += new_prices
        self.endInsertRows()

    def data(self, index, role):
        """Returns the data or formatting to display

        Parameters
        ----------
        index : QtCore.QModelIndex
            A reference to the cell to display
        role : Qt.DisplayRole
            The required role (display, decoration, ...)

        Returns
        -------
        QtCore.QVariant
            If role = Qt.DisplayRole: the data to display or "Add a share price"
            If role = Qt.DecorationRole: the images for delete action
            If role = Qt.TextAlignmentRole: the proper alignment
        """
        if not index.isValid():
            return False

        col = index.column()
        if role == Qt.DisplayRole:
            # New item row
            if index.row() == len(self.share_prices):
                if index.column() == 0:
                    return _("Add a share price")
                return QtCore.QVariant()

            price = self.share_prices[index.row()]
            return [
                price.share.name if price.share else QtCore.QVariant(),
                price.id,
                QtCore.QDate(price.date) if price.date else QtCore.QVariant(),
                format_number(price.price),
                price.currency.short_name if price.currency else QtCore.QVariant(),
                price.source,
                QtCore.QVariant(),
            ][col]

        if role == Qt.EditRole:
            # New item row
            if index.row() == len(self.share_prices):
                price = SharePriceDatabaseModel()
                self.share_prices.append(price)
                self.count_values += 1
                # This forces the correct type of value
                return [
                    0,
                    None,
                    datetime.datetime.today(),
                    0,
                    0,
                    "",
                    None,
                ][col]

            price = self.share_prices[index.row()]
            return [
                price.share_id,
                None,
                price.date,
                price.price,
                price.currency_id,
                price.source,
                None,
            ][col]

        if (
            role == Qt.DecorationRole
            and col == 6
            and index.row() != len(self.share_prices)
        ):
            return QtCore.QVariant(QtGui.QIcon("assets/images/delete.png"))
        if role == Qt.TextAlignmentRole:
            return self.columns[index.column()]["alignment"]

        return QtCore.QVariant()

    def setData(self, index, value, role):
        """Applies the data entered by the user on the corresponding share price

        If mandatory data is missing, nothing will be shared & no error displayed.

        Parameters
        ----------
        index : QModelIndex
            The position of the data to modify
        value : QVariant
            Value entered by the user
        role : ItemDataRole
            The role for the modified data (should always be Qt.QtEditRole)

        Returns
        -------
        bool
            True if the data was successfully edited"""
        col = index.column()
        if role == Qt.EditRole:
            price = self.share_prices[index.row()]

            try:
                if col == 0:
                    if value > 0:
                        price.share_id = value
                        price.share = self.database.share_get_by_id(value)
                elif col == 2:
                    price.date = value
                elif col == 3:
                    try:
                        price.price = float(value)
                    except ValueError:
                        return False
                elif col == 4:
                    if value > 0:
                        price.currency_id = value
                        price.currency = self.database.share_get_by_id(value)
                elif col == 5:
                    price.source = value

                self.database.session.add(price)
                self.database.session.commit()
                self.dataChanged.emit(index, index, [Qt.EditRole])
                return True

            except (sqlalchemy.exc.IntegrityError, ValidationException):
                self.database.session.rollback()
                return True
        return False

    def flags(self, index):
        """Returns whether items are selectable, enabled or editable

        Parameters
        ----------
        index : QtCore.QModelIndex
            A reference to the cell to display (not used in this method)

        Returns
        ----------
        Qt.ItemFlags
            Enabled & selectable for ID and button columns
            Enabled, selectable & editable for other fields
        """
        if index.column() in (1, 6):
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def headerData(self, column, orientation, role):
        """Returns the headers to display for a given column

        Parameters
        ----------
        column : int
            The column number
        orientation : Qt.Orientation
            Whether headers are horizontal or vertical
        role : Qt.DisplayRole
            The required role (display, decoration, ...)

        Returns
        -------
        QtCore.QVariant
            If role = Qt.DisplayRole and orientation == Qt.Horizontal: the header name
            Else: QtCore.QVariant
        """
        if role != Qt.DisplayRole:
            return QtCore.QVariant()

        if orientation == Qt.Horizontal:
            return QtCore.QVariant(_(self.columns[column]["name"]))
        return QtCore.QVariant()

    def set_filters(self, share=None, date=None):
        """Applies the filters on the list of share prices to display

        Parameters
        ----------
        share : models.share.Share or int
            Only prices for that share (or share ID) will be displayed.
            -1 resets the filter
        date : QtCore.QDate, datetime.datetime, str or int
            Only prices after that date will be displayed
            -1 resets the filter
        """
        self.query = self.base_query

        if share:
            self.share = share
        if share == -1:
            self.share = None

        if self.share:
            if isinstance(self.share, int):
                self.query = self.query.filter(
                    SharePriceDatabaseModel.share_id == self.share
                )
            else:
                self.query = self.query.filter(
                    SharePriceDatabaseModel.share == self.share
                )

        if date:
            # Convert to datetime.datetime object
            if isinstance(date, QtCore.QDate):
                self.date = datetime.datetime.fromisoformat(date.toString(Qt.ISODate))
            elif isinstance(date, datetime.datetime):
                self.date = date
            elif isinstance(date, str):
                self.date = datetime.datetime.fromisoformat(date)
            elif isinstance(date, int):
                self.date = datetime.datetime.fromtimestamp(date)
            else:
                self.date = None
        elif date == -1:
            self.date = None

        if self.date:
            self.query = self.query.filter(
                SharePriceDatabaseModel.date >= self.date.date()
            )

        self.count_values = self.query.count()
        self.query = self.query.order_by(SharePriceDatabaseModel.date)
        self.share_prices = self.query.all()

    def on_table_clicked(self, index):
        """User clicks on delete button => triggers the deletion

        Parameters
        ----------
        index : QtCore.QModelIndex
            A reference to the cell to display
        """
        if index.column() == 6:
            self.on_click_delete_button(index)

    def on_click_delete_button(self, index):
        """Displays a confirmation dialog for deletion of share prices

        If deletion is confirmed, reloads the data

        Parameters
        ----------
        index : QtCore.QModelIndex
            A reference to the cell to display
        """
        price = self.share_prices[index.row()]
        messagebox = QtWidgets.QMessageBox.critical(
            self.parent(),
            _("Please confirm"),
            _("Are you sure you want to delete this price?"),
            buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            defaultButton=QtWidgets.QMessageBox.No,
        )

        if messagebox == QtWidgets.QMessageBox.Yes:
            if price.id:
                self.database.delete(price)
            self.beginRemoveRows(index, index.row(), index.row())
            self.set_filters()  # Reload the data
            self.endRemoveRows()


class SharePricesTableView(QtWidgets.QTableView, autoresize.AutoResize):
    """Table for display of share prices, based on user selection

    Attributes
    ----------
    columns : list of dicts
        Columns to display. Each column should have a name and size key
    parent_controller : SharePricesController
        The controller displaying this class
    database : models.database.Database
        A reference to the application database
    model : TransactionsTableModel
        The model for interaction with the database

    transaction_details : controllers.transaction.TransactionController
        The controller for creating/editing a single transaction

    Methods
    -------
    __init__ (parent_controller)
        Sets up model & delegates for the table display
    set_filters (share=None, date=None)
        Applies the filters on the list of share prices & refreshes the display
    on_table_clicked (index)
        User click handler - delete a share price
    """

    columns = [
        {
            "name": _("Share"),
            "size": 0.3,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": _("ID"),
            "size": 0,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Date"),
            "size": 0.2,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Price"),
            "size": 0.2,
            "alignment": Qt.AlignRight,
        },
        {
            "name": _("Currency"),
            "size": 0.1,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": _("Source"),
            "size": 0.2,
            "alignment": Qt.AlignLeft,
        },
        {
            "name": _("Delete"),
            "size": 80,
            "alignment": Qt.AlignCenter,
        },
    ]

    def __init__(self, parent_controller):
        """Sets up model & delegates for the table display

        Parameters
        ----------
        parent_controller : SharePricesController
            The controller displaying this class
        """
        super().__init__()
        self.parent_controller = parent_controller
        self.database = parent_controller.database

        self.model = SharePricesTableModel(self.database, self.columns)
        self.setModel(self.model)
        self.setItemDelegateForColumn(0, ShareDelegate(self, self.database))
        self.setItemDelegateForColumn(2, DateDelegate(self))
        self.setItemDelegateForColumn(4, ShareDelegate(self, self.database))

        self.clicked.connect(self.on_table_clicked)

    def set_filters(self, share=None, date=None):
        """Applies the filters on the list of share prices & refreshes the display

        Parameters
        ----------
        share : int
            The selected share, used to filter the list of prices displayed
        date : datetime.date
            The selected date, used to filter the list of prices displayed
        """
        self.model.set_filters(share, date)
        self.model.layoutChanged.emit()
        self.viewport().update()

    def on_table_clicked(self, index):
        """User click handler - triggers the model's method

        Parameters
        ----------
        index : QtCore.QModelIndex
            A reference to the cell to display (not used in this method)
        """
        self.model.on_table_clicked(index)


class SharePricesController:
    """Controller for display & interactions on share prices list

    Attributes
    ----------
    name : str
        Name of the controller - used in display
    share_id : int
        The ID of the selected share

    parent_window : QtWidgets.QMainWindow
        The parent window
    database : models.database.Database
        A reference to the application database

    display_widget : QtWidgets.QWidget
        The main display for this controller
    form_layout : QtWidgets.QFormLayout
        The layout of the screen
    field_share : controllers.widgets.sharecombobox.ShareComboBox
        A combobox to select a share
    field_date : QtWidgets.QDateEdit
        A field to select a date (& filter the prices)
    table : SharePricesTableView
        The table displaying the share prices matching the filters

    Methods
    -------
    __init__ (parent_window)
        Returns a QtWidgets.QAction for display in the main window toolbar

    get_toolbar_button
        Returns a QtWidgets.QAction for display in the main window toolbar
    get_display_widget
        Returns the main QtWidgets.QWidget for this controller

    on_select_share
        User selects a share => filter the list of share prices
    on_select_date
        User selects a date => filter the list of share prices
    """

    name = "Share Prices"
    share_id = 0

    def __init__(self, parent_window):
        """Stores parameters & creates all UI elements

        Parameters
        ----------
        parent_window : QtWidgets.QMainWindow
            The main window displaying this controller
        """
        self.parent_window = parent_window
        self.database = parent_window.database

        self.display_widget = QtWidgets.QWidget()
        self.display_widget.layout = QtWidgets.QVBoxLayout()
        self.form_layout = QtWidgets.QFormLayout()
        self.field_share = ShareComboBox(self.database, include_choice_all=True)
        self.field_date = QtWidgets.QDateEdit()
        self.table = SharePricesTableView(self)

    def get_toolbar_button(self):
        """Returns a QtWidgets.QAction for display in the main window toolbar"""
        button = QtWidgets.QAction(
            QtGui.QIcon("assets/images/money.png"),
            _("Share Prices"),
            self.parent_window,
        )
        button.setStatusTip(_("Displays share prices"))
        button.triggered.connect(lambda: self.parent_window.display_tab(self.name))
        return button

    def get_display_widget(self):
        """Returns the main QtWidgets.QWidget for this controller"""
        self.display_widget.setLayout(self.display_widget.layout)

        # Create the group of fields at the top
        form_group = QtWidgets.QGroupBox("")
        form_group.setLayout(self.form_layout)
        self.display_widget.layout.addWidget(form_group)

        # Add Share field
        self.form_layout.addRow(QtWidgets.QLabel(_("Share")), self.field_share)
        self.field_share.currentIndexChanged.connect(self.on_select_share)

        # Add Date field
        self.form_layout.addRow(QtWidgets.QLabel("Date"), self.field_date)
        default_date = QtCore.QDate.currentDate().addMonths(-1)
        self.field_date.setDate(default_date)
        width = self.field_date.sizeHint().width()
        self.field_date.dateChanged.connect(self.on_select_date)
        self.field_date.setMinimumWidth(width * 2)

        # Display table
        self.table.set_filters(date=default_date)
        self.display_widget.layout.addWidget(self.table)

        self.parent_window.setCentralWidget(self.display_widget)

        return self.display_widget

    def on_select_share(self, index):
        """User selects a share => filter the list of share prices

        Parameters
        ----------
        index : int
            The index of the item selected in the dropdown
        """
        share_id = self.field_share.itemData(index)
        self.table.set_filters(share=share_id)

    def on_select_date(self, date):
        """User selects a date => filter the list of share prices

        Parameters
        ----------
        date : datetime.date
            The selected date
        """
        self.table.set_filters(date=date)
