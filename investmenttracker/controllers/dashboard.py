import datetime
import gettext
import os.path

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt

from models.shareprice import SharePrice
import models.config

_ = gettext.gettext

#TODO: Check if the configuration is updated when changes are made
#TODO: Check if the configuration is restored when opening
#TODO: Test a bunch of cases (share/currency via ID, name, main code, extra codes, ...)

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
            start_date = datetime.date(today.year, today.month-6, 1)
        else:
            start_date = datetime.date(today.year-1, today.month+6, 1)
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
                share=share, start_date=start_date, end_date=current_date, currency=share.base_currency
            )
            for current_date in all_dates:
                prices = [p for p in share_prices if p.date.year == current_date.year and p.date.month == current_date.month]
                table_row.append(len(prices))
            table_rows.append(table_row)

        self.setRowCount(len(table_rows))

        for row, table_row in enumerate(table_rows):
            for column, value in enumerate(table_row):
                # Skip name, will be added through headers
                if column == 0:
                    continue
                item = QtWidgets.QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignRight)
                if value <= 10 and column != len(table_row)-1:
                    item.setForeground(QtGui.QBrush(Qt.red))
                self.setItem(row, column, item)

        self.setVerticalHeaderLabels([a[0] for a in table_rows])
        self.resizeColumnsToContents()
        self.resizeRowsToContents()

class ImportResultsDialog:
    name = _('Load results')
    shares = {}
    loading_results = {}

    def __init__(self, parent_controller, shares, loading_results):
        super().__init__()
        self.parent_controller = parent_controller
        self.shares = shares
        self.loading_results = loading_results

    def show_window(self):
        if hasattr(self, "window"):
            self.window.close()
            self.window = None

        self.window = QtWidgets.QDialog(self.parent_controller.parent_window)
        self.window.setModal(True)

        # Display content
        self.layout = QtWidgets.QVBoxLayout()
        self.window.setWindowTitle(self.name)
        self.window.setLayout(self.layout)

        # Table with results
        self.results_table = QtWidgets.QTableWidget()
        self.layout.addWidget(self.results_table)

        # Validation buttons
        buttons = QtWidgets.QDialogButtonBox.Ok
        buttonBox = QtWidgets.QDialogButtonBox(buttons)
        buttonBox.accepted.connect(self.window.close)
        self.layout.addWidget(buttonBox)

        self.display_results()

        self.window.setMinimumSize(700, 900)
        self.window.resize(self.layout.sizeHint())
        self.window.show()

    def display_results(self):
        self.results_table.setRowCount(len(self.loading_results)+1)
        self.results_table.setColumnCount(4)

        for i, item in enumerate([_('Share'), _('Loaded'), _('Duplicate'), _('Code')]):
            item = QtWidgets.QTableWidgetItem(item)
            self.results_table.setHorizontalHeaderItem(i, item)

        # Add data in table
        row = 0
        for share_id, results in self.loading_results.items():
            data = [self.shares[share_id].name, results['loaded'], results['duplicate'], self.shares[share_id].main_code]
            for column, info in enumerate(data):
                item = QtWidgets.QTableWidgetItem(str(info))
                if type(info) == int:
                    item.setTextAlignment(Qt.AlignRight)
                self.results_table.setItem(row, column, item)
            row += 1
        total_loaded = sum(a['loaded'] for a in self.loading_results.values())
        total_duplicate = sum(a['duplicate'] for a in self.loading_results.values())
        data = [_('Total'), total_loaded, total_duplicate]
        for column, info in enumerate(data):
            item = QtWidgets.QTableWidgetItem(str(info))
            if type(info) == int:
                item.setTextAlignment(Qt.AlignRight)
            self.results_table.setItem(row, column, item)

        self.results_table.resizeColumnsToContents()
        self.results_table.resizeRowsToContents()



class ImportDialog:
    name = _('Import share prices')
    delimiter = ";"
    decimal_dot = "."
    has_headers = False
    # Structure: {column number: field mapped}
    mapping = {}

    required_fields = {
        'share': _('Share'),
        'date': _('Date'),
        'price': _('Price'),
        'currency': _('Currency'),
        'source': _('Source'),
    }
    # Maps possible headers to field name
    header_to_field = {
        'share': 'share',
        'share_id': 'share',
        'date': 'date',
        'price': 'price',
        'value': 'price',
        'currency': 'currency',
        'currency_id': 'currency',
        'source': 'source',
    }
    # Maps field formats (when multiple ones are possible)
    field_formats = {
        'date': {
            '%d/%m/%Y': _('Date (DD/MM/YYYY)'),
            '%m/%d/%Y': _('Date (MM/DD/YYYY)'),
            '%Y/%m/%d': _('Date (YYYY/MM/DD)'),
            '%d-%m-%Y': _('Date (DD-MM-YYYY)'),
            '%m-%d-%Y': _('Date (MM-DD-YYYY)'),
            '%Y-%m-%d': _('Date (YYYY-MM-DD)'),
        }
    }

    data = []
    nb_columns = 0
    data_errors = {}
    data_checked = False

    def __init__(self, parent_controller):
        super().__init__()
        self.parent_controller = parent_controller
        self.database = parent_controller.database
        self.config = parent_controller.config
        self.delimiter = self.config.get('import.delimiter', self.delimiter)
        self.decimal_dot = self.config.get('import.decimal_dot', self.decimal_dot)
        self.has_headers = self.config.get('import.decimal_dot', self.decimal_dot)

        mapping = self.config.get('import.mapping', '')
        if mapping:
            self.mapping = {column:i for column, i in mapping if i != ''}

    def show_window(self):
        if hasattr(self, "window"):
            self.window.close()
            self.window = None

        self.window = QtWidgets.QDialog(self.parent_controller.parent_window)
        self.window.setModal(True)

        # Display content
        self.layout = QtWidgets.QGridLayout()
        self.window.setWindowTitle(self.name)
        self.window.setLayout(self.layout)

        # Field delimiter
        self.delimiter_label = QtWidgets.QLabel(_("Field delimiter"))
        self.layout.addWidget(self.delimiter_label, 0, 0)

        self.delimiter_widget = QtWidgets.QComboBox()
        for delimiter in [',', ';', ':', 'Tab']:
            self.delimiter_widget.addItem(delimiter)
        self.delimiter_widget.setCurrentText(self.delimiter)
        self.delimiter_widget.currentTextChanged.connect(self.set_delimiter)
        self.layout.addWidget(self.delimiter_widget, 0, 1)

        # Decimal point
        self.decimal_dot_label = QtWidgets.QLabel(_("Decimal point"))
        self.layout.addWidget(self.decimal_dot_label, 1, 0)

        self.decimal_dot_widget = QtWidgets.QComboBox()
        for decimal_dot in [',', '.']:
            self.decimal_dot_widget.addItem(decimal_dot)
        self.decimal_dot_widget.setCurrentText(self.decimal_dot)
        self.decimal_dot_widget.currentTextChanged.connect(self.set_decimal_dot)
        self.layout.addWidget(self.decimal_dot_widget, 1, 1)

        # Does the file has headers?
        self.has_headers_widget = QtWidgets.QCheckBox(_("The file has headers"))
        self.has_headers_widget.setTristate(False)
        self.has_headers_widget.clicked.connect(self.on_has_headers)
        self.layout.addWidget(self.has_headers_widget, 2, 0, 1, 2)

        # Errors
        self.error_label = QtWidgets.QLabel()
        self.error_label.setProperty("class", "validation_warning")
        self.layout.addWidget(self.error_label, 3, 0, 1, 2)

        # Table with preview & choice of values
        self.data_table = QtWidgets.QTableWidget()
        self.layout.addWidget(self.data_table, 4, 0, 1, 2)

        # Validation buttons
        buttons = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        buttonBox = QtWidgets.QDialogButtonBox(buttons)
        buttonBox.accepted.connect(self.on_confirm_load)
        buttonBox.rejected.connect(self.window.close)
        self.layout.addWidget(buttonBox, 5, 1)


        self.process_data()

        self.window.setMinimumSize(600, 500)
        self.window.resize(self.layout.sizeHint())
        self.window.showMaximized()

    def set_file(self, file_path):
        self.file_path = file_path
        self.file_contents = open(file_path, "r+").read().splitlines()

    def process_data(self):
        self.parse_headers()
        if self.has_headers:
            self.has_headers_widget.setCheckState(Qt.Checked)
        self.load_file_in_memory()
        self.refine_mapping()
        if self.is_mapping_complete():
            self.check_data(30)
        self.display_table()

    # Looks for headers, but doesn't check the format of the data
    def parse_headers(self):
        if self.mapping:
            return

        file_headers = self.file_contents[0].split(self.delimiter)
        # Found a header
        if any(header in self.header_to_field for header in file_headers):
            self.has_headers = True
            for column, file_header in enumerate(file_headers):
                if file_header in self.header_to_field:
                    self.mapping[column] = self.header_to_field[file_header]

    def load_file_in_memory(self):
        self.data = []
        for row, line in enumerate(self.file_contents):
            if self.has_headers and row == 0:
                continue
            fields = line.split(self.delimiter)
            self.data.append(fields)
            self.nb_columns = max(self.nb_columns, len(fields))

    # Will try to find option ID based on existing mapping - mostly for date format
    def refine_mapping(self):
        if not self.mapping:
            return

        for column, field in self.mapping.items():
            if field == 'date':
                date_formats = self.parse_date_format(self.data, column)
                if len(date_formats) == 1:
                    self.mapping[column] = date_formats[0]

    # Check we have all fields needed & they appear only once
    def is_mapping_complete(self):
        # Convert format ID (in self.mapping) to a field list
        mapped_fields = [self.header_to_field[f] for f in self.mapping.values() if f in self.header_to_field and f not in self.field_formats]
        mapped_fields += [k for k in self.field_formats for f in self.mapping.values() if f in self.field_formats[k]]
        missing = [f for f in self.required_fields if f not in mapped_fields]
        duplicate = [f for f in self.required_fields if mapped_fields.count(f) >1]

        if missing or duplicate:
            errors = []
            if missing:
                fields = ", ".join([self.required_fields[i] for i in missing])
                errors.append(_("Missing fields: {fields}").format(fields=fields))
            if duplicate:
                fields = ", ".join([self.required_fields[i] for i in duplicate])
                errors.append(_("Duplicate fields: {fields}").format(fields=fields))
            self.error_label.setText("\n".join(errors))
            return False
        self.error_label.setText("")
        return True

    # Checks each row for format + values and provides a "status"
    def check_data(self, nb_rows=30):
        self.data_checked = False
        if not self.mapping or not self.data:
            return

        errors = {}
        for row, fields in enumerate(self.data):
            if row > nb_rows:
                break
            errors[row] = {}
            for column, value in enumerate(fields):
                if column not in self.mapping:
                    continue
                field_id = self.mapping[column]
                # Shares and currencies should exist in the DB
                if field_id in ("share", 'currency'):
                    share = self.database.share_search(value)
                    if len(share) != 1:
                        try:
                            share = self.database.share_get_by_id(value)
                        except:
                            errors[row][column] = _("Could not find share in database")
                # Date should have the proper format - Unknown date format
                elif field_id == "date":
                    # This should not happen
                    errors[row][column] = _("Unknown date format")
                # Date should have the proper format - Date format known
                elif field_id in self.field_formats["date"]:
                    try:
                        datetime.datetime.strptime(value, field_id)
                    except:
                        errors[row][column] = _("The date format is wrong")
                # Price should be a valid float
                elif field_id == "price":
                    try:
                        corrected_value = value.replace(self.decimal_dot, '.')
                        corrected_value = corrected_value.replace(' ', '')
                        corrected_value = float(corrected_value)
                    except:
                        errors[row][column] = _("The price is not a decimal number")
                # No need to check "source": it's a free text field
            if not errors[row]:
                del errors[row]
        self.data_checked = True
        self.data_errors = errors

    def display_table(self):
        self.data_table.setRowCount(len(self.data))
        self.data_table.setColumnCount(self.nb_columns)

        # Define all possible options
        possible_values = [("", 0)]
        for field_id, label in self.required_fields.items():
            if field_id in self.field_formats:
                for format_id in self.field_formats[field_id]:
                    label = self.field_formats[field_id][format_id]
                    possible_values.append((label, format_id))
            else:
                possible_values.append((label, field_id))

        # Add headers (dropdown for choice)
        self.map_fields = {}
        for column in range(self.nb_columns):
            self.map_fields[column] = QtWidgets.QComboBox()
            known_index = 0
            for index, element in enumerate(possible_values):
                self.map_fields[column].addItem(*element)
                # Is header mapping known?
                if column in self.mapping and self.mapping[column] == element[1]:
                    known_index = index
            if known_index:
                self.map_fields[column].setCurrentIndex(known_index)
            self.data_table.setCellWidget(0, column, self.map_fields[column])

            self.map_fields[column].currentIndexChanged.connect(lambda index, c=column: self.on_change_header(c, possible_values[index]))

        # Add data in table
        for row, table_row in enumerate(self.data):
            if row == 30:
                break
            # Setting indicators
            if self.data_checked:
                item = QtWidgets.QTableWidgetItem()
                if row in self.data_errors:
                    item.setIcon(QtGui.QIcon("assets/images/ko.png"))
                    item.setToolTip("/n".join(self.data_errors[row].values()))
                self.data_table.setVerticalHeaderItem(row+1, item)

            for column, field in enumerate(table_row):
                item = QtWidgets.QTableWidgetItem(str(field))
                if row in self.data_errors and column in self.data_errors[row]:
                    item.setBackground(Qt.red)
                self.data_table.setItem(row+1, column, item)

        self.data_table.resizeColumnsToContents()
        self.data_table.resizeRowsToContents()

    def on_has_headers(self, has_headers):
        self.has_headers = has_headers
        self.mapping = {}
        self.load_file_in_memory()
        if has_headers:
            self.parse_headers()
            self.refine_mapping()
            if self.is_mapping_complete():
                self.check_data(30)
        self.display_table()

    def on_change_header(self, column, value):
        self.mapping[column] = value[1]
        if self.is_mapping_complete():
            self.check_data(30)
        self.display_table()

    def on_confirm_load(self):
        # Check if the data is at the right format
        if not self.is_mapping_complete():
            return
        self.check_data(float('inf'))

        # Get all shares that are synchronized
        shares = self.database.shares_get()
        shares = {s.id:s for s in shares if s.sync_origin}
        load_results = {s: {'loaded': 0, 'duplicate': 0} for s in shares}
        ready_to_load = {}
        search_results = {}
        for row, fields in enumerate(self.data):
            if row in self.data_errors:
                #TODO: check if this filters properly (wrong_data in SQL?)
                continue
            share_price = SharePrice()
            for column, field_id in self.mapping.items():
                if field_id == 'share':
                    # Stored in 'cache' to avoid repetitive calls to DB
                    if fields[column] in search_results:
                        share_price.share_id = search_results[fields[column]].id
                        continue

                    share = self.database.share_search(fields[column])
                    if len(share) != 1:
                        self.data_errors[row] = {column: _("Could not find share in database")}
                        break
                    search_results[fields[column]] = share[0]
                    share_price.share_id = share[0].id
                elif field_id in self.field_formats['date']:
                    share_price.date = datetime.datetime.strptime(fields[column], field_id)
                elif field_id == 'price':
                    share_price.price = float(fields[column])
                elif field_id == 'currency':
                    # Stored in 'cache' to avoid repetitive calls to DB
                    if fields[column] in search_results:
                        share_price.currency_id = search_results[fields[column]].id
                        continue

                    share = self.database.share_search(fields[column])
                    if len(share) != 1:
                        self.data_errors[row] = {column: _("Could not find currency in database")}
                        break
                    search_results[fields[column]] = share[0]
                    share_price.currency_id = share[0].id
                elif field_id == 'source':
                    share_price.source = fields[column]

            # Check for duplicates
            existing = self.database.share_prices_get(share=share_price.share_id, currency=share_price.currency_id, start_date=share_price.date, exact_date=True)
            if existing:
                load_results[share_price.share_id]['duplicate'] += 1
            else:
                load_results[share_price.share_id]['loaded'] += 1
                ready_to_load[row] = share_price

        # Load data
        self.database.session.add_all(ready_to_load.values())
        self.database.session.commit()


        self.results = ImportResultsDialog(self.parent_controller, shares, load_results)
        self.results.show_window()

    def parse_date_format(self, table_rows, column):
        data_to_check = [i[column] for i in table_rows if i[column] != ''][:50]
        possible_formats = []
        for possible_format in self.field_formats['date']:
            try:
                [datetime.datetime.strptime(d, possible_format) for d in data_to_check]
                possible_formats.append(possible_format)
            except ValueError:
                continue
        return possible_formats

    def set_delimiter(self, new_delimiter):
        if new_delimiter == self.decimal_dot:
            self.delimiter_choice.setCurrentText('Tab')
            return
        self.delimiter = new_delimiter
        self.process_data()

    def set_decimal_dot(self, new_decimal_dot):
        if new_decimal_dot == self.delimiter:
            self.decimal_dot_choice.setCurrentText('.')
            return
        self.decimal_dot = new_decimal_dot
        self.process_data()

class DashboardController:
    name = "Dashboard"
    display_hidden = False

    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.database = parent_window.database
        self.config = parent_window.database.configs_get_all()

    def get_toolbar_button(self):
        button = QtWidgets.QAction(
            QtGui.QIcon("assets/images/dashboard.png"), _("Dashboard"), self.parent_window
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
        self.export_file_label = QtWidgets.QLabel(_('Export share list'))
        self.display_widget.layout.addWidget(self.export_file_label, 0, 0)

        self.export_file_path = QtWidgets.QLineEdit()
        self.export_file_path.setText(self.config.get('export.filename', ''))
        self.export_file_path.setEnabled(False)
        self.display_widget.layout.addWidget(self.export_file_path, 0, 1)

        self.export_file_choose = QtWidgets.QPushButton(_("Choose export file"))
        self.export_file_choose.clicked.connect(self.on_choose_export_file)
        self.display_widget.layout.addWidget(self.export_file_choose, 0, 2)

        self.export_file = QtWidgets.QPushButton(_("Export data"))
        self.export_file.clicked.connect(self.on_export_shares)
        self.display_widget.layout.addWidget(self.export_file, 0, 3)


        # Load transactions from file
        self.load_from_file_label = QtWidgets.QLabel(_('Load share prices from file'))
        self.display_widget.layout.addWidget(self.load_from_file_label, 1, 0)

        self.load_from_file_path = QtWidgets.QLineEdit()
        self.load_from_file_path.setText(self.config.get('import.filename', ''))
        self.load_from_file_path.setEnabled(False)
        self.display_widget.layout.addWidget(self.load_from_file_path, 1, 1)

        self.load_from_file_choose = QtWidgets.QPushButton(_("Choose file"))
        self.load_from_file_choose.clicked.connect(self.on_choose_load_file)
        self.display_widget.layout.addWidget(self.load_from_file_choose, 1, 2)

        self.load_from_file = QtWidgets.QPushButton(_("Load data"))
        self.load_from_file.clicked.connect(self.on_load_share_prices)
        self.display_widget.layout.addWidget(self.load_from_file, 1, 3)

        # Last file import
        self.last_import_label = QtWidgets.QLabel(_('Last import done on'))
        self.display_widget.layout.addWidget(self.last_import_label, 2, 0)

        last_import_date = self.config.get('import.last', '')
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
        config = self.database.config_get_by_name('export.filename')
        if config:
            dialog.setDirectory(os.path.dirname(config.value))

        target, _ = dialog.getSaveFileName(self.parent_window, "Choose File")
        if target:
            self.export_file_path.setText(target)

            # Update DB
            config = self.database.config_get_by_name('export.filename')
            if config:
                config.value = target
            else:
                config = models.config.Config(name='export.filename', value=target)
            self.database.session.add(config)
            self.database.session.commit()
            # Update cache
            self.config = self.database.configs_get_all()

    def on_export_shares(self):
        # TODO: Actually export the shares
        print('export shares')
        return

    def on_choose_load_file(self):
        dialog = QtWidgets.QFileDialog(self.parent_window)

        # Re-open last folder (if any)
        config = self.database.config_get_by_name('import.filename')
        if config:
            dialog.setDirectory(os.path.dirname(config.value))

        target, _ = dialog.getOpenFileName(self.parent_window, "Choose File")
        if target:
            self.load_from_file_path.setText(target)

            # Update DB
            config = self.database.config_get_by_name('import.filename')
            if config:
                config.value = target
            else:
                config = models.config.Config(name='import.filename', value=target)
            self.database.session.add(config)
            self.database.session.commit()
            # Update cache
            self.config = self.database.configs_get_all()

    def on_load_share_prices(self):
        file_path = self.load_from_file_path.text()
        if not file_path:
            self.error_label.setText(_("Please select a file before importing"))
            return
        self.error_label.setText('')

        import_dialog = ImportDialog(self)
        try:
            import_dialog.set_file(file_path)
        except UnicodeDecodeError:
            self.error_label.setText(_("There was an error reading this file. Please choose another file."))
            return
        import_dialog.show_window()