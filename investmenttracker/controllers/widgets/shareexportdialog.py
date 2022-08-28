"""Displays a tool to import share prices

Classes
----------
SharePriceImportResultsDialog
    A dialog displaying the results of importing share prices

SharePriceImportDialog
    A dialog to select mapping information for share price import
"""
import gettext
import os

from PyQt5 import QtWidgets

_ = gettext.gettext


class ShareExportDialog:
    """Displays a dialog to export shares to a file

    The goal is for the user to select the details of the file format before export

    The system:
    - Stores user-provided mapping (if any) and tries to use it
    - Exports the data upon user confirmation

    Attributes
    ----------
    name : str
        The name of this dialog. Displayed in top bar.

    delimiter : str
        The delimiter between fields in the file to import
    export_headers : bool
        Whether the imported file has headers on the first row
    file_path : str
        The path to the file to import
    mapping : dict of format {column number: field mapped}
        The mapping between column numbers and the corresponding field
    shares : list of models.share.Share
        The list of shares to export
    possible_fields : dict of format {field ID: field label}
        The list of fields that can be exported

    map_fields : dict of format {column number: field widget}
        The dropdowns displayed for user-provided mapping

    window : QtWidgets.QDialog
        The dialog this class displays
    layout : QtWidgets.QGridLayout
        The layout of the dialog being displayed
    delimiter_label : QtWidgets.QLabel
        The label 'Delimiter'
    delimiter_widget : QtWidgets.QComboBox
        The dropdown for delimiter choice
    export_headers_widget : QtWidgets.QCheckBox
        The checkbox 'Export headers?'

    error_label : QtWidgets.QLabel
        The display of errors
    data_table : QtWidgets.QTableWidget
        The table contains the mapped file contents

    Methods
    -------
    __init__ (parent_controller)
        Gets previous user's choices from the database & sets up UI elements

    show_window
        Displays the dialog with load results

    set_file (file_path)
        Sets the path of the file to export

    display_table
        Displays the table with mapping headers & the share data

    get_share_field (share, field_id)
        Gets the information of a given field for a given share

    on_export_headers (export_headers)
        User clicks on 'had headers'. Triggers a remapping of the file.
    on_change_header (column, value)
        User changes one of the header mapping. Triggers self.check_data
    on_confirm_export
        User clicks 'OK'. Export the share list

    set_delimiter (new_delimiter)
        Sets the field delimiter

    save_config
        Saves the preferences (delimiter, export_headers, mapping)
    """

    name = _("Export shares")
    delimiter = ";"
    export_headers = False
    file_path = ""
    # Structure: {column number: field mapped}
    mapping = {}
    shares = []

    possible_fields = {
        "name": _("Name"),
        "id": _("ID"),
        "main_code": _("Main code"),
        "code_sync_origin": _("Code of online source"),
        "sync_origin": _("Get prices online from?"),
        "base_currency.id": _("Base currency (ID)"),
        "base_currency.name": _("Base currency (name)"),
        "base_currency.main_code": _("Base currency (main code)"),
    }

    map_fields = {}

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
        self.shares = self.database.shares_get(only_synced=True)
        self.config = parent_controller.config

        self.delimiter = self.config.get("export.delimiter", self.delimiter)
        self.delimiter = "\t" if self.delimiter == "Tab" else self.delimiter
        self.export_headers = self.config.get(
            "export.export_headers", self.export_headers
        )
        self.export_headers = (
            False if self.export_headers == "0" else self.export_headers
        )

        mapping = self.config.get("export.mapping", "")
        if mapping:
            self.mapping = {
                col: val for col, val in enumerate(mapping.split(";")) if val != ""
            }

        self.window = QtWidgets.QDialog(self.parent_controller.parent_window)
        self.layout = QtWidgets.QGridLayout()
        self.delimiter_label = QtWidgets.QLabel(_("Field delimiter"))
        self.delimiter_widget = QtWidgets.QComboBox()
        self.export_headers_widget = QtWidgets.QCheckBox(_("Export headers?"))
        self.error_label = QtWidgets.QLabel()
        self.data_table = QtWidgets.QTableWidget()

    def show_window(self):
        """Shows the export dialog"""
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

        # Should we export headers?
        self.export_headers_widget.setTristate(False)
        self.export_headers_widget.clicked.connect(self.on_export_headers)
        self.layout.addWidget(self.export_headers_widget, 2, 0, 1, 2)

        # Errors
        self.error_label.setProperty("class", "validation_warning")
        self.layout.addWidget(self.error_label, 3, 0, 1, 2)

        # Table with preview & choice of values
        self.layout.addWidget(self.data_table, 4, 0, 1, 2)
        self.data_table.setEditTriggers(self.data_table.NoEditTriggers)

        # Validation buttons
        buttons = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        button_box = QtWidgets.QDialogButtonBox(buttons)
        button_box.accepted.connect(self.on_confirm_export)
        button_box.rejected.connect(self.window.close)
        button_box.button(QtWidgets.QDialogButtonBox.Ok).setText(_("Export"))
        self.layout.addWidget(button_box, 5, 1)

        self.display_table()

        self.window.setMinimumSize(600, 500)
        self.window.resize(self.layout.sizeHint())
        self.window.showMaximized()

    def set_file(self, file_path):
        """Sets the path of the file to export"""
        self.file_path = file_path

    def display_table(self):
        """Displays the table with mapping headers & the share data

        The header will have allow the user to choose the mapping for each column
        All synced shares will be displayed in the table
        """
        self.data_table.clear()
        self.data_table.setRowCount(len(self.shares) + 1)  # +1 due to headers
        self.data_table.setColumnCount(len(self.possible_fields))

        # Define all possible options
        possible_values = [("", 0)]
        for field_id, label in self.possible_fields.items():
            possible_values.append((label, field_id))

        # Add headers (dropdown for choice)
        if self.map_fields:
            # Delete existing fields
            indexes = list(self.map_fields.keys())
            for column in indexes:
                del self.map_fields[column]
        self.map_fields = {}
        for column in range(len(self.possible_fields)):
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
        for row, share in enumerate(self.shares):
            # Setting indicators
            for column in range(len(self.possible_fields)):
                value = ""
                if column in self.mapping:
                    value = self.get_share_field(share, self.mapping[column])
                item = QtWidgets.QTableWidgetItem(str(value))
                self.data_table.setItem(row + 1, column, item)

        self.data_table.resizeColumnsToContents()
        self.data_table.resizeRowsToContents()

    def get_share_field(self, share, field_id):
        """Gets the information of a given field for a given share

        Parameters
        ----------
        share : model.share.Share
            The share to be displayed
        field_id : str
            The field to display (may be a related object field)
        """
        if field_id in ["name", "id", "main_code", "code_sync_origin"]:
            return getattr(share, field_id)
        if field_id == "sync_origin":
            return getattr(share, field_id).name
        if field_id.startswith("base_currency"):
            if share.base_currency:
                field = field_id[len("base_currency") + 1 :]
                return getattr(share.base_currency, field)
        return ""

    def on_export_headers(self, export_headers):
        """User clicks on 'had headers'"""
        self.export_headers = export_headers

    def on_change_header(self, column, value):
        """User changes one of the header mapping. Triggers self.check_mapping"""
        self.mapping[column] = value[1]
        self.display_table()

    def on_confirm_export(self):
        """User clicks 'OK'. Export the share list"""
        self.save_config()

        file_contents = []

        if not self.mapping:
            self.error_label.setText(_("Please choose at least 1 field to export"))
            return

        # Map all the data
        nb_columns = max(self.mapping.keys()) + 1
        if self.export_headers:
            file_row = [
                self.mapping[column] if column in self.mapping else ""
                for column in range(nb_columns)
            ]
            file_contents.append(self.delimiter.join(file_row))
        for share in self.shares:
            file_row = [
                str(self.get_share_field(share, self.mapping[column]))
                if column in self.mapping
                else ""
                for column in range(nb_columns)
            ]
            file_contents.append(self.delimiter.join(file_row))

        file_text = "\n".join(file_contents)

        # Check if file exists
        export_file = True
        if os.path.exists(self.file_path):
            messagebox = QtWidgets.QMessageBox.critical(
                self.window,
                _("File exists"),
                _("The file already exists. Overwrite?"),
                buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                defaultButton=QtWidgets.QMessageBox.No,
            )

            if messagebox == QtWidgets.QMessageBox.No:
                export_file = False

        if export_file:
            with open(self.file_path, "w", encoding="UTF-8") as file_pointer:
                file_pointer.write(file_text)
            messagebox = QtWidgets.QMessageBox.information(
                self.window,
                _("File exported"),
                _("The data has been successfully exported"),
            )
            if messagebox:
                self.window.close()

    def set_delimiter(self, new_delimiter):
        """Sets the field delimiter"""
        self.delimiter = "\t" if new_delimiter == "Tab" else new_delimiter
        self.mapping = {}

    def save_config(self):
        """Saves the preferences (delimiter, export_headers, mapping)"""
        delimiter = "Tab" if self.delimiter == "\t" else self.delimiter
        self.database.config_set("export.delimiter", delimiter)
        self.database.config_set("export.export_headers", self.export_headers)
        mapping = ""
        for column in range(len(self.possible_fields)):
            if column in self.mapping:
                mapping += self.mapping[column]
            mapping += ";"
        mapping = mapping[:-1]
        self.database.config_set("export.mapping", mapping)
