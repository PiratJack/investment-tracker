import gettext
import datetime

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAction,
    QWidget,
    QTableView,
    QDateEdit,
    QVBoxLayout,
    QGroupBox,
    QFormLayout,
    QLabel,
    QMessageBox,
)
import PyQt5.QtCore
from PyQt5.QtCore import QVariant
from PyQt5.QtCore import QDate, Qt

from .widgets.sharecombobox import ShareComboBox
from models.shareprice import SharePrice as SharePriceDatabaseModel

_ = gettext.gettext


class SharePricesTableModel(PyQt5.QtCore.QAbstractTableModel):
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
        return len(self.share_prices)

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
            PyQt5.QtCore.QModelIndex(),
            len(self.share_prices),
            len(self.share_prices) + items_to_fetch - 1,
        )
        self.share_prices += new_prices
        self.endInsertRows()

    def data(self, index, role):
        col = index.column()
        price = self.share_prices[index.row()]
        if role == PyQt5.QtCore.Qt.DisplayRole:
            if col == 0:
                return price.share.name
            elif col == 1:
                return price.id
            elif col == 2:
                return price.date.strftime("%Y-%m-%d")
            elif col == 3:
                return price.price
            elif col == 4:
                return price.currency
            elif col == 5:
                return price.source

        if role == PyQt5.QtCore.Qt.EditRole:
            if col == 2:
                return price.date.strftime("%Y-%m-%d")
            elif col == 3:
                return price.price
            elif col == 4:
                return price.currency
            elif col == 5:
                return price.source

        if role == PyQt5.QtCore.Qt.DecorationRole and col == 6:
            # pixmap = QPixmap.fromImage(QImage("assets/images/delete.png"))
            # pixmap = pixmap.scaled(25, 25)
            # return QVariant(pixmap)
            return QVariant(QIcon("assets/images/delete.png"))

    def setData(self, index, value, role):
        price = self.share_prices[index.row()]
        col = index.column()
        if role == Qt.EditRole:
            try:
                if col == 2:
                    price.date = datetime.datetime.strptime(value, "%Y-%m-%d")
                elif col == 3:
                    price.price = value
                elif col == 5:
                    price.source = value

                self.database.session.add(price)
                self.database.session.commit()
                self.dataChanged.emit(index, index, [PyQt5.QtCore.Qt.EditRole])
                return True

            except:
                return False

    def flags(self, index):
        if index.column() in (0, 1, 4, 6):
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        else:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def headerData(self, column, orientation, role):
        if role != PyQt5.QtCore.Qt.DisplayRole:
            return QVariant()

        if orientation == PyQt5.QtCore.Qt.Horizontal:
            return PyQt5.QtCore.QVariant(_(self.columns[column]["name"]))
        return QVariant()

    # Value -1 resets the filters
    def set_filters(self, share=None, date=None):
        self.query = self.base_query

        if share:
            self.share = share
        if share == -1:
            self.share = None

        if self.share:
            if type(self.share) == int:
                self.query = self.query.filter(
                    SharePriceDatabaseModel.share_id == self.share
                )
            else:
                self.query = self.query.filter(
                    SharePriceDatabaseModel.share == self.share
                )

        if date:
            # Convert to datetime.datetime object
            if type(date) == PyQt5.QtCore.QDate:
                self.date = datetime.datetime.fromisoformat(date.toString(Qt.ISODate))
            elif type(date) == datetime.datetime:
                self.date = date
            elif type(date) == str:
                self.date = datetime.datetime.fromisoformat(date)
            elif type(date) == int:
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
        self.share_prices = self.query.all()

    def on_table_clicked(self, index):
        if index.column() == 6:
            self.on_click_delete_button(index)

    def on_click_delete_button(self, index):
        price = self.share_prices[index.row()]
        messagebox = QMessageBox.critical(
            self.parent(),
            _("Please confirm"),
            _("Are you sure you want to delete this price?"),
            buttons=QMessageBox.Yes | QMessageBox.No,
            defaultButton=QMessageBox.No,
        )

        if messagebox == QMessageBox.Yes:
            self.database.share_price_delete(price)
            self.beginRemoveRows(index, index.row(), index.row())
            self.set_filters()  # Reload the data
            self.endRemoveRows()


class SharePricesTableView(QTableView):
    columns = [
        {
            "name": _("Share"),
            "size": 0.3,
            "alignment": PyQt5.QtCore.Qt.AlignLeft,
        },
        {
            "name": _("ID"),
            "size": 0,
            "alignment": PyQt5.QtCore.Qt.AlignRight,
        },
        {
            "name": _("Date"),
            "size": 0.2,
            "alignment": PyQt5.QtCore.Qt.AlignRight,
        },
        {
            "name": _("Price"),
            "size": 0.2,
            "alignment": PyQt5.QtCore.Qt.AlignRight,
        },
        {
            "name": _("Currency"),
            "size": 0.1,
            "alignment": PyQt5.QtCore.Qt.AlignLeft,
        },
        {
            "name": _("Source"),
            "size": 0.2,
            "alignment": PyQt5.QtCore.Qt.AlignLeft,
        },
        {
            "name": _("Delete"),
            "size": 80,
            "alignment": PyQt5.QtCore.Qt.AlignCenter,
        },
    ]

    def __init__(self, parent_controller):
        super().__init__()
        self.parent_controller = parent_controller
        self.database = parent_controller.database

        self.model = SharePricesTableModel(self.database, self.columns)
        self.setModel(self.model)
        self.hideColumn(1)

        self.clicked.connect(self.on_table_clicked)

    def set_filters(self, share=None, date=None):
        self.model.set_filters(share, date)
        self.model.layoutChanged.emit()
        self.viewport().update()

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
        button = QAction(
            QIcon("assets/images/money.png"), _("Share Prices"), self.parent_window
        )
        button.setStatusTip(_("Displays share prices"))
        button.triggered.connect(lambda: self.parent_window.display_tab(self.name))
        return button

    def get_display_widget(self):
        self.display_widget = QWidget()
        self.display_widget.layout = QVBoxLayout()
        self.display_widget.setLayout(self.display_widget.layout)

        # Create the group of fields at the top
        form_group = QGroupBox("")
        self.form_layout = QFormLayout()
        form_group.setLayout(self.form_layout)
        self.display_widget.layout.addWidget(form_group)

        # Add Share field
        self.field_share = ShareComboBox(self.database, include_choice_all=True)
        self.form_layout.addRow(QLabel(_("Share")), self.field_share)
        self.field_share.currentIndexChanged.connect(self.on_select_share)

        # Add Date field
        self.field_date = QDateEdit()
        self.form_layout.addRow(QLabel("Date"), self.field_date)
        default_date = QDate.currentDate().addMonths(-1)
        self.field_date.setDate(default_date)
        width = self.field_date.sizeHint().width()
        self.field_date.dateChanged.connect(self.on_select_date)
        self.field_date.setFixedWidth(width * 2)

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
