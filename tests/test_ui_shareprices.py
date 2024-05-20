import os
import sys
import pytest
import datetime
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "investmenttracker"))


class TestUiSharePrices:
    @pytest.fixture
    def app_shareprices(self, app_mainwindow):
        app_mainwindow.display_tab("Share Prices")

        yield app_mainwindow.layout.currentWidget()

    @pytest.fixture
    def app_ui(self, app_mainwindow, app_shareprices):
        def get_ui(element):
            # Main window
            if element == "mainwindow":
                return app_mainwindow

            # Overall elements
            if element == "layout":
                return app_shareprices.layout

            # Top: Share selection dropdown
            if element == "form_group":
                return app_shareprices.layout.itemAt(0).widget()
            elif element == "share_label":
                role = QtWidgets.QFormLayout.LabelRole
                return get_ui("form_group").layout().itemAt(0, role).widget()
            elif element == "share_field":
                role = QtWidgets.QFormLayout.FieldRole
                return get_ui("form_group").layout().itemAt(0, role).widget()

            # Middle: Share selection dropdown
            elif element == "date_label":
                role = QtWidgets.QFormLayout.LabelRole
                return get_ui("form_group").layout().itemAt(1, role).widget()
            elif element == "date_field":
                role = QtWidgets.QFormLayout.FieldRole
                return get_ui("form_group").layout().itemAt(1, role).widget()

            # Bottom: table
            elif element == "table":
                return app_shareprices.layout.itemAt(1).widget()
            elif element.startswith("table_"):
                row = int(element.split("_")[1])
                column = int(element.split("_")[2])
                index = get_ui("table").model.index(row, column)
                return get_ui("table").model.data(index, Qt.DisplayRole)
            elif element.startswith("tableedit_"):
                row = int(element.split("_")[1])
                column = int(element.split("_")[2])
                index = get_ui("table").model.index(row, column)
                return get_ui("table").model.data(index, Qt.EditRole)

            raise ValueError(f"Field {element} could not be found")

        return get_ui

    def test_shareprices_display(self, app_ui):
        # Check overall structure
        assert isinstance(app_ui("layout"), QtWidgets.QVBoxLayout), "Layout is OK"
        assert app_ui("layout").count() == 2, "Count of elements is OK"
        assert isinstance(
            app_ui("form_group").layout(), QtWidgets.QFormLayout
        ), "Layout is OK"

        # Check share dropdown
        assert isinstance(app_ui("share_label"), QtWidgets.QLabel), "Share label OK"
        assert app_ui("share_label").text() == "Share", "Share label OK"
        assert isinstance(app_ui("share_field"), QtWidgets.QComboBox), "Share field OK"
        assert app_ui("share_field").count() == 12, "Combobox count elements OK"
        assert app_ui("share_field").itemText(0) == "All", "Combobox item 1 OK"
        assert app_ui("share_field").itemText(1) == "AMEX", "Combobox item 2 OK"
        assert (
            app_ui("share_field").itemText(2) == "Accenture (NYSE:ACN)"
        ), "Combobox item 3 OK"

        # Check date
        assert isinstance(app_ui("date_label"), QtWidgets.QLabel), "Date label OK"
        assert app_ui("date_label").text() == "Date", "Date label OK"
        assert isinstance(app_ui("date_field"), QtWidgets.QDateEdit), "Date field OK"
        date_label = (
            QtCore.QDate.currentDate().addMonths(-1).toString(Qt.SystemLocaleShortDate)
        )
        assert app_ui("date_field").text() == date_label, "Date field OK"

        # Check table layout
        assert isinstance(app_ui("table"), QtWidgets.QTableView), "Table type is OK"
        index = app_ui("table").model.index(1, 1)
        assert app_ui("table").model.columnCount(index) == 7, "Column count OK"
        assert app_ui("table").model.rowCount(index) == 5, "Row count OK"

        # Check table layout for a share price
        assert app_ui("table_0_0") == "Accenture", "Price share OK"
        assert app_ui("table_0_1") == 3, "Price ID OK"
        date_label = QtCore.QDate.currentDate().addDays(-5)
        assert app_ui("table_0_2") == date_label, "Price date OK"
        assert app_ui("table_0_3") == "10,00000", "Price value OK"
        assert app_ui("table_0_4") == "Euro (EUR)", "Price currency OK"
        assert app_ui("table_0_5") == "Lambda", "Price source OK"
        index = app_ui("table").model.index(0, 6)
        assert (
            app_ui("table").model.data(index, Qt.DecorationRole).typeName() == "QIcon"
        ), "Delete icon displayed"
        # Check text alignment (not really useful...)
        index = app_ui("table").model.index(0, 5)
        actual_alignment = app_ui("table").model.data(index, Qt.TextAlignmentRole)
        assert actual_alignment and Qt.AlignRight == Qt.AlignRight, "Text alignment OK"
        assert (
            app_ui("table").model.data(index, Qt.WhatsThisRole).isNull
        ), "WhatsThis is empty"

        # Check table layout for adding a share price
        assert app_ui("table_4_0") == "Add a share price", "Price share OK"
        assert app_ui("table_4_1").isNull(), "Price ID OK"
        assert app_ui("table_4_2").isNull(), "Price date OK"
        assert app_ui("table_4_3").isNull(), "Price value OK"
        assert app_ui("table_4_4").isNull(), "Price currency OK"
        assert app_ui("table_4_5").isNull(), "Price source OK"
        assert app_ui("table_4_6").isNull(), "Price icon OK"

        # Check table layout for editing a share price
        assert app_ui("tableedit_0_0") == 2, "Price share ID OK"
        assert app_ui("tableedit_0_1") is None, "Price ID OK"
        date_label = QtCore.QDate.currentDate().addDays(-5)
        assert app_ui("tableedit_0_2") == date_label, "Price date OK"
        assert app_ui("tableedit_0_3") == 10, "Price value OK"
        assert app_ui("tableedit_0_4") == 5, "Price currency ID OK"
        assert app_ui("tableedit_0_5") == "Lambda", "Price source OK"

        # Check table layout for adding a share price (Edit version)
        # Each time it adds a new row, so it has to increment
        assert app_ui("tableedit_4_0") == 0, "Price share OK"
        assert app_ui("tableedit_5_1") is None, "Price ID OK"
        assert app_ui("tableedit_6_2").date() == datetime.date.today(), "Price date OK"
        assert app_ui("tableedit_7_3") == 0, "Price value OK"
        assert app_ui("tableedit_8_4") == 0, "Price currency OK"
        assert app_ui("tableedit_9_5") == "", "Price source OK"
        assert app_ui("tableedit_10_6") is None, "Price icon OK"


if __name__ == "__main__":
    pytest.main(["-s", __file__])
