import os
import sys
import pytest
import datetime
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "investmenttracker"))

import controllers.widgets.graphsarea


class TestUiGraphs:
    @pytest.fixture
    def app_graphs(self, app_mainwindow):
        app_mainwindow.display_tab("Graphs")

        yield app_mainwindow.layout.currentWidget()

    @pytest.fixture
    def app_ui(self, app_mainwindow, app_graphs):
        def get_ui(element):
            # Main window
            if element == "mainwindow":
                return app_mainwindow

            # Overall elements
            if element == "layout":
                return app_graphs.layout

            # Left: Choose what to display
            elif element == "left_column":
                return app_graphs.layout.itemAt(0).widget()

            # Left > Top: Account tree & checkboxes
            elif element == "account_tree":
                return get_ui("left_column").layout.itemAt(0).widget()

            # Left > Top: Account tree > Account with lots of history
            elif element == "account_history":
                return get_ui("account_tree").topLevelItem(0)
            elif element.startswith("account_history_"):
                column = int(element.split("_")[-1])
                return get_ui("account_history").data(column, Qt.DisplayRole)
            # Left > Top: Account tree > Account with no history
            elif element == "account_no_history":
                return get_ui("account_tree").topLevelItem(1)
            # Left > Top: Account tree > Disabled account
            elif element == "disabled_account":
                if get_ui("display_disabled_accounts").isChecked():
                    return get_ui("account_tree").topLevelItem(2)
            elif element.startswith("disabled_account_"):
                column = int(element.split("_")[-1])
                return get_ui("disabled_account").data(column, Qt.DisplayRole)
            # Left > Top: Account tree > Hidden account
            elif element == "hidden_account":
                if get_ui("display_hidden_accounts").isChecked():
                    position = (
                        3 if get_ui("display_disabled_accounts").isChecked() else 2
                    )
                    return get_ui("account_tree").topLevelItem(position)
            elif element.startswith("hidden_account_"):
                column = int(element.split("_")[-1])
                return get_ui("hidden_account").data(column, Qt.DisplayRole)
            # Left > Top: Account tree > Main account
            elif element == "main_account":
                position = 2
                position += 1 if get_ui("display_disabled_accounts").isChecked() else 0
                position += 1 if get_ui("display_hidden_accounts").isChecked() else 0
                return get_ui("account_tree").topLevelItem(position)
            elif element.startswith("main_account_"):
                column = int(element.split("_")[-1])
                return get_ui("main_account").data(column, Qt.DisplayRole)
            # Left > Top: Account tree > Test account in EUR
            elif element == "test_accounteur":
                position = 3
                position += 1 if get_ui("display_disabled_accounts").isChecked() else 0
                position += 1 if get_ui("display_hidden_accounts").isChecked() else 0
                return get_ui("account_tree").topLevelItem(position)
            elif element.startswith("test_accounteur_"):
                column = int(element.split("_")[-1])
                return get_ui("test_accounteur").data(column, Qt.DisplayRole)

            # Left > Top: Checkboxes for account display
            elif element == "display_hidden_accounts":
                return get_ui("left_column").layout.itemAt(1).widget()
            elif element == "display_disabled_accounts":
                return get_ui("left_column").layout.itemAt(2).widget()

            # Left > Bottom: Share tree & checkboxes
            elif element == "share_tree":
                return get_ui("left_column").layout.itemAt(3).widget()

            # Left > Bottom: Share tree > AMEX group
            elif element == "share_AMEX":
                return get_ui("share_tree").topLevelItem(0)
            elif element.startswith("share_AMEX_"):
                column = int(element.split("_")[-1])
                return get_ui("share_AMEX").data(column, Qt.DisplayRole)
            elif element == "share_ACN":
                return get_ui("share_AMEX").child(0)
            elif element == "share_WDAY":
                return get_ui("share_AMEX").child(1)

            # Left > Bottom: Share tree > CURRENCY group
            elif element == "share_CURRENCY":
                return get_ui("share_tree").topLevelItem(1)
            elif element.startswith("share_CURRENCY_"):
                column = int(element.split("_")[-1])
                return get_ui("share_CURRENCY").data(column, Qt.DisplayRole)
            elif element == "share_USD":
                return get_ui("share_CURRENCY").child(0)

            # Left > Bottom: Share tree > EUREX group
            elif element == "share_EUREX":
                return get_ui("share_tree").topLevelItem(2)
            elif element.startswith("share_EUREX_"):
                column = int(element.split("_")[-1])
                return get_ui("share_EUREX").data(column, Qt.DisplayRole)
            elif element == "share_AXA":
                return get_ui("share_EUREX").child(0)
            elif element == "share_BNP":
                if get_ui("display_hidden_shares").isChecked():
                    return get_ui("share_EUREX").child(1)

            # Left > Bottom: Share tree > ungrouped group
            elif element == "share_ungrouped":
                return get_ui("share_tree").topLevelItem(3)
            elif element.startswith("share_ungrouped_"):
                column = int(element.split("_")[-1])
                return get_ui("share_ungrouped").data(column, Qt.DisplayRole)
            elif element == "share_EUR":
                return get_ui("share_ungrouped").child(0)
            elif element == "share_HSBC":
                return get_ui("share_ungrouped").child(1)

            # Left > Bottom: Checkboxes for share display
            elif element == "display_hidden_shares":
                return get_ui("left_column").layout.itemAt(4).widget()

            # Right: Graph details
            elif element == "right_column":
                return app_graphs.layout.itemAt(1).widget()

            # Right > Top: Graph inputs > Period
            elif element == "period_label":
                return get_ui("right_column").layout.itemAtPosition(0, 0).widget()
            elif element == "period_start":
                return get_ui("right_column").layout.itemAtPosition(0, 1).widget()
            elif element == "period_end":
                return get_ui("right_column").layout.itemAtPosition(0, 2).widget()

            # Right > Top: Graph inputs > Baseline
            elif element == "baseline_enabled":
                return get_ui("right_column").layout.itemAtPosition(1, 0).widget()
            elif element == "baseline_date_label":
                return get_ui("right_column").layout.itemAtPosition(1, 1).widget()
            elif element == "baseline_date":
                return get_ui("right_column").layout.itemAtPosition(1, 2).widget()
            elif element == "baseline_net":
                return get_ui("right_column").layout.itemAtPosition(1, 3).widget()

            # Right > Top: Graph inputs > Display account composition
            elif element == "split_enabled":
                return get_ui("right_column").layout.itemAtPosition(2, 0).widget()

            # Right > Top: Graph inputs > Error messages
            elif element == "errors":
                return get_ui("right_column").layout.itemAtPosition(3, 0).widget()

            # Right > Center: Graph
            elif element == "graph":
                return get_ui("right_column").layout.itemAtPosition(4, 0).widget()
            elif element == "display_markers":
                return get_ui("right_column").layout.itemAtPosition(5, 0).widget()

            # Right > Bottom: Performance table
            elif element == "performance_table":
                return get_ui("right_column").layout.itemAtPosition(6, 0).widget()
            elif element.startswith("performance_table"):
                row, col = element.split("_")[2:]
                return get_ui("performance_table").item(int(row), int(col)).text()

            raise ValueError(f"Field {element} could not be found")

        return get_ui

    def click_tree_item(self, type, item, qtbot, app_ui):
        if item.parent():
            item.parent().setExpanded(True)
        topleft = app_ui(type + "_tree").visualItemRect(item).topLeft()
        qtbot.mouseClick(
            app_ui(type + "_tree").viewport(), Qt.LeftButton, Qt.NoModifier, topleft
        )
        qtbot.mouseDClick(
            app_ui(type + "_tree").viewport(), Qt.LeftButton, Qt.NoModifier, topleft
        )

    def test_graphs_display(self, app_ui):
        # Element types - structure is (element name, expected type, label)
        element_types = [
            ("layout", QtWidgets.QHBoxLayout, "Overall layout"),
            ("account_tree", QtWidgets.QTreeWidget, "Account tree"),
            ("display_hidden_accounts", QtWidgets.QCheckBox, "Display hidden accounts"),
            (
                "display_disabled_accounts",
                QtWidgets.QCheckBox,
                "Display disabled accounts",
            ),
            ("share_tree", QtWidgets.QTreeWidget, "Share tree"),
            ("share_AMEX", QtWidgets.QTreeWidgetItem, "AMEX share group"),
            ("share_CURRENCY", QtWidgets.QTreeWidgetItem, "CURRENCY share group"),
            ("display_hidden_shares", QtWidgets.QCheckBox, "Display hidden shares"),
            ("period_label", QtWidgets.QLabel, "Period - Label"),
            ("period_start", QtWidgets.QDateEdit, "Period - Start date"),
            ("period_end", QtWidgets.QDateEdit, "Period - End date"),
            ("baseline_enabled", QtWidgets.QCheckBox, "Baseline enabled"),
            ("baseline_date_label", QtWidgets.QLabel, "Baseline date label"),
            ("baseline_date", QtWidgets.QDateEdit, "Baseline date"),
            ("baseline_net", QtWidgets.QCheckBox, "Baseline net of cash entry/exit"),
            ("split_enabled", QtWidgets.QCheckBox, "Split enabled?"),
            ("errors", QtWidgets.QLabel, "Error messages"),
            ("graph", controllers.widgets.graphsarea.GraphsArea, "Graph"),
            ("display_markers", QtWidgets.QCheckBox, "Display markers"),
            ("performance_table", QtWidgets.QTableWidget, "Performance table"),
        ]
        for item in element_types:
            assert isinstance(app_ui(item[0]), item[1]), item[2] + " instance type OK"

        # Check overall structure
        assert app_ui("layout").count() == 2, "Count of elements is OK"

        # Left: Choose what to display
        assert isinstance(
            app_ui("left_column").layout, QtWidgets.QVBoxLayout
        ), "Left column layout OK"
        assert app_ui("left_column").layout.count() == 5, "Count of elements is OK"

        # Left > Top: Account tree
        assert app_ui("account_tree").topLevelItemCount() == 4, "Account tree count OK"

        # Left > Top: Account tree > Account with lots of history
        assert (
            app_ui("account_history_0") == "Account with lots of history"
        ), "Account name OK"
        assert app_ui("account_history_1") == "account", "Account type OK"
        assert app_ui("account_history_2") == "4", "Account ID OK"

        # Left > Top: Checkboxes for account display
        assert (
            app_ui("display_hidden_accounts").text() == "Display hidden accounts?"
        ), "Display hidden label OK"
        assert (
            app_ui("display_disabled_accounts").text() == "Display disabled accounts?"
        ), "Display disabled label OK"

        # Left > Bottom: Share tree & checkboxes
        assert app_ui("share_tree").topLevelItemCount() == 4, "Share tree count OK"

        # Left > Bottom: Share tree > AMEX group
        assert app_ui("share_AMEX_0") == "AMEX", "Share group name OK"
        assert app_ui("share_AMEX_1") == "Group", "Share group type OK"
        assert app_ui("share_AMEX_2") == "1", "Share group ID OK"

        # Left > Bottom: Share tree > CURRENCY group
        assert app_ui("share_CURRENCY_0") == "CURRENCY", "Share group name OK"
        assert app_ui("share_CURRENCY_1") == "Group", "Share group type OK"
        assert app_ui("share_CURRENCY_2") == "3", "Share group ID OK"

        # Left > Bottom: Checkboxes for share display
        assert (
            app_ui("display_hidden_shares").text() == "Display hidden shares?"
        ), "Display hidden shares OK"

        # Right: Graph details
        assert isinstance(
            app_ui("right_column").layout, QtWidgets.QGridLayout
        ), "Right column layout OK"
        assert app_ui("right_column").layout.columnCount() == 4, "Column count OK"
        assert app_ui("right_column").layout.rowCount() == 7, "Row count OK"

        # Right > Top: Graph inputs > Period
        assert app_ui("period_label").text() == "Period", "Period label OK"

        # Right > Top: Graph inputs > Baseline
        assert (
            app_ui("baseline_enabled").text() == "Display evolution?"
        ), "Baseline label OK"
        assert (
            app_ui("baseline_date_label").text() == "Baseline date"
        ), "Baseline date label OK"
        assert (
            app_ui("baseline_net").text()
            == "Net baseline (excludes entry/exit of cash and shares)"
        ), "Baseline net label OK"

        # Right > Top: Graph inputs > Display account composition
        assert (
            app_ui("split_enabled").text() == "Display account composition?"
        ), "Account split label OK"

        # Right > Center: Graph
        assert (
            app_ui("display_markers").text() == "Display markers?"
        ), "Display markers OK"

    def test_graphs_display_hidden_accounts(self, app_ui, qtbot):
        # Click on checkbox
        # This offset is just a guess to end up on the checkbox
        offset = QtCore.QPoint(2, app_ui("display_hidden_accounts").height() // 2)
        qtbot.mouseClick(
            app_ui("display_hidden_accounts"), Qt.LeftButton, Qt.NoModifier, offset
        )
        # Check hidden account is displayed
        assert (
            app_ui("account_tree").topLevelItemCount() == 5
        ), "Count of elements is OK"

        assert app_ui("hidden_account_0") == "Hidden account", "Account name OK"
        assert app_ui("hidden_account_1") == "account", "Account type OK"
        assert app_ui("hidden_account_2") == "2", "Account ID OK"

    def test_graphs_display_disabled_accounts(self, app_ui, qtbot):
        # Click on checkbox
        # This offset is just a guess to end up on the checkbox
        offset = QtCore.QPoint(2, app_ui("display_disabled_accounts").height() // 2)
        qtbot.mouseClick(
            app_ui("display_disabled_accounts"), Qt.LeftButton, Qt.NoModifier, offset
        )
        # Check hidden account is displayed
        assert (
            app_ui("account_tree").topLevelItemCount() == 5
        ), "Count of elements is OK"

        assert app_ui("disabled_account_0") == "Disabled account", "Account name OK"
        assert app_ui("disabled_account_1") == "account", "Account type OK"
        assert app_ui("disabled_account_2") == "3", "Account ID OK"

    def test_graphs_display_hidden_shares(self, app_ui, qtbot):
        # Click on checkbox
        # This offset is just a guess to end up on the checkbox
        offset = QtCore.QPoint(2, app_ui("display_hidden_shares").height() // 2)
        qtbot.mouseClick(
            app_ui("display_hidden_shares"), Qt.LeftButton, Qt.NoModifier, offset
        )
        # Check hidden share is displayed
        assert app_ui("share_EUREX").childCount() == 2, "2 EUREX shares"
        assert app_ui("share_BNP").data(0, Qt.DisplayRole) == "BNP", "BNP name OK"
        assert app_ui("share_BNP").data(1, Qt.DisplayRole) == "Share", "BNP type OK"
        assert app_ui("share_BNP").data(2, Qt.DisplayRole) == "7", "BNP ID OK"

    def test_graphs_account(self, app_ui, qtbot):
        # Select an account
        self.click_tree_item("account", app_ui("test_accounteur"), qtbot, app_ui)

        # Check display in the graph
        dataItems = app_ui("graph").plotItem.dataItems
        assert len(dataItems) == 1, "Graph curve count OK"
        assert dataItems[0].name() == "Test account in EUR (Euro)", "Curve name OK"
        assert len(dataItems[0].curve.yData) == 7, "7 different points in graph"
        values = [10500, 10200, 10300, 9300, 9800, 10000, 9700]
        assert (dataItems[0].curve.yData == values).all(), "Values are correct"

    def test_graphs_account_error(self, app_ui, qtbot):
        # Select an account
        self.click_tree_item("account", app_ui("main_account"), qtbot, app_ui)

        # Check display in the graph
        dataItems = app_ui("graph").plotItem.dataItems
        assert len(dataItems) == 1, "Graph curve count OK"
        assert dataItems[0].name() == "Main account (Euro)", "Curve name OK"
        assert len(dataItems[0].curve.yData) == 0, "No point in graph"
        assert (
            app_ui("errors").text()
            == "Could not display account Main account due to missing value for Accenture"
        ), "Error is displayed"

    def test_graphs_share(self, app_ui, qtbot):
        # Display hidden shares
        # This offset is just a guess to end up on the checkbox
        offset = QtCore.QPoint(2, app_ui("display_hidden_shares").height() // 2)
        qtbot.mouseClick(
            app_ui("display_hidden_shares"), Qt.LeftButton, Qt.NoModifier, offset
        )

        # Select BNP share
        self.click_tree_item("share", app_ui("share_BNP"), qtbot, app_ui)

        # Check display in the graph
        dataItems = app_ui("graph").plotItem.dataItems
        assert len(dataItems) == 1, "Graph curve count OK"
        assert dataItems[0].name() == "BNP (Euro)", "Curve name OK"
        assert len(dataItems[0].curve.yData) == 5, "5 different points in graph"
        values = [52, 53, 58, 60, 57]
        assert (dataItems[0].curve.yData == values).all(), "Values are correct"

    def test_graphs_share_without_currency(self, app_ui, qtbot):
        # Select BNP share
        self.click_tree_item("share", app_ui("share_USD"), qtbot, app_ui)

        # Check display in the graph
        dataItems = app_ui("graph").plotItem.dataItems
        assert len(dataItems) == 1, "Graph curve count OK"
        assert dataItems[0].name() == "Dollar", "Curve name OK"
        assert len(dataItems[0].curve.yData) == 1, "1 points i graph"
        values = [10]
        assert (dataItems[0].curve.yData == values).all(), "Values are correct"

    def test_graphs_period_change(self, app_ui, qtbot):
        # Select an account & a period
        self.click_tree_item("account", app_ui("test_accounteur"), qtbot, app_ui)
        app_ui("period_start").setDate(
            datetime.date.today() + datetime.timedelta(days=-5 * 30 + 3)
        )
        app_ui("period_end").setDate(
            datetime.date.today() + datetime.timedelta(days=-3 * 30 + 3)
        )

        # Check display in the graph
        dataItems = app_ui("graph").plotItem.dataItems
        assert len(dataItems) == 1, "Graph curve count OK"
        assert dataItems[0].name() == "Test account in EUR (Euro)", "Curve name OK"
        values = [10300, 9300, 9800]
        assert len(dataItems[0].curve.yData) == len(values), "3 points in graph"
        for i in range(len(values)):
            assert (
                round(dataItems[0].curve.yData[i], 3) == values[i]
            ), "Values are correct"

    def test_graphs_period_error(self, app_ui, qtbot):
        # Select an account & a period
        app_ui("period_start").setDate(
            datetime.date.today() + datetime.timedelta(days=-3 * 30 + 3)
        )
        app_ui("period_end").setDate(
            datetime.date.today() + datetime.timedelta(days=-5 * 30 + 3)
        )

        # Check display of error
        assert (
            app_ui("errors").text() == "Start date must be before end date"
        ), "Error is displayed"

    def test_graphs_baseline_enabled(self, app_ui, qtbot):
        # Select an account & enable baseline mode
        self.click_tree_item("account", app_ui("test_accounteur"), qtbot, app_ui)
        offset = QtCore.QPoint(2, app_ui("baseline_enabled").height() // 2)
        qtbot.mouseClick(
            app_ui("baseline_enabled"), Qt.LeftButton, Qt.NoModifier, offset
        )

        # Check display in the graph
        dataItems = app_ui("graph").plotItem.dataItems
        assert len(dataItems) == 1, "Graph curve count OK"
        assert dataItems[0].name() == "Test account in EUR (Euro)", "Curve name OK"
        assert len(dataItems[0].curve.yData) == 7, "7 different points in graph"
        values = [1, 0.971, 0.981, 0.886, 0.933, 0.952, 0.924]
        for i in range(len(values)):
            assert (
                round(dataItems[0].curve.yData[i], 3) == values[i]
            ), "Values are correct"

    def test_graphs_baseline_change(self, app_ui, qtbot):
        # Select an account & enable baseline mode
        self.click_tree_item("account", app_ui("test_accounteur"), qtbot, app_ui)
        offset = QtCore.QPoint(2, app_ui("baseline_enabled").height() // 2)
        qtbot.mouseClick(
            app_ui("baseline_enabled"), Qt.LeftButton, Qt.NoModifier, offset
        )

        # Select a baseline date
        # I couldn't find how to do it by typing keys, so instead the date is set programmatically
        app_ui("baseline_date").setDate(
            datetime.date.today() + datetime.timedelta(days=-3 * 30 + 3)
        )

        # Check display in the graph
        dataItems = app_ui("graph").plotItem.dataItems
        assert len(dataItems) == 1, "Graph curve count OK"
        assert dataItems[0].name() == "Test account in EUR (Euro)", "Curve name OK"
        assert len(dataItems[0].curve.yData) == 7, "7 different points in graph"
        values = [1.071, 1.041, 1.051, 0.949, 1, 1.020, 0.990]
        for i in range(len(values)):
            assert (
                round(dataItems[0].curve.yData[i], 3) == values[i]
            ), "Values are correct"

    def test_graphs_baseline_net(self, app_ui, qtbot):
        # Select an account & enable baseline mode
        self.click_tree_item("account", app_ui("test_accounteur"), qtbot, app_ui)
        offset = QtCore.QPoint(2, app_ui("baseline_enabled").height() // 2)
        qtbot.mouseClick(
            app_ui("baseline_enabled"), Qt.LeftButton, Qt.NoModifier, offset
        )
        offset = QtCore.QPoint(2, app_ui("baseline_net").height() // 2)
        qtbot.mouseClick(app_ui("baseline_net"), Qt.LeftButton, Qt.NoModifier, offset)

        # Check display in the graph
        dataItems = app_ui("graph").plotItem.dataItems
        assert len(dataItems) == 1, "Graph curve count OK"
        assert dataItems[0].name() == "Test account in EUR (Euro)", "Curve name OK"
        assert len(dataItems[0].curve.yData) == 7, "7 different points in graph"
        values = [1, 0.971, 0.981, 0.981, 1.029, 1.048, 1.019]
        for i in range(len(values)):
            assert (
                round(dataItems[0].curve.yData[i], 3) == values[i]
            ), "Values are correct"

    def test_graphs_account_split(self, app_ui, qtbot):
        # Select an account & enable split mode
        self.click_tree_item("account", app_ui("test_accounteur"), qtbot, app_ui)
        offset = QtCore.QPoint(2, app_ui("split_enabled").height() // 2)
        qtbot.mouseClick(app_ui("split_enabled"), Qt.LeftButton, Qt.NoModifier, offset)

        # Check display in the graph
        dataItems = app_ui("graph").plotItem.dataItems
        assert len(dataItems) == 3, "Graph curve count OK"
        assert dataItems[0].name() == "Euro", "Curve name OK"
        assert dataItems[1].name() == "BNP (Euro)", "Curve name OK"
        assert dataItems[2].name() == "Test account in EUR (Euro)", "Curve name OK"
        assert len(dataItems[0].curve.yData) == 7, "7 different points in graph"

        # Check values for Euro
        values = [
            1
        ] * 6  # Always 1 because it's the final share, which holds the total of all
        for i in range(len(values)):
            assert (
                round(dataItems[0].curve.yData[i], 3) == values[i]
            ), "Values are correct"
        # Check values for BNP
        values = [0.524, 0.510, 0.515, 0.570, 0.592, 0.600]
        for i in range(len(values)):
            assert (
                round(dataItems[1].curve.yData[i], 3) == values[i]
            ), "Values are correct"

    def test_graphs_account_split_error(self, app_ui, qtbot):
        # Select an account & enable split mode
        self.click_tree_item("account", app_ui("main_account"), qtbot, app_ui)
        self.click_tree_item("account", app_ui("test_accounteur"), qtbot, app_ui)
        offset = QtCore.QPoint(2, app_ui("split_enabled").height() // 2)
        qtbot.mouseClick(app_ui("split_enabled"), Qt.LeftButton, Qt.NoModifier, offset)

        # Check display in the graph
        dataItems = app_ui("graph").plotItem.dataItems
        assert len(dataItems) == 2, "Graph curve count OK"
        assert (
            app_ui("errors")
            .text()
            .find(
                "Could not display account Main account due to missing value for Accenture"
            )
            != -1
        ), "Error is displayed"
        assert (
            app_ui("errors").text().find("Only 1 account can be displayed in this mode")
            != -1
        ), "Error is displayed"

    def test_graphs_account_enable_disable_split(self, app_ui, qtbot):
        # Select an account & click twice on baseline
        self.click_tree_item("account", app_ui("test_accounteur"), qtbot, app_ui)
        offset = QtCore.QPoint(2, app_ui("split_enabled").height() // 2)
        qtbot.mouseClick(app_ui("split_enabled"), Qt.LeftButton, Qt.NoModifier, offset)
        qtbot.mouseClick(app_ui("split_enabled"), Qt.LeftButton, Qt.NoModifier, offset)

        # Check display in the graph
        dataItems = app_ui("graph").plotItem.dataItems
        assert len(dataItems) == 1, "Graph curve count OK"
        assert dataItems[0].name() == "Test account in EUR (Euro)", "Curve name OK"
        assert len(dataItems[0].curve.yData) == 7, "7 different points in graph"
        values = [10500, 10200, 10300, 9300, 9800, 10000, 9700]
        assert (dataItems[0].curve.yData == values).all(), "Values are correct"

    def test_graphs_markers_display(self, app_ui, qtbot):
        # Select an account & click twice on baseline
        self.click_tree_item("account", app_ui("test_accounteur"), qtbot, app_ui)
        offset = QtCore.QPoint(2, app_ui("display_markers").height() // 2)
        qtbot.mouseClick(
            app_ui("display_markers"), Qt.LeftButton, Qt.NoModifier, offset
        )

        # Check display in the graph
        # It seems impossible to check that markers are indeed displayed
        # They're added to QGraphicsScene, which doesn't expose much about its inner workings
        dataItems = app_ui("graph").plotItem.dataItems
        assert len(dataItems) == 1, "Graph curve count OK"
        assert dataItems[0].name() == "Test account in EUR (Euro)", "Curve name OK"
        assert len(dataItems[0].curve.yData) == 7, "7 different points in graph"
        values = [10500, 10200, 10300, 9300, 9800, 10000, 9700]
        assert (dataItems[0].curve.yData == values).all(), "Values are correct"

    def test_graphs_performance_table_share(self, app_ui, qtbot):
        # Display hidden shares
        # This offset is just a guess to end up on the checkbox
        offset = QtCore.QPoint(2, app_ui("display_hidden_shares").height() // 2)
        qtbot.mouseClick(
            app_ui("display_hidden_shares"), Qt.LeftButton, Qt.NoModifier, offset
        )

        # Select BNP share
        self.click_tree_item("share", app_ui("share_BNP"), qtbot, app_ui)

        # Check display in the table
        assert (
            app_ui("performance_table").verticalHeaderItem(0).text() == "BNP"
        ), "Name OK"
        assert app_ui("performance_table_0_1") == "55,00 EUR", "Values OK"
        assert app_ui("performance_table_0_2") == "52,00 EUR\n-5,45 %", "Values OK"
        assert app_ui("performance_table_0_3") == "53,00 EUR\n-3,64 %", "Values OK"
        assert app_ui("performance_table_0_4") == "58,00 EUR\n5,45 %", "Values OK"
        assert app_ui("performance_table_0_5") == "60,00 EUR\n9,09 %", "Values OK"

    def test_graphs_performance_table_account_before_its_creation(self, app_ui, qtbot):
        # Select an account
        self.click_tree_item("account", app_ui("main_account"), qtbot, app_ui)
        app_ui("period_start").setDate(datetime.date(2009, 1, 1))

        # Check display in the graph
        assert (
            app_ui("performance_table").verticalHeaderItem(0).text() == "Main account"
        ), "Name OK"
        assert app_ui("performance_table_0_1") == "Unknown", "Values OK"
        assert app_ui("performance_table_0_2") == "Unknown", "Values OK"
        assert app_ui("performance_table_0_3") == "Unknown", "Values OK"
        assert app_ui("performance_table_0_4") == "Unknown", "Values OK"
        assert app_ui("performance_table_0_5") == "Unknown", "Values OK"


if __name__ == "__main__":
    pytest.main(["-s", __file__])
