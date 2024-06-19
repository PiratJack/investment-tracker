import os
import sys
import pytest
import datetime
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "investmenttracker"))

from models.config import Config


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
    def importdialog_ui(self, qtbot, qapp):
        def get_ui(element):
            qtbot.waitUntil(lambda: qapp.activeWindow() is not None, timeout=800)
            dialog = qapp.activeWindow()

            if element == "dialog":
                return dialog
            elif element == "separator_title":
                return dialog.layout().itemAtPosition(0, 0).widget()
            elif element == "separator_field":
                return dialog.layout().itemAtPosition(0, 1).widget()
            elif element == "decimaldot_title":
                return dialog.layout().itemAtPosition(1, 0).widget()
            elif element == "decimaldot_field":
                return dialog.layout().itemAtPosition(1, 1).widget()
            elif element == "has_header":
                return dialog.layout().itemAtPosition(2, 0).widget()
            elif element == "errors":
                return dialog.layout().itemAtPosition(3, 0).widget()
            elif element == "table":
                return dialog.layout().itemAtPosition(4, 0).widget()
            elif element.startswith("table_"):
                row, col = element.split("_")[1:]
                if row == "0":
                    return get_ui("table").cellWidget(int(row), int(col))
                return get_ui("table").item(int(row), int(col))

            elif element == "buttonbox":
                return dialog.layout().itemAtPosition(5, 1).widget()
            elif element == "button_cancel":
                return get_ui("buttonbox").button(QtWidgets.QDialogButtonBox.Cancel)
            elif element == "button_ok":
                return get_ui("buttonbox").button(QtWidgets.QDialogButtonBox.Ok)

            raise ValueError(f"Field {element} could not be found")

        return get_ui

    @pytest.fixture
    def importresults_ui(self, qtbot, qapp):
        def get_ui(element):
            qtbot.waitUntil(lambda: qapp.activeWindow() is not None, timeout=500)
            qtbot.waitUntil(lambda: qapp.activeWindow().windowTitle() == "Load results")
            dialog = qapp.activeWindow()

            if element == "dialog":
                return dialog
            elif element == "table":
                return dialog.layout().itemAt(0).widget()
            elif element.startswith("table_"):
                row, col = element.split("_")[1:]
                return get_ui("table").item(int(row), int(col))

            elif element == "buttonbox":
                return dialog.layout().itemAt(1).widget()
            elif element == "button_ok":
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

    @pytest.fixture
    def patch_import(self, app_ui, qtbot, monkeypatch):
        def define_file(temp_file):
            monkeypatch.setattr(
                QtWidgets.QFileDialog,
                "getOpenFileName",
                lambda *args, **kwargs: (temp_file.fileName(), ""),
            )
            qtbot.mouseClick(app_ui("import_choose"), Qt.LeftButton, Qt.NoModifier)

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

    def test_export_choose_file(
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

    def test_export_choose_file_twice(
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

    def test_export_cancel(self, app_ui, qtbot, patch_export, exportdialog_ui):
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

    def test_export_confirm(
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

    def test_export_refuse_overwrite(
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

    def test_export_no_file_selected(
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

    def test_export_no_file_selected_error(
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

    def test_import_too_old(self, app_ui, app_db, app_mainwindow):
        # Set an old import date
        old_date = datetime.date.today() + datetime.timedelta(days=-45)
        app_db.config_set("import.last", old_date.strftime("%Y-%m-%d"))
        app_mainwindow.display_tab("Dashboard")

        # Check "Last import date" is updated
        assert app_ui("import_last_date").text() == old_date.strftime(
            "%d/%m/%Y"
        ), "Last import date OK"
        assert (
            app_ui("import_last_date").property("class") == "warning"
        ), "Last import date displayed OK"

    def test_import_inexistant_file(self, app_ui, qtbot, app_db, app_mainwindow):
        # Enter inexistant file in DB
        app_db.session.add_all([Config(name="import.filename", value="/test/path")])
        app_db.session.commit()
        app_db.config_get_by_name("import.filename")
        # Force reload of screen
        app_mainwindow.display_tab("Dashboard")

        # Check display of file path
        assert app_ui("import_path").text() == "/test/path", "Import path is inexistant"

        # Trigger import & check error
        qtbot.mouseClick(app_ui("import_exec"), Qt.LeftButton, Qt.NoModifier)
        assert app_ui("errors").text() == "The selected file does not exist", "Error OK"

    def test_import_no_file_selected(
        self, app_ui, qtbot, app_db, monkeypatch, importdialog_ui
    ):
        # Trigger import without selecting a file first
        temp_file = QtCore.QTemporaryFile()
        if temp_file.open():
            assert app_ui("import_path").text() == "", "Import path is empty at start"
            monkeypatch.setattr(
                QtWidgets.QFileDialog,
                "getOpenFileName",
                lambda *args, **kwargs: (temp_file.fileName(), ""),
            )

            # Display import dialog
            # This will trigger the selection of a file
            qtbot.mouseClick(app_ui("import_exec"), Qt.LeftButton, Qt.NoModifier)
            assert app_ui("errors").text() == "The selected file is empty", "Error OK"

    def test_import_no_file_selected_refuse_choosing(self, app_ui, qtbot, monkeypatch):
        # Refuse selecting a file
        monkeypatch.setattr(
            QtWidgets.QFileDialog,
            "getOpenFileName",
            lambda *args, **kwargs: (None, ""),
        )

        # Trigger import without selecting a file first
        qtbot.mouseClick(app_ui("import_exec"), Qt.LeftButton, Qt.NoModifier)
        assert (
            app_ui("errors").text() == "Please select a file before importing"
        ), "Error display OK"

    def test_import_unicode_error(self, app_ui, qtbot, app_db, monkeypatch):
        # Trigger import on wrongly encoded file
        temp_file = QtCore.QTemporaryFile()
        if temp_file.open():
            assert app_ui("import_path").text() == "", "Import path is empty at start"
            monkeypatch.setattr(
                QtWidgets.QFileDialog,
                "getOpenFileName",
                lambda *args, **kwargs: (temp_file.fileName(), ""),
            )

            temp_file.write(b"\x81")
            temp_file.close()

            # Trigger import
            qtbot.mouseClick(app_ui("import_exec"), Qt.LeftButton, Qt.NoModifier)
            assert (
                app_ui("errors").text()
                == "There was an error reading this file. Please choose another file."
            ), "Error display OK"

    def test_import_empty_file(self, app_ui, qtbot, patch_import):
        # Trigger import on temporary file
        temp_file = QtCore.QTemporaryFile()
        if temp_file.open():
            patch_import(temp_file)

            # Display import dialog
            qtbot.mouseClick(app_ui("import_exec"), Qt.LeftButton, Qt.NoModifier)
            assert app_ui("errors").text() == "The selected file is empty", "Error OK"

    def test_import_choose_file(self, app_ui, app_db, patch_import):
        # Create import file
        temp_file = QtCore.QTemporaryFile()
        if temp_file.open():
            # Trigger file selection
            patch_import(temp_file)

            # Check fields & DB are updated
            assert (
                app_ui("import_path").text() == temp_file.fileName()
            ), "Import path updated OK in UI"
            assert (
                app_db.config_get_by_name("import.filename").value
                == temp_file.fileName()
            ), "Import path updated OK in DB"

    def test_import_choose_file_twice(
        self, app_ui, app_db, patch_import, qtbot, monkeypatch
    ):
        # Create import file
        temp_file = QtCore.QTemporaryFile()
        if temp_file.open():
            patch_import(temp_file)

            # Trigger file selection a second time, with different value
            monkeypatch.setattr(
                QtWidgets.QFileDialog,
                "getOpenFileName",
                lambda *args, **kwargs: ("/tmp/temp.txt", ""),
            )
            qtbot.mouseClick(app_ui("import_choose"), Qt.LeftButton, Qt.NoModifier)

            # Check fields & DB are updated
            assert (
                app_ui("import_path").text() == "/tmp/temp.txt"
            ), "Import path updated OK in UI"
            assert (
                app_db.config_get_by_name("import.filename").value == "/tmp/temp.txt"
            ), "Import path updated OK in DB"

    def test_import_cancel(self, app_ui, app_db, patch_import, qtbot, importdialog_ui):
        def handle_dialog():
            # Get the different fields
            separator_title = importdialog_ui("separator_title")
            separator_field = importdialog_ui("separator_field")
            decimaldot_title = importdialog_ui("decimaldot_title")
            decimaldot_field = importdialog_ui("decimaldot_field")
            has_header = importdialog_ui("has_header")
            errors = importdialog_ui("errors")
            table = importdialog_ui("table")
            table_0_0 = importdialog_ui("table_0_0")
            table_0_1 = importdialog_ui("table_0_1")
            table_1_0 = importdialog_ui("table_1_0")
            table_1_1 = importdialog_ui("table_1_1")
            table_1_2 = importdialog_ui("table_1_2")
            table_1_3 = importdialog_ui("table_1_3")
            table_1_4 = importdialog_ui("table_1_4")
            button_ok = importdialog_ui("button_ok")
            button_cancel = importdialog_ui("button_cancel")

            assert isinstance(separator_title, QtWidgets.QLabel), "Separator title OK"
            assert separator_title.text() == "Field delimiter", "Separator title OK"
            assert isinstance(
                separator_field, QtWidgets.QComboBox
            ), "Field separator OK"
            assert separator_field.currentText() == ";", "Field separator value OK"
            assert isinstance(
                decimaldot_title, QtWidgets.QLabel
            ), "Decimal dot title OK"
            assert decimaldot_title.text() == "Decimal point", "Decimal dot title OK"
            assert isinstance(
                decimaldot_field, QtWidgets.QComboBox
            ), "Decimal dot field OK"
            assert decimaldot_field.currentText() == ".", "Decimal dot value field OK"
            assert isinstance(has_header, QtWidgets.QCheckBox), "Import header OK"
            assert has_header.text() == "The file has headers", "Import header OK"
            assert isinstance(errors, QtWidgets.QLabel), "Errors OK"
            assert (
                errors.text() == "Missing fields: Share, Date, Price, Currency, Source"
            ), "Errors OK"

            assert isinstance(table, QtWidgets.QTableWidget), "Table OK"
            assert isinstance(table_0_0, QtWidgets.QComboBox), "Table header OK"
            assert isinstance(table_0_1, QtWidgets.QComboBox), "Table header OK"
            assert table_0_0.currentText() == "", "Table header OK"
            assert table_0_1.currentText() == "", "Table header OK"
            assert table_1_0.text() == "WDAY", "Table row OK"
            assert table_1_1.text() == datetime.date.today().strftime(
                "%Y-%m-%d"
            ), "Table row OK"
            assert table_1_2.text() == "11", "Table row OK"
            assert table_1_3.text() == "USD", "Table row OK"
            assert table_1_4.text() == "Irrelevant", "Table row OK"

            assert isinstance(button_cancel, QtWidgets.QPushButton), "Cancel button OK"
            assert isinstance(button_ok, QtWidgets.QPushButton), "OK button OK"

            # Close dialog
            qtbot.mouseClick(button_cancel, Qt.LeftButton, Qt.NoModifier)

            # Check table has not changed
            assert app_ui("price_1_0") == "Workday", "No new value in price table"
            assert app_ui("price_1_6") == "0", "No new value in price table"
            assert app_ui("price_1_7") == "1", "No new value in price table"
            assert len(app_db.share_get_by_id(3).prices) == 1, "No new value in DB"

        # Create import file
        file_contents = [
            "WDAY",
            datetime.date.today().strftime("%Y-%m-%d"),
            "11",
            "USD",
            "Irrelevant",
        ]
        file_contents = bytearray(";".join(file_contents), "UTF-8")
        temp_file = QtCore.QTemporaryFile()
        if temp_file.open():
            patch_import(temp_file)
            temp_file.write(file_contents)
            temp_file.close()  # Needed for some reason, otherwise python sees empty file

            # Trigger the display of the dialog
            QtCore.QTimer.singleShot(0, handle_dialog)
            qtbot.mouseClick(app_ui("import_exec"), Qt.LeftButton, Qt.NoModifier)

    def test_import_confirm(
        self, app_ui, app_db, patch_import, qtbot, importdialog_ui, importresults_ui
    ):
        def handle_import_dialog():
            # Get the different fields
            errors = importdialog_ui("errors")
            table_0_0 = importdialog_ui("table_0_0")
            table_0_1 = importdialog_ui("table_0_1")
            table_0_2 = importdialog_ui("table_0_2")
            table_0_3 = importdialog_ui("table_0_3")
            table_0_4 = importdialog_ui("table_0_4")
            button_ok = importdialog_ui("button_ok")

            # Set import fields & check error display along the way
            table_0_0.setCurrentIndex(table_0_0.findText("Share"))
            assert (
                errors.text() == "Missing fields: Date, Price, Currency, Source"
            ), "Errors OK"
            table_0_1.setCurrentIndex(
                table_0_1.findText("Date (YYYY-MM-DD)", Qt.MatchExactly)
            )
            assert (
                errors.text() == "Missing fields: Price, Currency, Source"
            ), "Errors OK"
            table_0_2.setCurrentIndex(table_0_2.findText("Price", Qt.MatchExactly))
            assert errors.text() == "Missing fields: Currency, Source", "Errors OK"
            table_0_3.setCurrentIndex(table_0_2.findText("Currency", Qt.MatchExactly))
            assert errors.text() == "Missing fields: Source", "Errors OK"
            table_0_4.setCurrentIndex(table_0_2.findText("Source", Qt.MatchExactly))
            assert errors.text() == "", "Errors OK"

            # Confirm import
            QtCore.QTimer.singleShot(0, handle_import_results)
            qtbot.mouseClick(button_ok, Qt.LeftButton, Qt.NoModifier)

        def handle_import_results():
            # Get the different fields
            table_0_0 = importresults_ui("table_0_0")
            table_0_1 = importresults_ui("table_0_1")
            table_0_2 = importresults_ui("table_0_2")
            table_0_3 = importresults_ui("table_0_3")
            table_1_0 = importresults_ui("table_1_0")
            table_1_1 = importresults_ui("table_1_1")
            table_1_2 = importresults_ui("table_1_2")
            table_1_3 = importresults_ui("table_1_3")
            button_ok = importresults_ui("button_ok")

            assert table_0_0.text() == "Workday", "Import result OK"
            assert table_0_1.text() == "1", "Import result OK"
            assert table_0_2.text() == "0", "Import result OK"
            assert table_0_3.text() == "WDAY", "Import result OK"
            assert table_1_0.text() == "Total", "Import result OK"
            assert table_1_1.text() == "1", "Import result OK"
            assert table_1_2.text() == "0", "Import result OK"
            assert table_1_3 is None, "Import result OK"

            # Close dialog
            qtbot.mouseClick(button_ok, Qt.LeftButton, Qt.NoModifier)

            # Check table has been updated
            assert app_ui("price_1_0") == "Workday", "New price in price table"
            assert app_ui("price_1_6") == "0", "New price in price table"
            assert app_ui("price_1_7") == "2", "New price in price table"
            assert len(app_db.share_get_by_id(3).prices) == 2, "New price in DB"

            # Check "Last import date" is updated
            assert app_ui("import_last_date").text() == datetime.date.today().strftime(
                "%d/%m/%Y"
            ), "Last import date OK"

        # Create import file
        file_contents = [
            "WDAY",
            datetime.date.today().strftime("%Y-%m-%d"),
            "11",
            "USD",
            "Irrelevant",
        ]
        file_contents = bytearray(";".join(file_contents), "UTF-8")
        temp_file = QtCore.QTemporaryFile()
        if temp_file.open():
            patch_import(temp_file)
            temp_file.write(file_contents)
            temp_file.close()  # Needed for some reason, otherwise python sees empty file

            # Trigger the display of the dialog
            QtCore.QTimer.singleShot(0, handle_import_dialog)
            qtbot.mouseClick(app_ui("import_exec"), Qt.LeftButton, Qt.NoModifier)

    def test_import_twice(
        self,
        app_ui,
        app_db,
        qapp,
        patch_import,
        qtbot,
        importdialog_ui,
        importresults_ui,
    ):
        def handle_first_import_dialog():
            # Get the different fields
            errors = importdialog_ui("errors")
            table_0_0 = importdialog_ui("table_0_0")
            table_0_1 = importdialog_ui("table_0_1")
            table_0_2 = importdialog_ui("table_0_2")
            table_0_3 = importdialog_ui("table_0_3")
            table_0_4 = importdialog_ui("table_0_4")
            button_ok = importdialog_ui("button_ok")

            # Set import fields & check error display along the way
            table_0_0.setCurrentIndex(table_0_0.findText("Share"))
            table_0_1.setCurrentIndex(
                table_0_1.findText("Date (YYYY-MM-DD)", Qt.MatchExactly)
            )
            table_0_2.setCurrentIndex(table_0_2.findText("Price", Qt.MatchExactly))
            table_0_3.setCurrentIndex(table_0_2.findText("Currency", Qt.MatchExactly))
            table_0_4.setCurrentIndex(table_0_2.findText("Source", Qt.MatchExactly))
            assert errors.text() == "", "Errors OK"

            # Confirm import
            QtCore.QTimer.singleShot(0, handle_first_import_results)
            qtbot.mouseClick(button_ok, Qt.LeftButton, Qt.NoModifier)

            # Check configuration is saved
            assert (
                app_db.config_get_by_name("import.mapping").value
                == "share;%Y-%m-%d;price;currency;source"
            ), "Mapping is saved"

        def handle_second_import_dialog():
            # Get the different fields
            errors = importdialog_ui("errors")
            table_0_0 = importdialog_ui("table_0_0")
            table_0_1 = importdialog_ui("table_0_1")
            table_0_2 = importdialog_ui("table_0_2")
            table_0_3 = importdialog_ui("table_0_3")
            table_0_4 = importdialog_ui("table_0_4")
            button_ok = importdialog_ui("button_ok")

            # All import fields should be OK based on configuration saving
            assert table_0_0.currentText() == "Share", "Import config save OK"
            assert (
                table_0_1.currentText() == "Date (YYYY-MM-DD)"
            ), "Import config save OK"
            assert table_0_2.currentText() == "Price", "Import config save OK"
            assert table_0_3.currentText() == "Currency", "Import config save OK"
            assert table_0_4.currentText() == "Source", "Import config save OK"
            assert errors.text() == "", "Errors OK"

            # Confirm import
            QtCore.QTimer.singleShot(0, handle_second_import_results)
            qtbot.mouseClick(button_ok, Qt.LeftButton, Qt.NoModifier)

        def handle_first_import_results():
            # Check the different fields
            assert importresults_ui("table_0_0").text() == "Workday", "Import result OK"
            assert importresults_ui("table_0_1").text() == "1", "Import result OK"
            assert importresults_ui("table_0_2").text() == "0", "Import result OK"
            assert importresults_ui("table_0_3").text() == "WDAY", "Import result OK"
            assert importresults_ui("table_1_0").text() == "Total", "Import result OK"
            assert importresults_ui("table_1_1").text() == "1", "Import result OK"
            assert importresults_ui("table_1_2").text() == "0", "Import result OK"
            assert importresults_ui("table_1_3") is None, "Import result OK"

            # Close dialog
            button_ok = importresults_ui("button_ok")
            qtbot.mouseClick(button_ok, Qt.LeftButton, Qt.NoModifier)

            # Check table has been updated
            assert app_ui("price_1_0") == "Workday", "New price in price table"
            assert app_ui("price_1_6") == "0", "New price in price table"
            assert app_ui("price_1_7") == "2", "New price in price table"
            assert len(app_db.share_get_by_id(3).prices) == 2, "New price in DB"

            # Trigger the second display of the dialog
            QtCore.QTimer.singleShot(0, handle_second_import_dialog)
            qtbot.mouseClick(app_ui("import_exec"), Qt.LeftButton, Qt.NoModifier)

        def handle_second_import_results():
            # Check the different fields
            assert importresults_ui("table_0_0").text() == "Workday", "Import result OK"
            assert importresults_ui("table_0_1").text() == "0", "Import result OK"
            assert importresults_ui("table_0_2").text() == "1", "Import result OK"
            assert importresults_ui("table_0_3").text() == "WDAY", "Import result OK"
            assert importresults_ui("table_1_0").text() == "Total", "Import result OK"
            assert importresults_ui("table_1_1").text() == "0", "Import result OK"
            assert importresults_ui("table_1_2").text() == "1", "Import result OK"
            assert importresults_ui("table_1_3") is None, "Import result OK"

            # Close dialog
            button_ok = importresults_ui("button_ok")
            qtbot.mouseClick(button_ok, Qt.LeftButton, Qt.NoModifier)

            # Check table has been updated
            assert app_ui("price_1_0") == "Workday", "No new price in price table"
            assert app_ui("price_1_6") == "0", "No new price in price table"
            assert app_ui("price_1_7") == "2", "No new price in price table"
            assert len(app_db.share_get_by_id(3).prices) == 2, "No new price in DB"

        # Create import file
        file_contents = [
            "WDAY",
            datetime.date.today().strftime("%Y-%m-%d"),
            "11",
            "USD",
            "Irrelevant",
        ]
        file_contents = bytearray(";".join(file_contents), "UTF-8")
        temp_file = QtCore.QTemporaryFile()
        if temp_file.open():
            patch_import(temp_file)
            temp_file.write(file_contents)
            temp_file.close()  # Needed for some reason, otherwise python sees empty file

            # Trigger the display of the dialog
            QtCore.QTimer.singleShot(0, handle_first_import_dialog)
            qtbot.mouseClick(app_ui("import_exec"), Qt.LeftButton, Qt.NoModifier)

            # This prevents the DB from being deleted too early
            qtbot.wait(500)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
