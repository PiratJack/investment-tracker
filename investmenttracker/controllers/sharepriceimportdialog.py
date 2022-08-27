"""Displays a tool to import share prices

Classes
----------
SharePriceImportResultsDialog
    A dialog displaying the results of importing share prices

SharePriceImportDialog
    A dialog to select mapping information for share price import
"""
import datetime
import gettext

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt

import sqlalchemy

from models.shareprice import SharePrice

_ = gettext.gettext


class SharePriceImportResultsDialog:
    """Displays accounts & held shares

    Attributes
    ----------
    name : str
        The name of this dialog. Displayed in top bar.
    shares : list of models.share.Share
        All shares present in database
    load_results : dict of format {share_id: {'loaded': int, 'duplicate': int}}
        The summary of the load per share
    parent_controller : ImportDialog
        The controller parent of this dialog

    window : QtWidgets.QDialog
        The dialog this class displays
    layout : QtWidgets.QVBoxLayout
        The layout of the dialog being displayed
    results_table : QtWidgets.QTableWidget
        The table with results

    Methods
    -------
    __init__ (parent_controller, shares, load_results)
        Sets up all data required to display the screen

    show_window
        Displays the dialog with load results

    fill_results_table
        Fills in the results table
    """

    name = _("Load results")
    shares = {}
    load_results = {}

    def __init__(self, parent_controller, shares, load_results):
        """Sets up all data required to display the screen

        Parameters
        ----------
        parent_window : QtWidgets.QMainWindow
            The window displaying this controller
        shares : list of models.share.Share
            All shares present in database
        load_results : dict of format {share_id: {'loaded': int, 'duplicate': int}}
            The summary of the load per share
        """
        super().__init__()
        self.parent_controller = parent_controller
        self.shares = shares
        self.load_results = load_results

        self.window = QtWidgets.QDialog(self.parent_controller.parent_window)
        self.layout = QtWidgets.QVBoxLayout()
        self.results_table = QtWidgets.QTableWidget()

    def show_window(self):
        """Displays the dialog with load results"""
        if hasattr(self, "window"):
            self.window.close()
            self.window = None

        self.window.setModal(True)

        # Display content
        self.window.setWindowTitle(self.name)
        self.window.setLayout(self.layout)

        # Table with results
        self.layout.addWidget(self.results_table)

        # Validation buttons
        buttons = QtWidgets.QDialogButtonBox.Ok
        button_box = QtWidgets.QDialogButtonBox(buttons)
        button_box.accepted.connect(self.window.close)
        self.layout.addWidget(button_box)

        self.fill_results_table()

        self.window.setMinimumSize(700, 900)
        self.window.resize(self.layout.sizeHint())
        self.window.show()

    def fill_results_table(self):
        """Fills in the results table"""
        self.results_table.setRowCount(len(self.load_results) + 1)
        self.results_table.setColumnCount(4)

        columns = enumerate([_("Share"), _("Loaded"), _("Duplicate"), _("Code")])
        for column, field in columns:
            item = QtWidgets.QTableWidgetItem(field)
            self.results_table.setHorizontalHeaderItem(column, item)

        # Add data in table
        row = 0
        result_keys = sorted(
            self.load_results.keys(), key=lambda s: self.shares[s].name
        )
        for share_id in result_keys:
            results = self.load_results[share_id]
            data = [
                self.shares[share_id].name,
                results["loaded"],
                results["duplicate"],
                self.shares[share_id].main_code,
            ]

            for column, info in enumerate(data):
                item = QtWidgets.QTableWidgetItem(str(info))
                if isinstance(info, int):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    if info > 0:
                        item.setBackground(QtGui.QBrush(Qt.darkCyan))
                self.results_table.setItem(row, column, item)
            row += 1

        # Calculate & display totals
        total_loaded = sum(a["loaded"] for a in self.load_results.values())
        total_duplicate = sum(a["duplicate"] for a in self.load_results.values())
        data = [_("Total"), total_loaded, total_duplicate]
        for column, info in enumerate(data):
            item = QtWidgets.QTableWidgetItem(str(info))
            if isinstance(info, int):
                item.setTextAlignment(Qt.AlignRight)
                if info > 0:
                    item.setBackground(QtGui.QBrush(Qt.darkCyan))
            self.results_table.setItem(row, column, item)

        self.results_table.resizeColumnsToContents()
        self.results_table.resizeRowsToContents()


class SharePriceImportDialog:
    """Displays a dialog to import share prices from a file

    The goal is for the user to see all errors prior to the actual import.

    The system:
    - Stores user-provided mapping (if any) and tries to use it
    - Guesses mappping based on the file's first row & date formats
    - Checks data and provides errors to the user
    - Loads the data upon user confirmation, then displays a summary

    Attributes
    ----------
    name : str
        The name of this dialog. Displayed in top bar.

    delimiter : str
        The delimiter between fields in the file to import
    decimal_dot : str
        The delimiter between fields in the file to import
    has_headers : bool
        Whether the imported file has headers on the first row
    file_path : str
        The path to the file to import
    file_contents : list of str
        The contents of the file to import
    mapping : dict of format {column number: field mapped}
        The mapping between column numbers and the corresponding field
    required_fields : dict of format {field ID: field label}
        The list of required fields
    header_to_field : dict of format {possible header name: field ID}
        Mapping of possible header labels to field IDs
    field_formats : dict of format {field ID: {format: label of format}}
        Possible formats for specific fields (mostly dates)

    map_fields : dict of format {column number: field widget}
        The dropdowns displayed for user-provided mapping
    nb_columns : int
        The number of columns in the file (maximum of all rows)
    data : list of lists (format: [row: [list of columns]])
        The data present in the file
    data_errors : list of dicts - format: [row: {column: error}]
        The errors detected in parsing the file. column = -1 for general errors
    data_checked : bool
        Whether the data has been parsed / checked

    window : QtWidgets.QDialog
        The dialog this class displays
    layout : QtWidgets.QGridLayout
        The layout of the dialog being displayed
    results_table : QtWidgets.QTableWidget
        The table with results
    delimiter_label : QtWidgets.QLabel
        The label 'Delimiter'
    delimiter_widget : QtWidgets.QComboBox
        The dropdown for delimiter choice
    decimal_dot_label : QtWidgets.QLabel
        The label 'Decimal dot'
    decimal_dot_widget : QtWidgets.QComboBox
        The dropdown for decimal dot choice
    has_headers_widget : QtWidgets.QCheckBox
        The checkbox 'file has headers'

    error_label : QtWidgets.QLabel
        The display of errors
    data_table : QtWidgets.QTableWidget
        The table contains the mapped file contents

    load_results : dict of format {share_id: {'loaded': int, 'duplicate': int}}
        The summary of the load per share
    results_dialog : SharePriceImportResultsDialog
        The dialog displaying import results

    Methods
    -------
    __init__ (parent_controller)
        Gets previous user's choices from the database & sets up UI elements

    show_window
        Displays the dialog with load results

    set_file (file_path)
        Sets the path of the file to import

    process_data
        Processes the file (by calling many other functions)
    parse_headers
        Reads the file headers to guess possible headers
    load_file_in_memory
        Loads the file and splits it according to self.delimiter
        Updates self.data and self.nb_columns
    refine_mapping
        Refines the mapping by guessing special formats (like date format)
    is_mapping_complete
        Returns True if all required fields are mapped without duplicate
    check_data (nb_rows)
        Checks nb_rows of data for data format
        Updates self.data_errors according to found errors
    check_duplicate (share_price)
        Returns True if a share price is NOT a duplicate of existing data
    display_table
        Displays the table with mapping headers & the details of file data

    on_has_headers (has_headers)
        User clicks on 'had headers'. Triggers a remapping of the file.
    on_change_header (column, value)
        User changes one of the header mapping. Triggers self.check_data
    on_confirm_load
        User clicks 'OK'. Will load data without errors.
    parse_date_format (table_rows, column)
        Guesses the date format for a given column

    set_delimiter (new_delimiter)
        Sets the field delimiter
    set_decimal_dot (new_decimal_dot)
        Sets the decimal separator

    save_config
        Saves the preferences (delimiter, decimal_dot, has_headers, mapping)
    """

    name = _("Import share prices")
    delimiter = ";"
    decimal_dot = "."
    has_headers = False
    file_path = ""
    file_contents = []
    # Structure: {column number: field mapped}
    mapping = {}

    required_fields = {
        "share": _("Share"),
        "date": _("Date"),
        "price": _("Price"),
        "currency": _("Currency"),
        "source": _("Source"),
    }
    # Maps possible headers to field name
    header_to_field = {
        "share": "share",
        "share_id": "share",
        "date": "date",
        "price": "price",
        "value": "price",
        "currency": "currency",
        "currency_id": "currency",
        "source": "source",
    }
    # Maps field formats (when multiple ones are possible)
    field_formats = {
        "date": {
            "%d/%m/%Y": _("Date (DD/MM/YYYY)"),
            "%m/%d/%Y": _("Date (MM/DD/YYYY)"),
            "%Y/%m/%d": _("Date (YYYY/MM/DD)"),
            "%d-%m-%Y": _("Date (DD-MM-YYYY)"),
            "%m-%d-%Y": _("Date (MM-DD-YYYY)"),
            "%Y-%m-%d": _("Date (YYYY-MM-DD)"),
        }
    }

    map_fields = {}
    nb_columns = 0
    data = []
    data_errors = {}
    data_checked = False
    load_results = {}
    results_dialog = None

    def __init__(self, parent_controller):
        """Gets previous user's choices from the database & sets up UI elements

        Parameters
        ----------
        parent_controller : controllers.TransactionsController
            The controller displaying this class
        """
        super().__init__()
        self.parent_controller = parent_controller
        self.database = parent_controller.database
        self.config = parent_controller.config
        self.delimiter = self.config.get("import.delimiter", self.delimiter)
        self.delimiter = "\t" if self.delimiter == "Tab" else self.delimiter
        self.decimal_dot = self.config.get("import.decimal_dot", self.decimal_dot)
        self.has_headers = self.config.get("import.has_headers", self.has_headers)
        self.has_headers = False if self.has_headers == "0" else self.has_headers

        mapping = self.config.get("import.mapping", "")
        if mapping:
            self.mapping = {
                col: val for col, val in enumerate(mapping.split(";")) if val != ""
            }

        self.window = QtWidgets.QDialog(self.parent_controller.parent_window)
        self.layout = QtWidgets.QGridLayout()
        self.delimiter_label = QtWidgets.QLabel(_("Field delimiter"))
        self.delimiter_widget = QtWidgets.QComboBox()
        self.decimal_dot_label = QtWidgets.QLabel(_("Decimal point"))
        self.decimal_dot_widget = QtWidgets.QComboBox()
        self.has_headers_widget = QtWidgets.QCheckBox(_("The file has headers"))
        self.error_label = QtWidgets.QLabel()
        self.data_table = QtWidgets.QTableWidget()

    def show_window(self):
        """Shows the import dialog"""
        if hasattr(self, "window"):
            self.window.close()
            self.window = None

        self.window.setModal(True)

        # Display content
        self.window.setWindowTitle(self.name)
        self.window.setLayout(self.layout)

        # Field delimiter
        self.layout.addWidget(self.delimiter_label, 0, 0)
        for delimiter in [",", ";", ":", "Tab"]:
            self.delimiter_widget.addItem(delimiter)
        delimiter = "Tab" if self.delimiter == "\t" else self.delimiter
        self.delimiter_widget.setCurrentText(delimiter)
        self.delimiter_widget.currentTextChanged.connect(self.set_delimiter)
        self.layout.addWidget(self.delimiter_widget, 0, 1)

        # Decimal point
        self.layout.addWidget(self.decimal_dot_label, 1, 0)
        for decimal_dot in [",", "."]:
            self.decimal_dot_widget.addItem(decimal_dot)
        self.decimal_dot_widget.setCurrentText(self.decimal_dot)
        self.decimal_dot_widget.currentTextChanged.connect(self.set_decimal_dot)
        self.layout.addWidget(self.decimal_dot_widget, 1, 1)

        # Does the file has headers?
        self.has_headers_widget.setTristate(False)
        self.has_headers_widget.clicked.connect(self.on_has_headers)
        self.layout.addWidget(self.has_headers_widget, 2, 0, 1, 2)

        # Errors
        self.error_label.setProperty("class", "validation_warning")
        self.layout.addWidget(self.error_label, 3, 0, 1, 2)

        # Table with preview & choice of values
        self.layout.addWidget(self.data_table, 4, 0, 1, 2)

        # Validation buttons
        buttons = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        button_box = QtWidgets.QDialogButtonBox(buttons)
        button_box.accepted.connect(self.on_confirm_load)
        button_box.rejected.connect(self.window.close)
        self.layout.addWidget(button_box, 5, 1)

        self.process_data()

        self.window.setMinimumSize(600, 500)
        self.window.resize(self.layout.sizeHint())
        self.window.showMaximized()

    def set_file(self, file_path):
        """Sets the path of the file to import"""
        self.file_path = file_path
        self.file_contents = open(file_path, "r+", encoding="UTF-8").read().splitlines()

    def process_data(self):
        """Processes the file

        In order:
        - Resets data checks
        - Parse first line of file to find headers
        - Load file to memory
        - Determine special field formats (like date)
        - Check data (if all headers are known)
        - Display results
        """
        self.data_errors = {}
        self.data_checked = False

        self.parse_headers()
        if self.has_headers:
            self.has_headers_widget.setCheckState(Qt.Checked)
        self.load_file_in_memory()
        self.refine_mapping()
        if self.is_mapping_complete():
            self.check_data(30)
        self.display_table()

    def parse_headers(self):
        """Reads the file headers to guess possible headers"""
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
        """Loads the file and splits it according to self.delimiter

        Updates self.data and self.nb_columns
        """
        self.data = []
        self.nb_columns = 0
        for row, line in enumerate(self.file_contents):
            if self.has_headers and row == 0:
                continue
            fields = line.split(self.delimiter)
            self.data.append(fields)
            self.nb_columns = max(self.nb_columns, len(fields))

    def refine_mapping(self):
        """Refines the mapping by guessing special formats (like date format)"""
        if not self.mapping:
            return

        for column, field in self.mapping.items():
            if field == "date":
                date_formats = self.parse_date_format(self.data, column)
                if len(date_formats) == 1:
                    self.mapping[column] = date_formats[0]

    def is_mapping_complete(self):
        """Returns True if all required fields are mapped without duplicate"""
        # Convert format ID (in self.mapping) to a field list
        mapped_fields = [
            self.header_to_field[f]
            for f in self.mapping.values()
            if f in self.header_to_field and f not in self.field_formats
        ]
        mapped_fields += [
            k
            for k, v in self.field_formats.items()
            for f in self.mapping.values()
            if f in v
        ]
        missing = [f for f in self.required_fields if f not in mapped_fields]
        duplicate = [f for f in self.required_fields if mapped_fields.count(f) > 1]

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

    def check_data(self, nb_rows=30):
        """Checks nb_rows of data for data format

        Updates self.data_errors according to found errors
        Checks performed:
        - Share and Currency field contain a reference to existing shares
        - Dates are in the right format
        - Prices can be converted to floats
        - Source is mandatory

        Parameters
        ----------
        nb_rows : int
            The number of rows to check in the file
        """
        self.data_checked = False
        if not self.mapping or not self.data:
            return

        errors = {}
        for row, fields in enumerate(self.data):
            if row > nb_rows:
                break
            errors[row] = {}
            if len(fields) <= max(self.mapping.keys()):
                errors[row][-1] = _("Missing mandatory fields")
                continue
            for column, value in enumerate(fields):
                if column not in self.mapping:
                    continue
                field_id = self.mapping[column]
                # Shares and currencies should exist in the DB
                if field_id in ("share", "currency"):
                    share = self.database.share_search(value)
                    if len(share) != 1:
                        try:
                            share = self.database.share_get_by_id(value)
                        except sqlalchemy.orm.exc.NoResultFound:
                            errors[row][column] = _("Could not find share in database")
                # Date should have the proper format - Unknown date format
                elif field_id == "date":
                    # This should not happen
                    errors[row][column] = _("Unknown date format")
                # Date should have the proper format - Date format known
                elif field_id in self.field_formats["date"]:
                    try:
                        datetime.datetime.strptime(value, field_id)
                    except ValueError:
                        errors[row][column] = _("The date format is wrong")
                # Price should be a valid float
                elif field_id == "price":
                    try:
                        corrected_value = value.replace(self.decimal_dot, ".")
                        corrected_value = corrected_value.replace(" ", "")
                        corrected_value = float(corrected_value)
                    except ValueError:
                        errors[row][column] = _("The price is not a decimal number")
                # Source is mandatory
                elif field_id == "source":
                    if value == "":
                        errors[row][column] = _("The source field is mandatory")
            if not errors[row]:
                del errors[row]
        self.data_checked = True
        self.data_errors = errors

    def check_duplicate(self, share_price):
        """Returns True if a share price is NOT a duplicate of existing data

        Also updates self.load_results"""
        # Check for duplicates
        existing = self.database.share_prices_get(
            share_id=share_price.share_id,
            currency_id=share_price.currency_id,
            start_date=share_price.date,
            exact_date=True,
        )
        # Share is not synced yet still in the file
        if share_price.share_id not in self.load_results:
            self.load_results[share_price.share_id] = {"loaded": 0, "duplicate": 0}
        if existing:
            self.load_results[share_price.share_id]["duplicate"] += 1
        else:
            self.load_results[share_price.share_id]["loaded"] += 1
            return True
        return False

    def display_table(self):
        """Displays the table with mapping headers & the details of file data

        The header will have allow the user to choose the mapping for each column
        The first 30 rows of the file are displayed
        Each cell may be colored in red in case data errors are detected
        """
        self.data_table.clear()
        self.data_table.setRowCount(min(31, len(self.data) + 1))  # +1 due to headers
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
        if self.map_fields:
            indexes = list(self.map_fields.keys())
            for column in indexes:
                del self.map_fields[column]
        self.map_fields = {}
        for column in range(self.nb_columns):
            self.map_fields[column] = QtWidgets.QComboBox()
            known_index = 0
            for index, possible_value in enumerate(possible_values):
                self.map_fields[column].addItem(*possible_value)
                # Is header mapping known?
                if column in self.mapping and self.mapping[column] == possible_value[1]:
                    known_index = index
            if known_index:
                self.map_fields[column].setCurrentIndex(known_index)
            self.data_table.setCellWidget(0, column, self.map_fields[column])

            self.map_fields[column].currentIndexChanged.connect(
                lambda index, c=column: self.on_change_header(c, possible_values[index])
            )

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
                self.data_table.setVerticalHeaderItem(row + 1, item)

            for column, field in enumerate(table_row):
                item = QtWidgets.QTableWidgetItem(str(field))
                if row in self.data_errors and column in self.data_errors[row]:
                    item.setBackground(Qt.red)
                self.data_table.setItem(row + 1, column, item)

        self.data_table.resizeColumnsToContents()
        self.data_table.resizeRowsToContents()

    def on_has_headers(self, has_headers):
        """User clicks on 'had headers'. Triggers a remapping of the file."""
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
        """User changes one of the header mapping. Triggers self.check_data"""
        self.mapping[column] = value[1]
        if self.is_mapping_complete():
            self.check_data(30)
        self.display_table()

    def on_confirm_load(self):
        """User clicks 'OK'. Will load data without errors.

        First maps all rows to corresponding models.shareprice.SharePrice objects
        Then checks for duplicates
        Updated load results
        Displays the SharePriceImportResultsDialog
        """
        # Check if the data is at the right format
        if not self.is_mapping_complete():
            return
        self.check_data(float("inf"))

        self.save_config()

        # Get all shares that are synchronized
        all_shares = {s.id: s for s in self.database.shares_get(with_hidden=True)}
        synced_shares = {s.id: s for s in all_shares.values() if s.sync_origin}
        load_results = {s: {"loaded": 0, "duplicate": 0} for s in synced_shares}
        ready_to_load = {}
        search_results = {}
        for row, fields in enumerate(self.data):
            if row in self.data_errors:
                continue
            share_price = SharePrice()
            for column, field_id in self.mapping.items():
                if column > len(fields):
                    self.data_errors[row] = {
                        -1: _("Missing fields in this row - column {column}").format(
                            column=column
                        )
                    }
                    break
                if field_id == "share":
                    # Stored in 'cache' to avoid repetitive calls to DB
                    if fields[column] in search_results:
                        share_price.share_id = search_results[fields[column]].id
                        continue

                    share = self.database.share_search(fields[column])
                    if len(share) != 1:
                        self.data_errors[row] = {
                            column: _("Could not find share in database")
                        }
                        break
                    search_results[fields[column]] = share[0]
                    share_price.share_id = share[0].id
                elif field_id in self.field_formats["date"]:
                    share_price.date = datetime.datetime.strptime(
                        fields[column], field_id
                    )
                elif field_id == "price":
                    share_price.price = float(fields[column])
                elif field_id == "currency":
                    # Stored in 'cache' to avoid repetitive calls to DB
                    if fields[column] in search_results:
                        share_price.currency_id = search_results[fields[column]].id
                        continue

                    share = self.database.share_search(fields[column])
                    if len(share) != 1:
                        self.data_errors[row] = {
                            column: _("Could not find currency in database")
                        }
                        break
                    search_results[fields[column]] = share[0]
                    share_price.currency_id = share[0].id
                elif field_id == "source":
                    share_price.source = fields[column]

            # Remove errors
            if row in self.data_errors:
                continue

            if self.check_duplicate(share_price):
                ready_to_load[row] = share_price

        # Load data
        self.database.session.add_all(ready_to_load.values())
        self.database.session.commit()

        self.results_dialog = SharePriceImportResultsDialog(
            self.parent_controller, all_shares, load_results
        )
        self.results_dialog.show_window()

    def parse_date_format(self, table_rows, column):
        """Guesses the date format for a given column"""
        data_to_check = [
            i[column] for i in table_rows if column in i and i[column] != ""
        ][:50]
        possible_formats = []
        for possible_format in self.field_formats["date"]:
            try:
                [datetime.datetime.strptime(d, possible_format) for d in data_to_check]
                possible_formats.append(possible_format)
            except ValueError:
                continue
        return possible_formats

    def set_delimiter(self, new_delimiter):
        """Sets the field delimiter"""
        if new_delimiter == self.decimal_dot:
            self.delimiter_widget.setCurrentText("Tab")
            return
        self.delimiter = "\t" if new_delimiter == "Tab" else new_delimiter
        self.mapping = {}
        self.process_data()

    def set_decimal_dot(self, new_decimal_dot):
        """Sets the decimal separator"""
        if new_decimal_dot == self.delimiter:
            self.decimal_dot_widget.setCurrentText(".")
            return
        self.decimal_dot = new_decimal_dot
        self.mapping = {}
        self.process_data()

    def save_config(self):
        """Saves the preferences (delimiter, decimal_dot, has_headers, mapping)"""
        delimiter = "Tab" if self.delimiter == "\t" else self.delimiter
        self.database.config_set("import.delimiter", delimiter)
        self.database.config_set("import.decimal_dot", self.decimal_dot)
        self.database.config_set("import.has_headers", self.has_headers)
        mapping = ""
        for column in range(self.nb_columns):
            if column in self.mapping:
                mapping += self.mapping[column]
            mapping += ";"
        mapping = mapping[:-1]
        self.database.config_set("import.mapping", mapping)
        self.database.config_set(
            "import.last", datetime.datetime.now().strftime("%Y-%m-%d")
        )
