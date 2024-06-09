"""Displays a dashboard of prices & tools to import/export data

Classes
----------
SharePriceStatsTable
    A table displaying statistics about share prices

DashboardController
    Controller for dashboard display - handled user interactions & children widgets
"""

import logging
import datetime
import gettext
import os.path
import os

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt

import models.config
from controllers.widgets.sharepriceimportdialog import SharePriceImportDialog
from controllers.widgets.shareexportdialog import ShareExportDialog

_ = gettext.gettext
logger = logging.getLogger(__name__)


class SharePriceStatsTable(QtWidgets.QTableWidget):
    """A table displaying statistics about share prices

    The goal is to identify shares for which we don't have a lot of prices available
    Each row is a share, each column is a month
    Cells display the number of share prices available for that month

    Attributes
    ----------
    parent_controller : SharesController
        The controller in which this class is displayed
    database : models.database.Database
        A reference to the application database

    Methods
    -------
    __init__ (parent_controller)
        Stores parameters for future use & loads data to display
    load_data
        Loads all data from database and fill the table
    """

    def __init__(self, parent_controller):
        """Stores parameters for future use & loads data to display

        Parameters
        ----------
        parent_controller : DashboardController
            The controller in which this table is displayed
        """
        logger.debug("SharePriceStatsTable.__init__")
        super().__init__()
        self.parent_controller = parent_controller
        self.database = parent_controller.database

    def load_data(self):
        """Loads all data from database and fill the table"""
        logger.debug("SharePriceStatsTable.load_data")
        self.clear()
        table_rows = []

        # Determine dates & set headers
        all_dates = []
        table_row = [""]
        today = datetime.date.today()
        if today.month > 6:
            start_date = datetime.date(today.year, today.month - 6, 1)
        else:
            start_date = datetime.date(today.year - 1, today.month + 6, 1)
        current_date = start_date
        while current_date <= today:
            all_dates.append(current_date)
            table_row.append(current_date.strftime("%x"))
            if current_date.month == 12:
                current_date = datetime.date(current_date.year + 1, 1, 1)
            else:
                current_date = datetime.date(
                    current_date.year, current_date.month + 1, 1
                )
        end_date = current_date
        self.setColumnCount(len(table_row))
        self.setHorizontalHeaderLabels(table_row)

        all_shares = self.database.shares_get(only_synced=True)
        for share in sorted(all_shares, key=lambda s: s.name):
            table_row = [share.name]
            share_prices = self.database.share_prices_get(
                share_id=share,
                start_date=start_date,
                end_date=end_date,
                currency_id=share.base_currency,
            )
            for current_date in all_dates:
                prices = [
                    p
                    for p in share_prices
                    if p.date.year == current_date.year
                    and p.date.month == current_date.month
                ]
                table_row.append(len(prices))
            table_rows.append(table_row)

        self.setRowCount(len(table_rows))

        for row, table_row in enumerate(table_rows):
            for column, value in enumerate(table_row):
                # Skip name, will be added through headers
                if column == 0:
                    continue
                item = QtWidgets.QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if value <= 10 and column != len(table_row) - 1:
                    item.setForeground(QtGui.QBrush(Qt.red))
                self.setItem(row, column, item)

        self.setVerticalHeaderLabels([a[0] for a in table_rows])
        self.resizeColumnsToContents()
        self.resizeRowsToContents()


class DashboardController:
    """Controller for dashboard display - handles user interactions & children widgets

    From top to bottom, displays:
    - Widgets to export shares in a file
    - Widgets to import share prices in the database
    - A table showing how many share prices are available per month & share

    Attributes
    ----------
    name : str
        Name of the controller - used in display
    display_hidden_accounts : bool
        Whether to display hidden accounts

    parent_window : QtWidgets.QMainWindow
        The parent window
    database : models.database.Database
        A reference to the application database
    config : dict of str
        The configuration items from the database

    display_widget : QtWidgets.QWidget
        The main display for this controller

    export_file_label : QtWidgets.QLabel
        The label to select a file for exporting shares
    export_file_path : QtWidgets.QLineEdit
        The path of the file for exporting shares
    export_file_choose : QtWidgets.QPushButton
        Button to select the file for exporting shares
    export_file : QtWidgets.QPushButton
        Button to trigger the export of shares

    import_file_label : QtWidgets.QLabel
        The label to select a file for importing share prices
    import_file_path : QtWidgets.QLineEdit
        The path of the file for importing share prices
    import_file_choose : QtWidgets.QPushButton
        Button to select the file for importing share prices
    import_file : QtWidgets.QPushButton
        Button to trigger the import of share prices

    last_import_label : QtWidgets.QLabel
        The label for the last import of share prices
    last_import : QtWidgets.QLabel
        The date of the last import of share prices

    error_label : QtWidgets.QLabel
        Errors to display

    share_price_stats : SharePriceStatsTable
        The table displaying share price statistics

    Methods
    -------
    __init__ (parent_controller)
        Stores parameters for future use, loads config & prepared UI elements
    get_toolbar_button
        Returns a QtWidgets.QAction for display in the main window toolbar
    get_display_widget
       Returns the main QtWidgets.QWidget for this controller
    reload_data
       Reloads all data from DB

    on_choose_export_file
       User wants to select export file: display dialog & store selection
    on_export_shares
       User wants to export shares: display export dialog

    on_choose_import_file
       User wants to select import file: display dialog & store selection
    on_import_share_prices
       User wants to import share prices: display import dialog
    """

    name = "Dashboard"

    def __init__(self, parent_window):
        """Stores parameters for future use, loads config & prepares UI elements"""
        logger.debug("DashboardController.__init__")
        self.parent_window = parent_window
        self.database = parent_window.database
        self.config = parent_window.database.configs_get_all()

        self.display_widget = QtWidgets.QWidget()
        self.export_file_label = QtWidgets.QLabel(_("Export share list"))
        self.export_file_path = QtWidgets.QLineEdit()
        self.export_file_choose = QtWidgets.QPushButton(_("Choose export file"))
        self.export_file = QtWidgets.QPushButton(_("Export data"))

        self.import_file_label = QtWidgets.QLabel(_("Load share prices from file"))
        self.import_file_path = QtWidgets.QLineEdit()
        self.import_file_choose = QtWidgets.QPushButton(_("Choose file"))
        self.import_file = QtWidgets.QPushButton(_("Load data"))

        self.last_import_label = QtWidgets.QLabel(_("Last import done on"))
        self.last_import = QtWidgets.QLabel()

        self.error_label = QtWidgets.QLabel()

        self.share_price_stats = SharePriceStatsTable(self)

    def get_toolbar_button(self):
        """Returns a QtWidgets.QAction for display in the main window toolbar"""
        logger.debug("DashboardController.get_toolbar_button")
        button = QtWidgets.QAction(
            QtGui.QIcon(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                + "/assets/images/dashboard.png"
            ),
            _("Dashboard"),
            self.parent_window,
        )
        button.setStatusTip(_("Dashboard"))
        button.triggered.connect(lambda: self.parent_window.display_tab(self.name))
        return button

    def get_display_widget(self):
        """Returns the main QtWidgets.QWidget for this controller"""
        logger.debug("DashboardController.get_display_widget")
        self.display_widget.layout = QtWidgets.QGridLayout()
        self.display_widget.setLayout(self.display_widget.layout)

        self.display_widget.layout.setHorizontalSpacing(
            self.display_widget.layout.horizontalSpacing() * 3
        )

        # Export shares to file
        self.display_widget.layout.addWidget(self.export_file_label, 0, 0)

        self.export_file_path.setEnabled(False)
        self.display_widget.layout.addWidget(self.export_file_path, 0, 1)

        self.export_file_choose.clicked.connect(self.on_choose_export_file)
        self.display_widget.layout.addWidget(self.export_file_choose, 0, 2)

        self.export_file.clicked.connect(self.on_export_shares)
        self.display_widget.layout.addWidget(self.export_file, 0, 3)

        # Load transactions from file
        self.display_widget.layout.addWidget(self.import_file_label, 1, 0)

        self.import_file_path.setEnabled(False)
        self.display_widget.layout.addWidget(self.import_file_path, 1, 1)

        self.import_file_choose.clicked.connect(self.on_choose_import_file)
        self.display_widget.layout.addWidget(self.import_file_choose, 1, 2)

        self.import_file.clicked.connect(self.on_import_share_prices)
        self.display_widget.layout.addWidget(self.import_file, 1, 3)

        # Last file import
        self.display_widget.layout.addWidget(self.last_import_label, 2, 0)

        self.display_widget.layout.addWidget(self.last_import, 2, 1)

        # Errors
        self.error_label.setProperty("class", "validation_warning")
        self.display_widget.layout.addWidget(self.error_label, 2, 2, 1, 2)

        # Share price statistics
        self.display_widget.layout.addWidget(self.share_price_stats, 3, 0, 1, 4)

        self.parent_window.setCentralWidget(self.display_widget)

        self.reload_data()

        return self.display_widget

    def reload_data(self):
        """Reloads all data from DB"""
        logger.debug("DashboardController.reload_data")
        self.config = self.database.configs_get_all()

        self.export_file_path.setText(self.config.get("export.filename", ""))
        self.import_file_path.setText(self.config.get("import.filename", ""))

        last_import_date = self.config.get("import.last", "")
        if last_import_date:
            last_import_date = datetime.datetime.strptime(last_import_date, "%Y-%m-%d")
            self.last_import.setText(last_import_date.strftime("%x"))

            too_old = datetime.datetime.now() + datetime.timedelta(days=-30)
            if last_import_date <= too_old:
                self.last_import.setProperty("class", "warning")

        self.share_price_stats.load_data()

    def on_choose_export_file(self):
        """User wants to select export file: display dialog & store selection"""
        logger.debug("DashboardController.on_choose_export_file")
        dialog = QtWidgets.QFileDialog(self.parent_window)

        # Re-open last folder (if any)
        config = self.database.config_get_by_name("export.filename")
        if config:
            dialog.setDirectory(os.path.dirname(config.value))

        target, _ = dialog.getSaveFileName(self.parent_window, "Choose File")
        if target:
            self.export_file_path.setText(target)

            # Update DB
            config = self.database.config_get_by_name("export.filename")
            if config:
                config.value = target
            else:
                config = models.config.Config(name="export.filename", value=target)
            self.database.session.add(config)
            self.database.session.commit()
            # Update cache
            self.config = self.database.configs_get_all()

    def on_export_shares(self):
        """User wants to export shares: display export dialog"""
        logger.debug("DashboardController.on_export_shares")
        file_path = self.export_file_path.text()
        if not file_path:
            self.on_choose_export_file()
        # If user still doesn't want to choose, display error
        file_path = self.export_file_path.text()
        if not file_path:
            self.error_label.setText(_("Please select a file before exporting"))
            return
        self.error_label.setText("")

        export_dialog = ShareExportDialog(self)
        export_dialog.set_file(file_path)
        export_dialog.show_window()

        self.reload_data()

    def on_choose_import_file(self):
        """User wants to select import file: display dialog & store selection"""
        logger.debug("DashboardController.on_choose_import_file")
        dialog = QtWidgets.QFileDialog(self.parent_window)

        # Re-open last folder (if any)
        config = self.database.config_get_by_name("import.filename")
        if config:
            dialog.setDirectory(os.path.dirname(config.value))

        target, _ = dialog.getOpenFileName(self.parent_window, "Choose File")
        if target:
            self.import_file_path.setText(target)

            # Update DB
            config = self.database.config_get_by_name("import.filename")
            if config:
                config.value = target
            else:
                config = models.config.Config(name="import.filename", value=target)
            self.database.session.add(config)
            self.database.session.commit()
            # Update cache
            self.config = self.database.configs_get_all()

    def on_import_share_prices(self):
        """User wants to import share prices: display import dialog

        Opens file selection if file is not selected yet
        Displays error if user still doesn't want to choose a file
        """
        logger.debug("DashboardController.on_import_share_prices")
        file_path = self.import_file_path.text()
        if not file_path:
            self.on_choose_import_file()
        # If user still doesn't want to choose, display error
        if not file_path:
            self.error_label.setText(_("Please select a file before importing"))
            return
        self.error_label.setText("")

        import_dialog = SharePriceImportDialog(self)
        try:
            import_dialog.set_file(file_path)
        except UnicodeDecodeError:
            self.error_label.setText(
                _("There was an error reading this file. Please choose another file.")
            )
            return
        except UnicodeDecodeError:
            self.error_label.setText(
                _("There was an error reading this file. Please choose another file.")
            )
            return
        except FileNotFoundError:
            self.error_label.setText(_("The selected file does not exist"))
            return
        import_dialog.window.finished.connect(self.reload_data)
        import_dialog.show_window()
