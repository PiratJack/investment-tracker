"""Displays a dashboard of prices & tools to import/export data

Classes
----------
SharePriceStatsTable
    A table displaying statistics about share prices

DashboardController
    Handles user interactions and links all displayed widgets

ImportResultsDialog
    A dialog displaying the results of importing share prices
"""
import datetime
import gettext
import os.path

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt

import controllers.importdialog
import models.config

_ = gettext.gettext


class SharePriceStatsTable(QtWidgets.QTableWidget):
    def __init__(self, parent_controller):
        super().__init__()
        self.parent_controller = parent_controller
        self.database = parent_controller.database
        self.load_data()

    def load_data(self):
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
        self.setColumnCount(len(table_row))
        self.setHorizontalHeaderLabels(table_row)

        all_shares = self.database.shares_get()
        for share in all_shares:
            table_row = [share.name]
            share_prices = self.database.share_prices_get(
                share_id=share,
                start_date=start_date,
                end_date=current_date,
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
    name = "Dashboard"
    display_hidden = False

    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.database = parent_window.database
        self.config = parent_window.database.configs_get_all()

    def get_toolbar_button(self):
        button = QtWidgets.QAction(
            QtGui.QIcon("assets/images/dashboard.png"),
            _("Dashboard"),
            self.parent_window,
        )
        button.setStatusTip(_("Dashboard"))
        button.triggered.connect(lambda: self.parent_window.display_tab(self.name))
        return button

    def get_display_widget(self):
        self.display_widget = QtWidgets.QWidget()
        self.display_widget.layout = QtWidgets.QGridLayout()
        self.display_widget.setLayout(self.display_widget.layout)

        self.display_widget.layout.setHorizontalSpacing(
            self.display_widget.layout.horizontalSpacing() * 3
        )

        # Export shares to file
        self.export_file_label = QtWidgets.QLabel(_("Export share list"))
        self.display_widget.layout.addWidget(self.export_file_label, 0, 0)

        self.export_file_path = QtWidgets.QLineEdit()
        self.export_file_path.setText(self.config.get("export.filename", ""))
        self.export_file_path.setEnabled(False)
        self.display_widget.layout.addWidget(self.export_file_path, 0, 1)

        self.export_file_choose = QtWidgets.QPushButton(_("Choose export file"))
        self.export_file_choose.clicked.connect(self.on_choose_export_file)
        self.display_widget.layout.addWidget(self.export_file_choose, 0, 2)

        self.export_file = QtWidgets.QPushButton(_("Export data"))
        self.export_file.clicked.connect(self.on_export_shares)
        self.display_widget.layout.addWidget(self.export_file, 0, 3)

        # Load transactions from file
        self.load_from_file_label = QtWidgets.QLabel(_("Load share prices from file"))
        self.display_widget.layout.addWidget(self.load_from_file_label, 1, 0)

        self.load_from_file_path = QtWidgets.QLineEdit()
        self.load_from_file_path.setText(self.config.get("import.filename", ""))
        self.load_from_file_path.setEnabled(False)
        self.display_widget.layout.addWidget(self.load_from_file_path, 1, 1)

        self.load_from_file_choose = QtWidgets.QPushButton(_("Choose file"))
        self.load_from_file_choose.clicked.connect(self.on_choose_load_file)
        self.display_widget.layout.addWidget(self.load_from_file_choose, 1, 2)

        self.load_from_file = QtWidgets.QPushButton(_("Load data"))
        self.load_from_file.clicked.connect(self.on_load_share_prices)
        self.display_widget.layout.addWidget(self.load_from_file, 1, 3)

        # Last file import
        self.last_import_label = QtWidgets.QLabel(_("Last import done on"))
        self.display_widget.layout.addWidget(self.last_import_label, 2, 0)

        last_import_date = self.config.get("import.last", "")
        self.last_import = QtWidgets.QLabel()
        if last_import_date:
            last_import_date = datetime.datetime.strptime(last_import_date, "%Y-%m-%d")
            self.last_import.setText(last_import_date.strftime("%x"))

            too_old = datetime.datetime.now() + datetime.timedelta(days=-30)
            if last_import_date <= too_old:
                self.last_import.setProperty("class", "warning")
        self.display_widget.layout.addWidget(self.last_import, 2, 1)

        # Errors
        self.error_label = QtWidgets.QLabel()
        self.error_label.setProperty("class", "validation_warning")
        self.display_widget.layout.addWidget(self.error_label, 2, 2, 1, 2)

        # Share price statistics
        self.share_price_stats = SharePriceStatsTable(self)
        self.display_widget.layout.addWidget(self.share_price_stats, 4, 0, 1, 4)

        # TODO (major) - Audit: shares with price that change too much (in last 3 months)

        self.parent_window.setCentralWidget(self.display_widget)

        return self.display_widget

    def reload_data(self):
        return

    def on_choose_export_file(self):
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
        # TODO: Actually export the shares
        print("export shares")
        return

    def on_choose_load_file(self):
        dialog = QtWidgets.QFileDialog(self.parent_window)

        # Re-open last folder (if any)
        config = self.database.config_get_by_name("import.filename")
        if config:
            dialog.setDirectory(os.path.dirname(config.value))

        target, _ = dialog.getOpenFileName(self.parent_window, "Choose File")
        if target:
            self.load_from_file_path.setText(target)

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

    def on_load_share_prices(self):
        file_path = self.load_from_file_path.text()
        if not file_path:
            self.error_label.setText(_("Please select a file before importing"))
            return
        self.error_label.setText("")

        import_dialog = controllers.importdialog.ImportDialog(self)
        try:
            import_dialog.set_file(file_path)
        except UnicodeDecodeError:
            self.error_label.setText(
                _("There was an error reading this file. Please choose another file.")
            )
            return
        import_dialog.show_window()
