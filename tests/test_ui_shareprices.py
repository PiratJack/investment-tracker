import os
import sys
import pytest
import datetime
import sqlalchemy.orm
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
            elif element.startswith("tableeditfield_"):
                row = int(element.split("_")[1])
                column = int(element.split("_")[2])
                index = get_ui("table").model.index(row, column)
                return get_ui("table").indexWidget(index)

            raise ValueError(f"Field {element} could not be found")

        return get_ui

    def enter_value_in_field(self, item_name, value, app_ui, qtbot):
        col = {
            "share": 0,
            "date": 2,
            "price": 3,
            "currency": 4,
            "source": 5,
        }[item_name]

        # Double-click on table to allow edition
        y_position = app_ui("table").rowViewportPosition(0) + 5
        x_position = app_ui("table").columnViewportPosition(col) + 10
        point = QtCore.QPoint(x_position, y_position)
        qtbot.mouseClick(
            app_ui("table").viewport(), Qt.LeftButton, Qt.NoModifier, point
        )
        qtbot.mouseDClick(
            app_ui("table").viewport(), Qt.LeftButton, Qt.NoModifier, point
        )

        # Enter new value
        if item_name == "date":
            # I couldn't find how to do it by typing keys, so instead the date is set programmatically
            app_ui("tableeditfield_0_" + str(col)).setDate(value)
        else:
            qtbot.keyClicks(app_ui("tableeditfield_0_" + str(col)), str(value))

        # Typing "Enter" doesn't seem to be enough ==> click outside the widget to validate
        x_position = app_ui("table").columnViewportPosition(0) + 10
        y_position = app_ui("table").rowViewportPosition(1) + 5
        point = QtCore.QPoint(x_position, y_position)
        qtbot.mouseClick(
            app_ui("table").viewport(), Qt.LeftButton, Qt.NoModifier, point
        )

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

    def test_shareprices_select_share_via_dropdown(self, app_ui, qtbot):
        # Select a share
        qtbot.keyClicks(app_ui("share_field"), "Accenture")

        # Check table layout
        assert isinstance(app_ui("table"), QtWidgets.QTableView), "Table type is OK"
        index = app_ui("table").model.index(1, 1)
        assert app_ui("table").model.rowCount(index) == 2, "Row count OK"

    def test_shareprices_select_share_set_filters_int(self, app_ui, qtbot):
        # Select a share via its ID
        app_ui("table").set_filters(share=3)

        # Check table layout
        assert isinstance(app_ui("table"), QtWidgets.QTableView), "Table type is OK"
        index = app_ui("table").model.index(1, 1)
        assert app_ui("table").model.rowCount(index) == 2, "Row count OK"

    def test_shareprices_select_share_set_filters_Share(self, app_ui, qtbot, app_db):
        # Select a share via its ID
        app_ui("table").set_filters(share=app_db.share_get_by_id(3))

        # Check table layout
        assert isinstance(app_ui("table"), QtWidgets.QTableView), "Table type is OK"
        index = app_ui("table").model.index(1, 1)
        assert app_ui("table").model.rowCount(index) == 2, "Row count OK"

    def test_shareprices_select_date_via_user_input(self, app_ui, qtbot):
        # Select a date
        # I couldn't find how to do it by typing keys, so instead the date is set programmatically
        # #qtbot.keyClicks(app_ui("tableeditfield_0_2"), "01/04/2024")
        app_ui("date_field").setDate(QtCore.QDate(2020, 4, 1))

        # Check table layout
        index = app_ui("table").model.index(1, 1)
        assert app_ui("table").model.rowCount(index) == 7, "Row count OK"

    def test_shareprices_select_date_via_set_filters_datetime(self, app_ui, qtbot):
        # Select a date
        app_ui("table").set_filters(date=datetime.datetime(2020, 4, 1))

        # Check table layout
        index = app_ui("table").model.index(1, 1)
        assert app_ui("table").model.rowCount(index) == 7, "Row count OK"

    def test_shareprices_select_date_via_set_filters_str(self, app_ui, qtbot):
        # Select a date
        app_ui("table").set_filters(date="2020-04-01")

        # Check table layout
        index = app_ui("table").model.index(1, 1)
        assert app_ui("table").model.rowCount(index) == 7, "Row count OK"

    def test_shareprices_select_date_via_set_filters_int(self, app_ui, qtbot):
        # Select a date
        app_ui("table").set_filters(date=3)

        # Check table layout
        index = app_ui("table").model.index(1, 1)
        assert app_ui("table").model.rowCount(index) == 8, "Row count OK"

    def test_shareprices_select_date_via_set_filters_variant(self, app_ui, qtbot):
        # Select a date
        app_ui("table").set_filters(date=QtWidgets.QComboBox)

        # Check table layout
        index = app_ui("table").model.index(1, 1)
        assert app_ui("table").model.rowCount(index) == 8, "Row count OK"

    def test_shareprices_select_date_via_set_filters_minus_one(self, app_ui, qtbot):
        # Select a date
        app_ui("table").set_filters(date=-1)

        # Check table layout
        index = app_ui("table").model.index(1, 1)
        assert app_ui("table").model.rowCount(index) == 8, "Row count OK"

    def test_shareprices_click_table(self, app_ui, qtbot):
        # Select a share
        qtbot.keyClicks(app_ui("share_field"), "Accenture")

        # Click on table > triggers saving / restoring selection
        x_position = app_ui("table").columnViewportPosition(1)
        y_position = app_ui("table").rowViewportPosition(1)
        point = QtCore.QPoint(x_position, y_position)
        qtbot.mouseClick(
            app_ui("table").viewport(), Qt.LeftButton, Qt.NoModifier, point
        )
        # Click on non-editable field
        x_position = app_ui("table").columnViewportPosition(5)
        point = QtCore.QPoint(x_position, y_position)
        qtbot.mouseClick(
            app_ui("table").viewport(), Qt.LeftButton, Qt.NoModifier, point
        )

    def test_shareprices_edit_share(self, app_ui, qtbot, app_db):
        # Get displayed price
        shareprice = app_db.share_price_get_by_id(3)

        # Enter new value
        self.enter_value_in_field("share", "Workday", app_ui, qtbot)

        # Check database is updated
        assert shareprice.share.name == "Workday", "Share price share is modified"

    def test_shareprices_edit_date(self, app_ui, qtbot, app_db):
        # Get displayed price
        shareprice = app_db.share_price_get_by_id(3)

        # Enter new value
        self.enter_value_in_field("date", QtCore.QDate.currentDate(), app_ui, qtbot)

        # Check database is updated
        assert shareprice.date == datetime.date.today(), "Share price date is modified"

    def test_shareprices_edit_price(self, app_ui, qtbot, app_db):
        # Get displayed price
        shareprice = app_db.share_price_get_by_id(3)

        # Enter new value
        self.enter_value_in_field("price", 15, app_ui, qtbot)

        # Check database is updated
        assert shareprice.price == 15, "Share price value is modified"

    def test_shareprices_edit_currency(self, app_ui, qtbot, app_db):
        # Get displayed price
        shareprice = app_db.share_price_get_by_id(3)

        # Enter new value
        self.enter_value_in_field("currency", "Dollar", app_ui, qtbot)

        # Check database is updated
        assert shareprice.currency.name == "Dollar", "Share price currency is modified"

    def test_shareprices_edit_currency_bad_value(self, app_ui, qtbot, app_db):
        # Get displayed price
        shareprice = app_db.share_price_get_by_id(3)

        # Enter new value
        self.enter_value_in_field("currency", "Accenture", app_ui, qtbot)

        # Check database is updated
        assert shareprice.currency.name == "Euro", "Price currency is NOT modified"

    def test_shareprices_edit_source(self, app_ui, qtbot, app_db):
        # Get displayed price
        shareprice = app_db.share_price_get_by_id(3)

        # Enter new value
        self.enter_value_in_field("source", "New", app_ui, qtbot)

        # Check database is updated
        assert shareprice.source == "New", "Share price source is modified"

    def test_shareprices_delete_cancel(self, app_ui, qtbot, app_db, monkeypatch):
        # Get displayed price
        shareprice = app_db.share_price_get_by_id(3)
        # Setup monkeypatch: cancel deletion
        monkeypatch.setattr(
            QtWidgets.QMessageBox,
            "critical",
            lambda *args, **kwargs: QtWidgets.QMessageBox.No,
        )

        # Double-click on deletion
        x_position = app_ui("table").columnViewportPosition(6) + 10
        y_position = app_ui("table").rowViewportPosition(0) + 5
        point = QtCore.QPoint(x_position, y_position)
        qtbot.mouseClick(
            app_ui("table").viewport(), Qt.LeftButton, Qt.NoModifier, point
        )
        qtbot.mouseDClick(
            app_ui("table").viewport(), Qt.LeftButton, Qt.NoModifier, point
        )

        # Check database is unchanged
        index = app_ui("table").model.index(1, 1)
        assert app_ui("table").model.rowCount(index) == 5, "Row count OK"
        assert shareprice is not None, "Share price remains unchanged"

    def test_shareprices_delete_confirm(self, app_ui, qtbot, app_db, monkeypatch):
        # Setup monkeypatch: cancel deletion
        monkeypatch.setattr(
            QtWidgets.QMessageBox,
            "critical",
            lambda *args, **kwargs: QtWidgets.QMessageBox.Yes,
        )

        # Double-click on deletion
        x_position = app_ui("table").columnViewportPosition(6) + 10
        y_position = app_ui("table").rowViewportPosition(0) + 5
        point = QtCore.QPoint(x_position, y_position)
        qtbot.mouseClick(
            app_ui("table").viewport(), Qt.LeftButton, Qt.NoModifier, point
        )
        qtbot.mouseDClick(
            app_ui("table").viewport(), Qt.LeftButton, Qt.NoModifier, point
        )

        # Check database is unchanged
        index = app_ui("table").model.index(1, 1)
        assert app_ui("table").model.rowCount(index) == 4, "Row count OK"
        with pytest.raises(sqlalchemy.orm.exc.NoResultFound):
            app_db.share_price_get_by_id(3)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
