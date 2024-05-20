import os
import sys
import pytest
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "investmenttracker"))


class TestUiTransactions:
    @pytest.fixture
    def app_transactions(self, app_mainwindow):
        app_mainwindow.display_tab("Transactions")

        yield app_mainwindow.layout.currentWidget()

    @pytest.fixture
    def app_ui(self, app_mainwindow, app_transactions):
        def get_ui(element):
            # Main window
            if element == "mainwindow":
                return app_mainwindow

            # Overall elements
            if element == "layout":
                return app_transactions.layout

            # Left: Account tree & checkboxes
            elif element == "left_column":
                return app_transactions.layout.itemAt(0).widget()
            elif element == "account_tree":
                return get_ui("left_column").layout.itemAt(0).widget()

            # Left: Account tree > Account with lots of history
            elif element == "account_history":
                return get_ui("account_tree").topLevelItem(0)
            elif element.startswith("account_history_"):
                column = int(element.split("_")[-1])
                return get_ui("account_history").data(column, Qt.DisplayRole)

            elif element == "account_historyACN":
                return get_ui("account_history").child(0)
            elif element.startswith("account_historyACN_"):
                column = int(element.split("_")[-1])
                return get_ui("account_historyACN").data(column, Qt.DisplayRole)

            # Left: Account tree > Account with no history
            elif element == "account_no_history":
                return get_ui("account_tree").topLevelItem(1)

            # Left: Account tree > Disabled account
            elif element == "disabled_account":
                if get_ui("display_disabled").isChecked():
                    return get_ui("account_tree").topLevelItem(2)
            elif element.startswith("disabled_account_"):
                column = int(element.split("_")[-1])
                return get_ui("disabled_account").data(column, Qt.DisplayRole)

            # Left: Account tree > Hidden account
            elif element == "hidden_account":
                if get_ui("display_hidden").isChecked():
                    position = 3 if get_ui("display_disabled").isChecked() else 2
                    return get_ui("account_tree").topLevelItem(position)
            elif element.startswith("hidden_account_"):
                column = int(element.split("_")[-1])
                return get_ui("hidden_account").data(column, Qt.DisplayRole)

            # Left: Account tree > Main account
            elif element == "main_account":
                return get_ui("account_tree").topLevelItem(3)

            # Left: Checkboxes
            elif element == "display_hidden":
                return get_ui("left_column").layout.itemAt(1).widget()
            elif element == "display_disabled":
                return get_ui("left_column").layout.itemAt(2).widget()

            # Right: Transactions table
            elif element == "right_column":
                return app_transactions.layout.itemAt(1).widget()
            elif element == "table":
                return get_ui("right_column").layout.itemAt(0).widget()
            elif element.startswith("table_"):
                row = int(element.split("_")[1])
                column = int(element.split("_")[2])
                index = get_ui("table").model.index(row, column)
                return get_ui("table").model.data(index, Qt.DisplayRole)

            raise ValueError(f"Field {element} could not be found")

        return get_ui

    def click_tree_item(self, item, qtbot, app_ui):
        if item.parent():
            item.parent().setExpanded(True)
        topleft = app_ui("account_tree").visualItemRect(item).topLeft()
        qtbot.mouseClick(
            app_ui("account_tree").viewport(), Qt.LeftButton, Qt.NoModifier, topleft
        )

    def test_transactions_display(self, app_ui):
        # Check overall structure
        assert isinstance(app_ui("layout"), QtWidgets.QHBoxLayout), "Layout is OK"
        assert app_ui("layout").count() == 2, "Count of elements is OK"
        assert isinstance(
            app_ui("left_column").layout, QtWidgets.QVBoxLayout
        ), "Left column layout is OK"
        assert (
            app_ui("left_column").layout.count() == 3
        ), "Left column count of elements is OK"

        # Check tree
        assert isinstance(
            app_ui("account_tree"), QtWidgets.QTreeWidget
        ), "The tree is a tree"
        assert (
            app_ui("account_tree").topLevelItemCount() == 3
        ), "Count of elements is OK"

        assert (
            app_ui("account_history_0") == "Account with lots of history"
        ), "Account name OK"
        assert app_ui("account_history_1") == "account", "Account type OK"
        assert app_ui("account_history_2") == "4", "Account ID OK"

        assert app_ui("account_historyACN_0") == "Accenture", "Share name OK"
        assert app_ui("account_historyACN_1") == "share", "Share type OK"
        assert app_ui("account_historyACN_2") == "2", "Share ID OK"

        # Check checkboxes
        assert isinstance(
            app_ui("display_hidden"), QtWidgets.QCheckBox
        ), "Display hidden is a checkbox"
        assert isinstance(
            app_ui("display_disabled"), QtWidgets.QCheckBox
        ), "Display disabled is a checkbox"

        # Check table layout
        assert isinstance(app_ui("table"), QtWidgets.QTableView), "Table type is OK"
        index = app_ui("table").model.index(1, 1)
        assert app_ui("table").model.columnCount(index) == 13, "Column count OK"
        assert app_ui("table").model.rowCount(index) == 1, "Row count OK"
        assert app_ui("table_0_0") == "Add a transaction", "Add transaction label OK"
        assert app_ui("table_0_1").isNull(), "Add transaction ID OK"
        assert app_ui("table_0_2").isNull(), "Add transaction date OK"
        assert app_ui("table_0_3").isNull(), "Add transaction type OK"
        assert app_ui("table_0_4").isNull(), "Add transaction label OK"
        assert app_ui("table_0_5").isNull(), "Add transaction # shares OK"
        assert app_ui("table_0_6").isNull(), "Add transaction share name OK"
        assert app_ui("table_0_7").isNull(), "Add transaction Balance (shares) OK"
        assert app_ui("table_0_8").isNull(), "Add transaction unit price OK"
        assert app_ui("table_0_9").isNull(), "Add transaction # cash OK"
        assert app_ui("table_0_10").isNull(), "Add transaction Balance (cash) OK"

    def test_transactions_display_hidden(self, app_ui, qtbot):
        # Click on checkbox
        # This offset is just a guess to end up on the checkbox
        offset = QtCore.QPoint(2, app_ui("display_hidden").height() // 2)
        qtbot.mouseClick(app_ui("display_hidden"), Qt.LeftButton, Qt.NoModifier, offset)
        # Check hidden account is displayed
        assert (
            app_ui("account_tree").topLevelItemCount() == 4
        ), "Count of elements is OK"

        assert app_ui("hidden_account_0") == "Hidden account", "Account name OK"
        assert app_ui("hidden_account_1") == "account", "Account type OK"
        assert app_ui("hidden_account_2") == "2", "Account ID OK"

    def test_transactions_display_disabled(self, app_ui, qtbot):
        # Click on checkbox
        # This offset is just a guess to end up on the checkbox
        offset = QtCore.QPoint(2, app_ui("display_disabled").height() // 2)
        qtbot.mouseClick(
            app_ui("display_disabled"), Qt.LeftButton, Qt.NoModifier, offset
        )
        # Check hidden account is displayed
        assert (
            app_ui("account_tree").topLevelItemCount() == 4
        ), "Count of elements is OK"

        assert app_ui("disabled_account_0") == "Disabled account", "Account name OK"
        assert app_ui("disabled_account_1") == "account", "Account type OK"
        assert app_ui("disabled_account_2") == "3", "Account ID OK"

    def test_transactions_display_hidden_and_disabled(self, app_ui, qtbot):
        # Click on checkbox
        # This offset is just a guess to end up on the checkbox
        offset = QtCore.QPoint(2, app_ui("display_disabled").height() // 2)
        qtbot.mouseClick(
            app_ui("display_disabled"), Qt.LeftButton, Qt.NoModifier, offset
        )
        qtbot.mouseClick(app_ui("display_hidden"), Qt.LeftButton, Qt.NoModifier, offset)
        # Check hidden account is displayed
        assert (
            app_ui("account_tree").topLevelItemCount() == 5
        ), "Count of elements is OK"

        assert app_ui("hidden_account_0") == "Hidden account", "Account name OK"
        assert app_ui("hidden_account_1") == "account", "Account type OK"
        assert app_ui("hidden_account_2") == "2", "Account ID OK"

        assert app_ui("disabled_account_0") == "Disabled account", "Account name OK"
        assert app_ui("disabled_account_1") == "account", "Account type OK"
        assert app_ui("disabled_account_2") == "3", "Account ID OK"

    def test_transactions_click_account(self, app_ui, qtbot):
        # Click on account
        self.click_tree_item(app_ui("account_history"), qtbot, app_ui)
        index = app_ui("table").model.index(1, 1)
        # Check number of transactions displayed
        assert app_ui("table").model.columnCount(index) == 13, "Column count OK"
        assert app_ui("table").model.rowCount(index) == 6, "Row count OK"

        assert app_ui("table_0_0") == "Account with lots of history", "Account name OK"
        assert app_ui("table_0_1") == 10, "Transaction ID OK"
        assert app_ui("table_0_2") == QtCore.QDate(2020, 4, 1), "Transaction date OK"
        assert app_ui("table_0_3") == "Cash deposit", "Transaction type OK"
        assert app_ui("table_0_4") == "First investment", "Transaction label OK"
        assert app_ui("table_0_5") == "-", "Transaction # shares OK"
        assert app_ui("table_0_6") == "-", "Transaction share name OK"
        assert app_ui("table_0_7") == "-", "Transaction Balance (shares) OK"
        assert app_ui("table_0_8") == "-", "Transaction unit price OK"
        assert app_ui("table_0_9") == "10\u202f000,00 EUR", "Transaction # cash OK"
        assert (
            app_ui("table_0_10") == "10\u202f000,00 EUR"
        ), "Transaction Balance (cash) OK"

        assert app_ui("table_1_0") == "Account with lots of history", "Account name OK"
        assert app_ui("table_1_1") == 11, "Transaction ID OK"
        assert app_ui("table_1_2") == QtCore.QDate(2020, 4, 1), "Transaction date OK"
        assert app_ui("table_1_3") == "Asset buy / subscription", "Transaction type OK"
        assert app_ui("table_1_4") == "Buy Accenture", "Transaction label OK"
        assert app_ui("table_1_5") == "10,00000", "Transaction # shares OK"
        assert (
            app_ui("table_1_6") == "Accenture (NYSE:ACN)"
        ), "Transaction share name OK"
        assert app_ui("table_1_7") == "10,00000", "Transaction Balance (shares) OK"
        assert app_ui("table_1_8") == "200,00 EUR", "Transaction unit price OK"
        assert app_ui("table_1_9") == "-2\u202f000,00 EUR", "Transaction # cash OK"
        assert (
            app_ui("table_1_10") == "8\u202f000,00 EUR"
        ), "Transaction Balance (cash) OK"

    def test_transactions_click_share(self, app_ui, qtbot):
        # Click on share
        self.click_tree_item(app_ui("account_historyACN"), qtbot, app_ui)
        index = app_ui("table").model.index(1, 1)
        # Check number of transactions displayed
        assert app_ui("table").model.columnCount(index) == 13, "Column count OK"
        assert app_ui("table").model.rowCount(index) == 3, "Row count OK"

        assert app_ui("table_0_0") == "Account with lots of history", "Account name OK"
        assert app_ui("table_0_1") == 11, "Transaction ID OK"
        assert app_ui("table_0_2") == QtCore.QDate(2020, 4, 1), "Transaction date OK"
        assert app_ui("table_0_3") == "Asset buy / subscription", "Transaction type OK"
        assert app_ui("table_0_4") == "Buy Accenture", "Transaction label OK"
        assert app_ui("table_0_5") == "10,00000", "Transaction # shares OK"
        assert (
            app_ui("table_0_6") == "Accenture (NYSE:ACN)"
        ), "Transaction share name OK"
        assert app_ui("table_0_7") == "10,00000", "Transaction Balance (shares) OK"
        assert app_ui("table_0_8") == "200,00 EUR", "Transaction unit price OK"
        assert app_ui("table_0_9") == "-2\u202f000,00 EUR", "Transaction # cash OK"
        assert (
            app_ui("table_0_10") == "8\u202f000,00 EUR"
        ), "Transaction Balance (cash) OK"

        # Icons can't really be checked thoroughly
        index = app_ui("table").model.index(0, 11)
        assert (
            app_ui("table").model.data(index, Qt.DecorationRole).typeName() == "QIcon"
        ), "Duplicate icon displayed"
        index = app_ui("table").model.index(0, 12)
        assert (
            app_ui("table").model.data(index, Qt.DecorationRole).typeName() == "QIcon"
        ), "Delete icon displayed"
        assert (
            app_ui("table").model.data(index, Qt.WhatsThisRole).isNull()
        ), "WhatsThis is empty"

        # Check text alignment (not really useful...)
        index = app_ui("table").model.index(0, 5)
        actual_alignment = app_ui("table").model.data(index, Qt.TextAlignmentRole)
        assert actual_alignment and Qt.AlignRight == Qt.AlignRight, "Text alignment OK"

    def test_transactions_click_table(self, app_ui, qtbot):
        # Click on account & on share
        self.click_tree_item(app_ui("account_history"), qtbot, app_ui)
        self.click_tree_item(app_ui("account_historyACN"), qtbot, app_ui)

        # Click on table > triggers saving / restoring selection
        x_position = app_ui("table").columnViewportPosition(5)
        y_position = app_ui("table").rowViewportPosition(1)
        point = QtCore.QPoint(x_position, y_position)
        qtbot.mouseClick(
            app_ui("table").viewport(), Qt.LeftButton, Qt.NoModifier, point
        )


if __name__ == "__main__":
    pytest.main(["-s", __file__])
