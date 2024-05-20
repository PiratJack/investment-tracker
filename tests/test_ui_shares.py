import os
import sys
import datetime
import pytest
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "investmenttracker"))


class TestUiShares:
    @pytest.fixture
    def app_shares(self, app_mainwindow):
        app_mainwindow.display_tab("Shares")

        yield app_mainwindow.layout.currentWidget()

    @pytest.fixture
    def app_ui(self, app_mainwindow, app_shares):
        def get_ui(element):
            # Main window
            if element == "mainwindow":
                return app_mainwindow

            # Overall elements
            if element == "layout":
                return app_shares.layout

            # Top: Shares tree
            elif element == "share_tree":
                return app_shares.layout.itemAt(0).widget()
            elif element == "add_group":
                return get_ui("share_tree").topLevelItem(0)
            elif element == "add_share":
                return get_ui("share_tree").topLevelItem(1)
            elif element == "group_amex":
                return get_ui("share_tree").topLevelItem(2)
            elif element == "group_currency":
                return get_ui("share_tree").topLevelItem(3)
            elif element == "group_eurex":
                return get_ui("share_tree").topLevelItem(4)
            elif element == "group_ungrouped":
                return get_ui("share_tree").topLevelItem(5)

            elif element == "share_WDAY":
                return get_ui("group_amex").child(1)

            elif element == "share_USD":
                return get_ui("group_currency").child(0)

            elif element == "share_HSBC":
                return get_ui("group_ungrouped").child(1)

            # Bottom: "Display hidden shares?" button
            elif element == "display_hidden":
                return app_shares.layout.itemAt(1).widget()

            raise ValueError(f"Field {element} could not be found")

        return get_ui

    def test_shares_display(self, app_ui):
        # Check overall structure
        assert isinstance(app_ui("layout"), QtWidgets.QVBoxLayout), "Layout is OK"
        assert app_ui("layout").count() == 2, "Count of elements is OK"

        # Check tree
        assert isinstance(
            app_ui("share_tree"), QtWidgets.QTreeWidget
        ), "The tree is a tree"
        assert app_ui("share_tree").topLevelItemCount() == 6, "Count of elements is OK"

        assert (
            app_ui("add_group").data(0, Qt.DisplayRole) == "Add new group"
        ), "Add group name OK"
        assert app_ui("add_group").data(1, Qt.DisplayRole) == "0", "Add group ID OK"
        assert (
            app_ui("add_group").data(2, Qt.DisplayRole) == "group"
        ), "Add group type OK"
        assert app_ui("add_group").childCount() == 0, "Add group has no child"

        assert (
            app_ui("add_share").data(0, Qt.DisplayRole) == "Add new share"
        ), "Add share name OK"
        assert app_ui("add_share").data(1, Qt.DisplayRole) == "0", "Add share ID OK"
        assert (
            app_ui("add_share").data(2, Qt.DisplayRole) == "share"
        ), "Add share type OK"
        assert app_ui("add_share").childCount() == 0, "Add share has no child"

        assert app_ui("group_amex").data(0, Qt.DisplayRole) == "AMEX", "AMEX name OK"
        assert app_ui("group_amex").data(1, Qt.DisplayRole) == "1", "AMEX ID OK"
        assert app_ui("group_amex").data(2, Qt.DisplayRole) == "group", "AMEX type OK"
        assert app_ui("group_amex").childCount() == 2, "AMEX has 2 children"

        assert app_ui("share_USD").data(0, Qt.DisplayRole) == "Dollar", "USD name OK"
        assert app_ui("share_USD").data(1, Qt.DisplayRole) == "6", "USD ID OK"
        assert app_ui("share_USD").data(2, Qt.DisplayRole) == "share", "USD type OK"
        assert app_ui("share_USD").data(3, Qt.DisplayRole) == "USD", "USD code OK"
        assert (
            app_ui("share_USD").data(4, Qt.DisplayRole) == "10,00 EUR"
        ), "USD price OK"
        five_days_ago = datetime.date.today() + datetime.timedelta(days=-5)
        five_days_ago_label = five_days_ago.strftime("%d/%m/%Y")
        assert (
            app_ui("share_USD").data(5, Qt.DisplayRole) == five_days_ago_label
        ), "USD price date OK"
        assert app_ui("share_USD").data(6, Qt.DisplayRole) == "", "USD codes OK"
        assert app_ui("share_USD").data(7, Qt.DisplayRole) == "", "USD sync OK"
        assert app_ui("share_USD").checkState(8) == Qt.Unchecked, "USD hidden OK"
        assert app_ui("share_USD").childCount() == 0, "USD has 0 child"

        assert (
            app_ui("share_WDAY").data(6, Qt.DisplayRole) == "Alphavantage: 1rWDAY"
        ), "WDAY codes OK"
        assert (
            app_ui("share_WDAY").data(7, Qt.DisplayRole) == "Alphavantage"
        ), "WDAY sync OK"
        assert app_ui("share_WDAY").checkState(8) == Qt.Unchecked, "WDAY hidden OK"

        assert (
            app_ui("group_ungrouped").data(0, Qt.DisplayRole) == "Shares without group"
        ), "Ungrouped shares display OK"
        assert (
            app_ui("group_ungrouped").data(1, Qt.DisplayRole) == "-1"
        ), "Ungrouped shares ID OK"
        assert (
            app_ui("group_ungrouped").data(2, Qt.DisplayRole) == "group"
        ), "Ungrouped shares type OK"
        assert (
            app_ui("group_ungrouped").childCount() == 1
        ), "Ungrouped shares has 1 child"

        assert isinstance(
            app_ui("display_hidden"), QtWidgets.QCheckBox
        ), "Display hidden shared checkbox OK"
        assert (
            app_ui("display_hidden").text() == "Display hidden shares?"
        ), "Display hidden shared checkbox OK"

    def test_shares_display_hidden_shares(self, app_ui, qtbot):
        # Click on checkbox
        # This offset is just a guess to end up on the checkbox
        offset = QtCore.QPoint(2, app_ui("display_hidden").height() // 2)
        qtbot.mouseClick(app_ui("display_hidden"), Qt.LeftButton, Qt.NoModifier, offset)
        # Check hidden share is displayed
        assert (
            app_ui("group_ungrouped").childCount() == 2
        ), "Ungrouped shares has 2 children"
        assert app_ui("share_HSBC").data(0, Qt.DisplayRole) == "HSBC", "HSBC name OK"
        assert app_ui("share_HSBC").data(1, Qt.DisplayRole) == "4", "HSBC ID OK"
        assert app_ui("share_HSBC").data(2, Qt.DisplayRole) == "share", "HSBC type OK"
        assert app_ui("share_HSBC").data(3, Qt.DisplayRole) == "LU4325", "HSBC code OK"
        assert (
            app_ui("share_HSBC").data(4, Qt.DisplayRole) == "10,00 FR8472"
        ), "HSBC price OK"
        five_days_ago = datetime.date.today() + datetime.timedelta(days=-5)
        five_days_ago_label = five_days_ago.strftime("%d/%m/%Y")
        assert (
            app_ui("share_HSBC").data(5, Qt.DisplayRole) == five_days_ago_label
        ), "HSBC price date OK"
        assert app_ui("share_HSBC").data(6, Qt.DisplayRole) == "", "HSBC codes OK"
        assert app_ui("share_HSBC").data(7, Qt.DisplayRole) == "", "HSBC sync OK"
        assert app_ui("share_HSBC").checkState(8) == Qt.Checked, "HSBC hidden OK"
        assert app_ui("share_HSBC").childCount() == 0, "HSBC has 0 child"


if __name__ == "__main__":
    pytest.main(["-s", __file__])
