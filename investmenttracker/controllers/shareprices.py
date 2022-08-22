import gettext
import datetime

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
import sqlalchemy.exc

from .widgets.sharecombobox import ShareComboBox
from .widgets.delegates import DateDelegate, ShareDelegate
from models.base import ValidationException, format_number
from models.shareprice import SharePrice as SharePriceDatabaseModel

_ = gettext.gettext


class SharePricesTableModel(QtCore.QAbstractTableModel):
    # Will load values 20 by 20
    row_batch_count = 20

    def __init__(self, database, columns):
        super().__init__()
        self.columns = columns
        self.database = database
        self.base_query = self.database.share_price_query()
        self.share_prices = []
        self.share = None
        self.date = None

    def columnCount(self, index):
        return len(self.columns)

    def rowCount(self, index):
        return len(self.share_prices) + 1

    def canFetchMore(self, index):
        return len(self.share_prices) < self.count_values

    def fetchMore(self, index):
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
        if index.column() in (1, 6):
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def headerData(self, column, orientation, role):
        if role != Qt.DisplayRole:
            return QtCore.QVariant()

        if orientation == Qt.Horizontal:
            return QtCore.QVariant(_(self.columns[column]["name"]))
        return QtCore.QVariant()

    # Value -1 resets the filters
    def set_filters(self, share=None, date=None):
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
        if index.column() == 6:
            self.on_click_delete_button(index)

    def on_click_delete_button(self, index):
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


class SharePricesTableView(QtWidgets.QTableView):
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
        self.model.set_filters(share, date)
        self.model.layoutChanged.emit()
        self.viewport().update()

    def resizeEvent(self, event):
        QtWidgets.QMainWindow.resizeEvent(self, event)
        self.set_column_sizes(event)

    def set_column_sizes(self, event):
        grid_width = (
            self.width() - sum([x["size"] for x in self.columns if x["size"] > 1]) - 10
        )
        for column, field in enumerate(self.columns):
            if field["size"] == 0:
                self.hideColumn(column)
            elif field["size"] < 1:
                self.setColumnWidth(column, int(grid_width * field["size"]))
            else:
                self.setColumnWidth(column, field["size"])

    def on_table_clicked(self, index):
        self.model.on_table_clicked(index)


class SharePricesController:
    name = "Share Prices"
    share_id = 0
    date = datetime.datetime.now()

    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.database = parent_window.database

    def get_toolbar_button(self):
        button = QtWidgets.QAction(
            QtGui.QIcon("assets/images/money.png"),
            _("Share Prices"),
            self.parent_window,
        )
        button.setStatusTip(_("Displays share prices"))
        button.triggered.connect(lambda: self.parent_window.display_tab(self.name))
        return button

    def get_display_widget(self):
        self.display_widget = QtWidgets.QWidget()
        self.display_widget.layout = QtWidgets.QVBoxLayout()
        self.display_widget.setLayout(self.display_widget.layout)

        # Create the group of fields at the top
        form_group = QtWidgets.QGroupBox("")
        self.form_layout = QtWidgets.QFormLayout()
        form_group.setLayout(self.form_layout)
        self.display_widget.layout.addWidget(form_group)

        # Add Share field
        self.field_share = ShareComboBox(self.database, include_choice_all=True)
        self.form_layout.addRow(QtWidgets.QLabel(_("Share")), self.field_share)
        self.field_share.currentIndexChanged.connect(self.on_select_share)

        # Add Date field
        self.field_date = QtWidgets.QDateEdit()
        self.form_layout.addRow(QtWidgets.QLabel("Date"), self.field_date)
        default_date = QtCore.QDate.currentDate().addMonths(-1)
        self.field_date.setDate(default_date)
        width = self.field_date.sizeHint().width()
        self.field_date.dateChanged.connect(self.on_select_date)
        self.field_date.setMinimumWidth(width * 2)

        # Display table
        self.table = SharePricesTableView(self)
        self.table.set_filters(date=default_date)
        self.display_widget.layout.addWidget(self.table)

        self.parent_window.setCentralWidget(self.display_widget)

        return self.display_widget

    def on_select_share(self, index):
        share_id = self.field_share.itemData(index)
        self.table.set_filters(share=share_id)

    def on_select_date(self, date):
        self.table.set_filters(date=date)
