import os
import sys
import datetime
import pytest
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "investmenttracker"))


class TestUiAccounts:
    @pytest.fixture
    def app_accounts(self, app_mainwindow):
        app_mainwindow.display_tab("Accounts")

        yield app_mainwindow.layout.currentWidget()

    @pytest.fixture
    def app_ui(self, app_mainwindow, app_accounts):
        def get_ui(element):
            # Main window
            if element == "mainwindow":
                return app_mainwindow

            # Overall elements
            if element == "layout":
                return app_accounts.layout

            # Top: Shares tree
            elif element == "account_tree":
                return app_accounts.layout.itemAt(0).widget()

            # Top: Account tree > Account with lots of history
            elif element == "account_history":
                return get_ui("account_tree").topLevelItem(0)
            elif element.startswith("account_history_"):
                column = int(element.split("_")[-1])
                return get_ui("account_history").data(column, Qt.DisplayRole)

            elif element == "account_historyCash":
                return get_ui("account_history").child(1)
            elif element.startswith("account_historyCash_"):
                column = int(element.split("_")[-1])
                return get_ui("account_historyCash").data(column, Qt.DisplayRole)

            elif element == "account_historyACN":
                return get_ui("account_history").child(0)
            elif element.startswith("account_historyACN_"):
                column = int(element.split("_")[-1])
                return get_ui("account_historyACN").data(column, Qt.DisplayRole)

            elif element == "account_no_historyEUR":
                return get_ui("account_no_history").child(0)

            # Top: Account tree > Account with no history
            elif element == "account_no_history":
                return get_ui("account_tree").topLevelItem(1)

            # Top: Account tree > Add account
            elif element == "add_account":
                return get_ui("account_tree").topLevelItem(2)

            # Top: Account tree > Disabled account
            elif element == "disabled_account":
                if get_ui("display_disabled").isChecked():
                    return get_ui("account_tree").topLevelItem(3)
            elif element.startswith("disabled_account_"):
                column = int(element.split("_")[-1])
                return get_ui("disabled_account").data(column, Qt.DisplayRole)

            # Top: Account tree > Hidden account
            elif element == "hidden_account":
                if get_ui("display_hidden").isChecked():
                    position = 4 if get_ui("display_disabled").isChecked() else 3
                    return get_ui("account_tree").topLevelItem(position)
            elif element.startswith("hidden_account_"):
                column = int(element.split("_")[-1])
                return get_ui("hidden_account").data(column, Qt.DisplayRole)

            # Top: Account tree > Main account
            elif element == "main_account":
                return get_ui("account_tree").topLevelItem(3)

            # Bottom: Display hidden / disabled accounts
            elif element == "display_hidden":
                return app_accounts.layout.itemAt(1).widget()
            elif element == "display_disabled":
                return app_accounts.layout.itemAt(2).widget()

            # Right: Transaction table
            elif element == "transactions_table":
                return app_accounts.layout.itemAt(1).widget()

            raise ValueError(f"Field {element} could not be found")

        return get_ui

    def test_accounts_display(self, app_ui):
        # Check overall structure
        assert isinstance(app_ui("layout"), QtWidgets.QVBoxLayout), "Layout is OK"
        assert app_ui("layout").count() == 3, "Count of elements is OK"

        # Check tree
        assert isinstance(
            app_ui("account_tree"), QtWidgets.QTreeWidget
        ), "The tree is a tree"
        assert (
            app_ui("account_tree").topLevelItemCount() == 4
        ), "Count of elements is OK"

        assert (
            app_ui("add_account").data(0, Qt.DisplayRole) == "Add new account"
        ), "Add account name OK"
        assert app_ui("add_account").data(1, Qt.DisplayRole) == "0", "Add account ID OK"
        assert app_ui("add_account").childCount() == 0, "Add account has no child"

        assert (
            app_ui("account_history_0") == "Account with lots of history"
        ), "Account name OK"
        assert app_ui("account_history_1") == "4", "Account ID OK"
        assert app_ui("account_history_2") == "HIST", "Account code OK"
        assert app_ui("account_history_3") == "", "Account quantity OK"
        assert app_ui("account_history_4") == "Unknown or too old", "Account value OK"
        assert app_ui("account_history_5") == "", "Account at date OK"
        assert app_ui("account_history_6") == "10\u202f000,00000", "Account invested OK"
        assert app_ui("account_history").childCount() == 3, "Account has 3 children"

        assert app_ui("account_historyCash_0") == "Cash (EUR)", "Cash name OK"
        assert app_ui("account_historyCash_1") == "", "Cash ID OK"
        assert app_ui("account_historyCash_2") == "EUR", "Cash code OK"
        assert app_ui("account_historyCash_3") == "3\u202f750,00000", "Cash quantity OK"
        assert app_ui("account_historyCash_4") == "3\u202f750,00 EUR", "Cash value OK"
        assert app_ui("account_historyCash_5") == "", "Cash at date OK"
        assert app_ui("account_historyCash_6") == "", "Cash total invested OK"
        assert app_ui("account_historyCash").childCount() == 0, "Cash has 0 child"

        assert app_ui("account_historyACN_0") == "Accenture", "ACN name OK"
        assert app_ui("account_historyACN_1") == "", "ACN ID OK"
        assert app_ui("account_historyACN_2") == "NYSE:ACN", "ACN code OK"
        assert app_ui("account_historyACN_3") == "5,00000", "ACN quantity OK"
        assert app_ui("account_historyACN_4") == "50,00 EUR", "ACN value OK"
        five_days_ago = datetime.date.today() + datetime.timedelta(days=-5)
        five_days_ago_label = five_days_ago.strftime("%d/%m/%Y")
        assert app_ui("account_historyACN_5") == five_days_ago_label, "ACN at date OK"
        assert app_ui("account_historyACN_6") == "", "ACN total invested OK"
        assert app_ui("account_historyACN").childCount() == 0, "ACN has 0 child"

        # Check checkboxes
        assert isinstance(
            app_ui("display_hidden"), QtWidgets.QCheckBox
        ), "Display hidden is a checkbox"
        assert (
            app_ui("display_hidden").text() == "Display hidden accounts?"
        ), "Display hidden label OK"
        assert isinstance(
            app_ui("display_disabled"), QtWidgets.QCheckBox
        ), "Display disabled is a checkbox"
        assert (
            app_ui("display_disabled").text() == "Display disabled accounts?"
        ), "Display disabled label OK"

    def test_accounts_display_hidden_accounts(self, app_ui, qtbot):
        # Click on checkbox
        # This offset is just a guess to end up on the checkbox
        offset = QtCore.QPoint(2, app_ui("display_hidden").height() // 2)
        qtbot.mouseClick(app_ui("display_hidden"), Qt.LeftButton, Qt.NoModifier, offset)
        # Check hidden account is displayed
        assert (
            app_ui("account_tree").topLevelItemCount() == 5
        ), "Count of elements is OK"

        assert app_ui("hidden_account_0") == "Hidden account", "Account name OK"
        assert app_ui("hidden_account_1") == "2", "Account ID OK"
        assert app_ui("hidden_account_2") == "487485", "Account code OK"
        assert app_ui("hidden_account_3") == "", "Account quantity OK"
        assert app_ui("hidden_account_4") == "-", "Account value OK"
        assert app_ui("hidden_account_5") == "", "Account at date OK"
        assert app_ui("hidden_account_6") == "10\u202f000,00000", "Account invested OK"
        assert app_ui("hidden_account").childCount() == 1, "Account has 1 child"

    def test_accounts_display_disabled_accounts(self, app_ui, qtbot):
        # Click on checkbox
        # This offset is just a guess to end up on the checkbox
        offset = QtCore.QPoint(2, app_ui("display_disabled").height() // 2)
        qtbot.mouseClick(
            app_ui("display_disabled"), Qt.LeftButton, Qt.NoModifier, offset
        )
        # Check hidden account is displayed
        assert (
            app_ui("account_tree").topLevelItemCount() == 5
        ), "Count of elements is OK"

        assert app_ui("disabled_account_0") == "Disabled account", "Account name OK"
        assert app_ui("disabled_account_1") == "3", "Account ID OK"
        assert app_ui("disabled_account_2") == "54614", "Account code OK"
        assert app_ui("disabled_account_3") == "", "Account quantity OK"
        assert app_ui("disabled_account_4") == "10,00 EUR", "Account value OK"
        assert app_ui("disabled_account_5") == "", "Account at date OK"
        assert app_ui("disabled_account_6") == "10,00000", "Account invested OK"
        assert app_ui("disabled_account").childCount() == 2, "Account has 2 children"

    def test_accounts_display_hidden_and_disabled_accounts(self, app_ui, qtbot):
        # Click on checkbox
        # This offset is just a guess to end up on the checkbox
        offset = QtCore.QPoint(2, app_ui("display_disabled").height() // 2)
        qtbot.mouseClick(
            app_ui("display_disabled"), Qt.LeftButton, Qt.NoModifier, offset
        )
        qtbot.mouseClick(app_ui("display_hidden"), Qt.LeftButton, Qt.NoModifier, offset)
        # Check hidden account is displayed
        assert (
            app_ui("account_tree").topLevelItemCount() == 6
        ), "Count of elements is OK"

        assert app_ui("hidden_account_0") == "Hidden account", "Account name OK"
        assert app_ui("hidden_account_1") == "2", "Account ID OK"
        assert app_ui("hidden_account_2") == "487485", "Account code OK"
        assert app_ui("hidden_account_3") == "", "Account quantity OK"
        assert app_ui("hidden_account_4") == "-", "Account value OK"
        assert app_ui("hidden_account_5") == "", "Account at date OK"
        assert app_ui("hidden_account_6") == "10\u202f000,00000", "Account invested OK"
        assert app_ui("hidden_account").childCount() == 1, "Account has 1 child"

        assert app_ui("disabled_account_0") == "Disabled account", "Account name OK"
        assert app_ui("disabled_account_1") == "3", "Account ID OK"
        assert app_ui("disabled_account_2") == "54614", "Account code OK"
        assert app_ui("disabled_account_3") == "", "Account quantity OK"
        assert app_ui("disabled_account_4") == "10,00 EUR", "Account value OK"
        assert app_ui("disabled_account_5") == "", "Account at date OK"
        assert app_ui("disabled_account_6") == "10,00000", "Account invested OK"
        assert app_ui("disabled_account").childCount() == 2, "Account has 2 children"


if __name__ == "__main__":
    pytest.main(["-s", __file__])
