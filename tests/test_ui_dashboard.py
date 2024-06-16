import os
import sys
import pytest
import datetime
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "investmenttracker"))


class TestUiDashboard:
    @pytest.fixture
    def app_dashboard(self, app_mainwindow):
        app_mainwindow.display_tab("Dashboard")

        yield app_mainwindow.layout.currentWidget()

    @pytest.fixture
    def app_ui(self, app_mainwindow, app_dashboard):
        def get_ui(element):
            # Main window
            if element == "mainwindow":
                return app_mainwindow

            # Overall elements
            if element == "layout":
                return app_dashboard.layout

            # Top: Export-related items
            elif element == "export_title":
                return app_dashboard.layout.itemAtPosition(0, 0).widget()
            elif element == "export_path":
                return app_dashboard.layout.itemAtPosition(0, 1).widget()
            elif element == "export_choose":
                return app_dashboard.layout.itemAtPosition(0, 2).widget()
            elif element == "export_exec":
                return app_dashboard.layout.itemAtPosition(0, 3).widget()

            # 2nd from top: Import-related items
            elif element == "import_title":
                return app_dashboard.layout.itemAtPosition(1, 0).widget()
            elif element == "import_path":
                return app_dashboard.layout.itemAtPosition(1, 1).widget()
            elif element == "import_choose":
                return app_dashboard.layout.itemAtPosition(1, 2).widget()
            elif element == "import_exec":
                return app_dashboard.layout.itemAtPosition(1, 3).widget()
            elif element == "import_last_title":
                return app_dashboard.layout.itemAtPosition(2, 0).widget()
            elif element == "import_last_date":
                return app_dashboard.layout.itemAtPosition(2, 1).widget()

            # 3rd from top: Errors
            elif element == "errors":
                return app_dashboard.layout.itemAtPosition(2, 2).widget()

            # Bottom part: Price table
            elif element == "price_table":
                return app_dashboard.layout.itemAtPosition(3, 0).widget()
            elif element.startswith("price_"):
                row, col = map(int, element.split("_")[1:])
                if (
                    row > get_ui("price_table").rowCount()
                    or col >= get_ui("price_table").columnCount()
                ):
                    return None
                if row == 0:
                    return get_ui("price_table").horizontalHeaderItem(int(col)).text()
                if col == 0:
                    return get_ui("price_table").verticalHeaderItem(int(row) - 1).text()
                return get_ui("price_table").item(row - 1, col).text()

            raise ValueError(f"Field {element} could not be found")

        return get_ui

    @pytest.fixture
    def exportdialog_ui(self, qtbot, qapp):
        def get_ui(element):
            qtbot.waitUntil(lambda: qapp.activeWindow() is not None)
            dialog = qapp.activeWindow()

            if element == "dialog":
                return dialog
            elif element == "separator_title":
                return dialog.layout().itemAtPosition(0, 0).widget()
            elif element == "separator_field":
                return dialog.layout().itemAtPosition(0, 1).widget()
            elif element == "export_header":
                return dialog.layout().itemAtPosition(1, 0).widget()
            elif element == "errors":
                return dialog.layout().itemAtPosition(2, 0).widget()
            elif element == "table":
                return dialog.layout().itemAtPosition(3, 0).widget()
            elif element.startswith("table_"):
                row, col = element.split("_")[1:]
                if row == "0":
                    return get_ui("table").cellWidget(int(row), int(col))
                return get_ui("table").item(int(row), int(col))

            elif element == "buttonbox":
                return dialog.layout().itemAtPosition(4, 1).widget()
            elif element == "button_cancel":
                return get_ui("buttonbox").button(QtWidgets.QDialogButtonBox.Cancel)
            elif element == "button_export":
                return get_ui("buttonbox").button(QtWidgets.QDialogButtonBox.Ok)

            raise ValueError(f"Field {element} could not be found")

        return get_ui

    @pytest.fixture
    def patch_export(self, app_ui, qtbot, monkeypatch):
        def define_file(temp_file):
            monkeypatch.setattr(
                QtWidgets.QFileDialog,
                "getSaveFileName",
                lambda *args, **kwargs: (temp_file.fileName(), ""),
            )
            qtbot.mouseClick(app_ui("export_choose"), Qt.LeftButton, Qt.NoModifier)
            temp_file.close()  # Allow the app to use the file in read-write mode

        return define_file

    def test_dashboard_display(self, app_ui):
        # Check overall structure
        assert isinstance(app_ui("layout"), QtWidgets.QGridLayout), "Layout is OK"
        assert app_ui("layout").rowCount() == 4, "Row count is OK"
        assert app_ui("layout").columnCount() == 4, "Column count is OK"

        # Check Top: Export-related items
        assert isinstance(app_ui("export_title"), QtWidgets.QLabel), "Export title OK"
        assert app_ui("export_title").text() == "Export share list", "Export title OK"
        assert isinstance(app_ui("export_path"), QtWidgets.QLineEdit), "Export path OK"
        assert app_ui("export_path").text() == "", "Export path OK"
        assert isinstance(
            app_ui("export_choose"), QtWidgets.QPushButton
        ), "Export selection OK"
        assert (
            app_ui("export_choose").text() == "Choose export file"
        ), "Export selection OK"
        assert isinstance(
            app_ui("export_exec"), QtWidgets.QPushButton
        ), "Export exec OK"
        assert app_ui("export_exec").text() == "Export data", "Export exec OK"

        # Check 2nd from top: Import-related items
        assert isinstance(app_ui("import_title"), QtWidgets.QLabel), "Import title OK"
        assert (
            app_ui("import_title").text() == "Load share prices from file"
        ), "Import title OK"
        assert isinstance(app_ui("import_path"), QtWidgets.QLineEdit), "Import path OK"
        assert app_ui("import_path").text() == "", "Import path OK"
        assert isinstance(
            app_ui("import_choose"), QtWidgets.QPushButton
        ), "Import selection OK"
        assert app_ui("import_choose").text() == "Choose file", "Import selection OK"
        assert isinstance(
            app_ui("import_exec"), QtWidgets.QPushButton
        ), "Import exec OK"
        assert app_ui("import_exec").text() == "Load data", "Import exec OK"
        assert isinstance(
            app_ui("import_last_title"), QtWidgets.QLabel
        ), "Last import title OK"
        assert (
            app_ui("import_last_title").text() == "Last import done on"
        ), "Last import title OK"
        assert isinstance(
            app_ui("import_last_date"), QtWidgets.QLabel
        ), "Last import date OK"
        assert app_ui("import_last_date").text() == "", "Last import date OK"

        # Check error display
        assert isinstance(app_ui("errors"), QtWidgets.QLabel), "Errors OK"
        assert app_ui("errors").text() == "", "Errors OK"

        # Check bottom part: Price table
        assert isinstance(
            app_ui("price_table"), QtWidgets.QTableWidget
        ), "Price table OK"
        assert app_ui("price_table").rowCount() == 1, "Price table row count OK"
        assert app_ui("price_table").columnCount() == 8, "Price table column count OK"
        assert app_ui("price_1_0") == "Workday", "Price table value OK"
        assert app_ui("price_1_1") == "0", "Price table value OK"

    def test_dashboard_price_table_dates1(self, app_ui, app_mainwindow, monkeypatch):
        # Force today to be January 1st, 2024
        class mydatee(datetime.date):
            @classmethod
            def today(cls):
                return datetime.date(2024, 1, 1)

        # #monkeypatch.setattr(datetime.date, "today", lambda: datetime.date(2024,1,1))
        monkeypatch.setattr(datetime, "date", mydatee)
        # Force reload of the screen
        app_mainwindow.display_tab("Dashboard")

        assert app_ui("price_table").rowCount() == 1, "Price table row count OK"
        assert app_ui("price_table").columnCount() == 8, "Price table column count OK"
        assert app_ui("price_1_0") == "Workday", "Price table value OK"
        assert app_ui("price_1_1") == "0", "Price table value OK"
        assert app_ui("price_0_1") == "01/07/2023", "Price table header OK"
        assert app_ui("price_0_5") == "01/11/2023", "Price table header OK"
        assert app_ui("price_0_7") == "01/01/2024", "Price table header OK"

    def test_dashboard_price_table_dates2(self, app_ui, app_mainwindow, monkeypatch):
        # Force today to be January 1st, 2024
        class mydatee(datetime.date):
            @classmethod
            def today(cls):
                return datetime.date(2024, 8, 1)

        # #monkeypatch.setattr(datetime.date, "today", lambda: datetime.date(2024,1,1))
        monkeypatch.setattr(datetime, "date", mydatee)
        # Force reload of the screen
        app_mainwindow.display_tab("Dashboard")

        assert app_ui("price_table").rowCount() == 1, "Price table row count OK"
        assert app_ui("price_table").columnCount() == 8, "Price table column count OK"
        assert app_ui("price_1_0") == "Workday", "Price table value OK"
        assert app_ui("price_1_1") == "0", "Price table value OK"
        assert app_ui("price_0_1") == "01/02/2024", "Price table header OK"
        assert app_ui("price_0_5") == "01/06/2024", "Price table header OK"
        assert app_ui("price_0_7") == "01/08/2024", "Price table header OK"

    def test_export_file_choose(
        self, app_ui, app_db, qtbot, monkeypatch, patch_export, exportdialog_ui
    ):
        # Trigger export on temporary file
        temp_file = QtCore.QTemporaryFile()
        if temp_file.open():
            patch_export(temp_file)

            # Check fields & DB are updated
            assert (
                app_ui("export_path").text() == temp_file.fileName()
            ), "Export path updated OK in UI"
            assert (
                app_db.config_get_by_name("export.filename").value
                == temp_file.fileName()
            ), "Export path updated OK in DB"

    def test_export_file_choose_twice(
        self, app_ui, app_db, qtbot, monkeypatch, patch_export, exportdialog_ui
    ):
        # Trigger export on temporary file
        temp_file = QtCore.QTemporaryFile()
        if temp_file.open():
            patch_export(temp_file)

            # Trigger file selection a second time, with different value
            monkeypatch.setattr(
                QtWidgets.QFileDialog,
                "getSaveFileName",
                lambda *args, **kwargs: ("/tmp/temp.txt", ""),
            )
            qtbot.mouseClick(app_ui("export_choose"), Qt.LeftButton, Qt.NoModifier)

            # Check results
            assert (
                app_ui("export_path").text() == "/tmp/temp.txt"
            ), "Export path updated OK"
            assert (
                app_db.config_get_by_name("export.filename").value == "/tmp/temp.txt"
            ), "Export path updated OK"

    def test_export_file_cancel(self, app_ui, qtbot, patch_export, exportdialog_ui):
        # Check dialog contents + cancel
        def handle_dialog():
            # Get the different fields
            separator_title = exportdialog_ui("separator_title")
            separator_field = exportdialog_ui("separator_field")
            export_header = exportdialog_ui("export_header")
            errors = exportdialog_ui("errors")
            table = exportdialog_ui("table")
            table_0_0 = exportdialog_ui("table_0_0")
            table_0_1 = exportdialog_ui("table_0_1")
            table_1_0 = exportdialog_ui("table_1_0")
            table_1_1 = exportdialog_ui("table_1_1")
            button_export = exportdialog_ui("button_export")
            button_cancel = exportdialog_ui("button_cancel")

            assert isinstance(separator_title, QtWidgets.QLabel), "Separator title OK"
            assert separator_title.text() == "Field delimiter", "Separator title OK"
            assert isinstance(separator_field, QtWidgets.QComboBox), "Export header OK"
            assert separator_field.currentText() == ";", "Field separator value OK"
            assert isinstance(export_header, QtWidgets.QCheckBox), "Export header OK"
            assert export_header.text() == "Export headers?", "Export header OK"
            assert isinstance(errors, QtWidgets.QLabel), "Errors OK"
            assert errors.text() == "", "Errors OK"

            assert isinstance(table, QtWidgets.QTableWidget), "Table OK"
            assert isinstance(table_0_0, QtWidgets.QComboBox), "Table header OK"
            assert isinstance(table_0_1, QtWidgets.QComboBox), "Table header OK"
            assert table_0_0.currentText() == "", "Table header OK"
            assert table_0_1.currentText() == "", "Table header OK"
            assert table_1_0.text() == "", "Table row OK"
            assert table_1_1.text() == "", "Table row OK"

            assert isinstance(button_cancel, QtWidgets.QPushButton), "Cancel button OK"
            assert isinstance(button_export, QtWidgets.QPushButton), "Export button OK"

            qtbot.mouseClick(button_cancel, Qt.LeftButton, Qt.NoModifier)

        # Trigger export on temporary file
        temp_file = QtCore.QTemporaryFile()
        if temp_file.open():
            patch_export(temp_file)

            # Display export dialog
            QtCore.QTimer.singleShot(0, handle_dialog)
            qtbot.mouseClick(app_ui("export_exec"), Qt.LeftButton, Qt.NoModifier)

            # Check results
            file_contents = (
                open(temp_file.fileName(), "r+", encoding="UTF-8").read().splitlines()
            )
            assert file_contents == [], "No data exported"

    def test_export_file_confirm(
        self, app_ui, qtbot, monkeypatch, patch_export, exportdialog_ui
    ):
        # Choose values and confirm export
        def handle_dialog():
            # Get the different fields
            separator_field = exportdialog_ui("separator_field")
            table_0_0 = exportdialog_ui("table_0_0")
            table_0_1 = exportdialog_ui("table_0_1")
            table_0_2 = exportdialog_ui("table_0_2")
            button_export = exportdialog_ui("button_export")

            # Set values for export
            separator_field.setCurrentText(":")
            table_0_0.setCurrentIndex(table_0_0.findText("ID"))
            table_0_1.setCurrentIndex(table_0_1.findText("Name", Qt.MatchExactly))
            table_0_2.setCurrentIndex(table_0_2.findText("Name of group"))

            # Check display is updated
            table_1_0 = exportdialog_ui("table_1_0")
            table_1_1 = exportdialog_ui("table_1_1")
            table_1_2 = exportdialog_ui("table_1_2")
            assert table_1_0.text() == "3", "Code display OK"
            assert table_1_1.text() == "Workday", "Name display OK"
            assert table_1_2.text() == "AMEX", "Group name display OK"

            qtbot.mouseClick(button_export, Qt.LeftButton, Qt.NoModifier)

        # Trigger export on temporary file
        temp_file = QtCore.QTemporaryFile()
        if temp_file.open():
            patch_export(temp_file)

            # Accept file overwriting + confirm OK at end
            monkeypatch.setattr(
                QtWidgets.QMessageBox,
                "critical",
                lambda *args, **kwargs: QtWidgets.QMessageBox.Yes,
            )
            monkeypatch.setattr(
                QtWidgets.QMessageBox,
                "information",
                lambda *args, **kwargs: QtWidgets.QMessageBox.Ok,
            )

            # Display export dialog
            QtCore.QTimer.singleShot(0, handle_dialog)
            qtbot.mouseClick(app_ui("export_exec"), Qt.LeftButton, Qt.NoModifier)
            qtbot.waitUntil(
                lambda: open(temp_file.fileName(), "r", encoding="UTF-8").read() != "",
                timeout=1000,
            )

            # Check file contents
            file_contents = (
                open(temp_file.fileName(), "r", encoding="UTF-8").read().splitlines()
            )
            assert file_contents == ["3:Workday:AMEX"], "Data exported OK"

    def test_export_file_refuse_overwrite(
        self, app_ui, qtbot, monkeypatch, patch_export, exportdialog_ui
    ):
        # Choose values and confirm export
        def handle_dialog():
            # Get the different fields
            separator_field = exportdialog_ui("separator_field")
            table_0_0 = exportdialog_ui("table_0_0")
            table_0_1 = exportdialog_ui("table_0_1")
            table_0_2 = exportdialog_ui("table_0_2")
            button_export = exportdialog_ui("button_export")

            # Set values for export
            separator_field.setCurrentText(":")
            table_0_0.setCurrentIndex(table_0_0.findText("ID"))
            table_0_1.setCurrentIndex(table_0_1.findText("Name", Qt.MatchExactly))
            table_0_2.setCurrentIndex(table_0_2.findText("Name of group"))

            # Check display is updated
            table_1_0 = exportdialog_ui("table_1_0")
            table_1_1 = exportdialog_ui("table_1_1")
            table_1_2 = exportdialog_ui("table_1_2")
            assert table_1_0.text() == "3", "Code display OK"
            assert table_1_1.text() == "Workday", "Name display OK"
            assert table_1_2.text() == "AMEX", "Group name display OK"

            qtbot.mouseClick(button_export, Qt.LeftButton, Qt.NoModifier)

        # Trigger export on temporary file
        temp_file = QtCore.QTemporaryFile()
        if temp_file.open():
            patch_export(temp_file)
            assert (
                app_ui("export_path").text() == temp_file.fileName()
            ), "Export path updated OK"

            # Refuse file overwriting
            monkeypatch.setattr(
                QtWidgets.QMessageBox,
                "critical",
                lambda *args, **kwargs: QtWidgets.QMessageBox.No,
            )

            # Display export dialog
            QtCore.QTimer.singleShot(0, handle_dialog)
            qtbot.mouseClick(app_ui("export_exec"), Qt.LeftButton, Qt.NoModifier)

            # Check file contents
            file_contents = (
                open(temp_file.fileName(), "r", encoding="UTF-8").read().splitlines()
            )
            assert file_contents == [], "Data exported OK"

    def test_export_file_no_file_selected(
        self, app_ui, qtbot, monkeypatch, patch_export, exportdialog_ui
    ):
        # Cancel everything, this is not the purpose of the test
        def handle_dialog():
            button_cancel = exportdialog_ui("button_cancel")
            qtbot.mouseClick(button_cancel, Qt.LeftButton, Qt.NoModifier)

            assert (
                app_ui("export_path").text() == temp_file.fileName()
            ), "Export path updated OK"
            assert app_ui("errors").text() == "", "No error displayed"

        # Trigger export on temporary file
        temp_file = QtCore.QTemporaryFile()
        if temp_file.open():
            assert app_ui("export_path").text() == "", "Export path is empty at start"
            monkeypatch.setattr(
                QtWidgets.QFileDialog,
                "getSaveFileName",
                lambda *args, **kwargs: (temp_file.fileName(), ""),
            )

            # Display export dialog
            # This will trigger the selection of a file, and then we cancel the export
            # It should still update the "export file path"
            QtCore.QTimer.singleShot(0, handle_dialog)
            qtbot.mouseClick(app_ui("export_exec"), Qt.LeftButton, Qt.NoModifier)

    def test_export_file_no_file_selected_error(
        self, app_ui, qtbot, monkeypatch, patch_export, exportdialog_ui
    ):
        # Trigger export on temporary file
        temp_file = QtCore.QTemporaryFile()
        if temp_file.open():
            # Refuse file selection
            monkeypatch.setattr(
                QtWidgets.QFileDialog,
                "getSaveFileName",
                lambda *args, **kwargs: (None, ""),
            )
            assert app_ui("export_path").text() == "", "Export path stays empty"

            # Display export dialog
            qtbot.mouseClick(app_ui("export_exec"), Qt.LeftButton, Qt.NoModifier)

            # Check error display
            assert (
                app_ui("errors").text() == "Please select a file before exporting"
            ), "Error display OK"


if __name__ == "__main__":
    pytest.main(["-s", __file__])
