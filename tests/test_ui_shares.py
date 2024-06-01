import os
import sys
import datetime
import pytest
import sqlalchemy.exc
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, "investmenttracker"))


class TestUiShares:
    # Edit dialog items
    dialog_items = {
        "share": {
            "name": 0,
            "main_code": 1,
            "base_currency_id": 2,
            "hidden": 3,
            "group_id": 4,
            "sync_origin": 5,
            "alpha_code": 6,
            "bourso_code": 7,
            "quantalys_code": 8,
            "button_ok": 2,
            "button_cancel": 1,
        },
        "sharegroup": {
            "name": 0,
            "button_ok": 2,
            "button_cancel": 1,
        },
    }

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

            elif element == "share_AXA":
                return get_ui("group_eurex").child(0)

            # Bottom: "Display hidden shares?" button
            elif element == "display_hidden":
                return app_shares.layout.itemAt(1).widget()

            raise ValueError(f"Field {element} could not be found")

        return get_ui

    def click_tree_item(self, item, qtbot, app_ui):
        if item.parent():
            item.parent().setExpanded(True)
        topleft = app_ui("share_tree").visualItemRect(item).topLeft() + QtCore.QPoint(
            60, 10
        )
        qtbot.mouseClick(
            app_ui("share_tree").viewport(), Qt.LeftButton, Qt.NoModifier, topleft
        )
        qtbot.mouseDClick(
            app_ui("share_tree").viewport(), Qt.LeftButton, Qt.NoModifier, topleft
        )

    def get_dialog_item(self, dialog, item_type, field, role=None):
        form_widget = dialog.layout().itemAt(0).widget()
        form_layout = form_widget.layout()
        positions = self.dialog_items[item_type]
        roles = {
            "label": QtWidgets.QFormLayout.LabelRole,
            "field": QtWidgets.QFormLayout.FieldRole,
        }

        if field.startswith("button"):
            buttonbox = dialog.layout().itemAt(1).widget()
            return buttonbox.layout().itemAt(positions[field]).widget()
        if role in ("label", "field"):
            return form_layout.itemAt(positions[field], roles[role]).widget()
        else:
            return form_layout.itemAt(positions[field] + 1, roles["field"]).widget()

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

    def test_shares_add_sharegroup_cancel(self, app_ui, qtbot, qapp):
        def handle_dialog():
            qtbot.waitUntil(lambda: qapp.activeWindow() is not None)
            dialog = qapp.activeWindow()
            assert dialog is not None, "Dialog gets displayed"

            # Check overall structure
            assert isinstance(
                dialog.layout(), QtWidgets.QVBoxLayout
            ), "Dialog layout OK"
            form_widget = dialog.layout().itemAt(0).widget()
            form_layout = form_widget.layout()
            assert isinstance(form_layout, QtWidgets.QFormLayout), "Form layout OK"
            assert form_layout.rowCount() == 1, "Form item count OK"
            name_label = self.get_dialog_item(dialog, "sharegroup", "name", "label")
            name_field = self.get_dialog_item(dialog, "sharegroup", "name", "field")
            assert isinstance(name_label, QtWidgets.QLabel), "Name label OK"
            assert isinstance(name_field, QtWidgets.QLineEdit), "Name field OK"
            buttonbox = dialog.layout().itemAt(1).widget()
            assert isinstance(buttonbox, QtWidgets.QDialogButtonBox), "Buttonbox OK"

            button = self.get_dialog_item(dialog, "sharegroup", "button_cancel")

            # Enter the name & click OK
            qtbot.keyClicks(name_field, "New group")
            qtbot.mouseClick(button, Qt.LeftButton, Qt.NoModifier)

            assert app_ui("share_tree").topLevelItemCount() == 6, "Element count OK"

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(0, handle_dialog)
        self.click_tree_item(app_ui("add_group"), qtbot, app_ui)

    def test_shares_add_sharegroup_empty_name(self, app_ui, qtbot, qapp, app_db):
        def handle_dialog():
            # Gather variables
            qtbot.waitUntil(lambda: qapp.activeWindow() is not None)
            dialog = qapp.activeWindow()
            button = self.get_dialog_item(dialog, "sharegroup", "button_ok")

            # Enter the name & click OK
            qtbot.mouseClick(button, Qt.LeftButton, Qt.NoModifier)
            error_field = self.get_dialog_item(dialog, "sharegroup", "name", "error")
            dialog.close()

            # Check results
            assert error_field.text() == "Missing share group name", "Error display OK"
            assert app_ui("share_tree").topLevelItemCount() == 6, "Element count OK"
            with pytest.raises(sqlalchemy.exc.NoResultFound):
                app_db.share_group_get_by_id(4)

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(0, handle_dialog)
        self.click_tree_item(app_ui("add_group"), qtbot, app_ui)

    def test_shares_add_sharegroup_confirm(self, app_ui, qtbot, qapp, app_db):
        def handle_dialog():
            # Gather variables
            qtbot.waitUntil(lambda: qapp.activeWindow() is not None)
            dialog = qapp.activeWindow()
            name_field = self.get_dialog_item(dialog, "sharegroup", "name", "field")
            button = self.get_dialog_item(dialog, "sharegroup", "button_ok")

            # Enter the name & click OK
            qtbot.keyClicks(name_field, "New group")
            qtbot.mouseClick(button, Qt.LeftButton, Qt.NoModifier)

            # Check results
            assert app_ui("share_tree").topLevelItemCount() == 7, "Element count OK"
            assert app_db.share_group_get_by_id(4).name == "New group", "Save OK"

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(0, handle_dialog)
        self.click_tree_item(app_ui("add_group"), qtbot, app_ui)

    def test_shares_edit_sharegroup(self, app_ui, qtbot, qapp, app_db):
        def handle_dialog():
            # Gather variables
            qtbot.waitUntil(lambda: qapp.activeWindow() is not None)
            dialog = qapp.activeWindow()
            name_field = self.get_dialog_item(dialog, "sharegroup", "name", "field")
            button = self.get_dialog_item(dialog, "sharegroup", "button_ok")

            # Enter the name & click OK
            qtbot.keyClicks(name_field, " markets")
            qtbot.mouseClick(button, Qt.LeftButton, Qt.NoModifier)

            # Check results
            assert app_ui("share_tree").topLevelItemCount() == 6, "Element count OK"
            assert app_db.share_group_get_by_id(1).name == "AMEX markets", "Save OK"

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(0, handle_dialog)
        self.click_tree_item(app_ui("group_amex"), qtbot, app_ui)

    def test_shares_add_share_cancel(self, app_ui, qtbot, qapp, app_db):
        def handle_dialog():
            qtbot.waitUntil(lambda: qapp.activeWindow() is not None)
            dialog = qapp.activeWindow()

            # Check overall structure
            assert isinstance(
                dialog.layout(), QtWidgets.QVBoxLayout
            ), "Dialog layout OK"
            form_widget = dialog.layout().itemAt(0).widget()
            form_layout = form_widget.layout()
            assert isinstance(form_layout, QtWidgets.QFormLayout), "Form layout OK"
            assert form_layout.rowCount() == 9, "Form item count OK"

            name_label = self.get_dialog_item(dialog, "share", "name", "label")
            name_field = self.get_dialog_item(dialog, "share", "name", "field")
            assert isinstance(name_label, QtWidgets.QLabel), "Name label OK"
            assert isinstance(name_field, QtWidgets.QLineEdit), "Name field OK"

            main_code_label = self.get_dialog_item(
                dialog, "share", "main_code", "label"
            )
            main_code_field = self.get_dialog_item(
                dialog, "share", "main_code", "field"
            )
            assert isinstance(main_code_label, QtWidgets.QLabel), "Code label OK"
            assert isinstance(main_code_field, QtWidgets.QLineEdit), "Code field OK"

            currency_label = self.get_dialog_item(
                dialog, "share", "base_currency_id", "label"
            )
            currency_field = self.get_dialog_item(
                dialog, "share", "base_currency_id", "field"
            )
            assert isinstance(currency_label, QtWidgets.QLabel), "Currency label OK"
            assert isinstance(currency_field, QtWidgets.QComboBox), "Currency field OK"

            hidden_label = self.get_dialog_item(dialog, "share", "hidden", "label")
            hidden_field = self.get_dialog_item(dialog, "share", "hidden", "field")
            assert isinstance(hidden_label, QtWidgets.QLabel), "Hidden label OK"
            assert isinstance(hidden_field, QtWidgets.QCheckBox), "Hidden field OK"

            group_id_label = self.get_dialog_item(dialog, "share", "group_id", "label")
            group_id_field = self.get_dialog_item(dialog, "share", "group_id", "field")
            assert isinstance(group_id_label, QtWidgets.QLabel), "Group ID label OK"
            assert isinstance(group_id_field, QtWidgets.QComboBox), "Group ID field OK"

            sync_origin_label = self.get_dialog_item(
                dialog, "share", "sync_origin", "label"
            )
            sync_origin_field = self.get_dialog_item(
                dialog, "share", "sync_origin", "field"
            )
            assert isinstance(
                sync_origin_label, QtWidgets.QLabel
            ), "Sync origin label OK"
            assert isinstance(
                sync_origin_field, QtWidgets.QComboBox
            ), "Sync origin field OK"

            alpha_label = self.get_dialog_item(dialog, "share", "alpha_code", "label")
            alpha_field = self.get_dialog_item(dialog, "share", "alpha_code", "field")
            assert isinstance(alpha_label, QtWidgets.QLabel), "Alpha code label OK"
            assert isinstance(alpha_field, QtWidgets.QLineEdit), "Alpha code field OK"

            bourso_label = self.get_dialog_item(dialog, "share", "bourso_code", "label")
            bourso_field = self.get_dialog_item(dialog, "share", "bourso_code", "field")
            assert isinstance(bourso_label, QtWidgets.QLabel), "Bourso code label OK"
            assert isinstance(bourso_field, QtWidgets.QLineEdit), "Bourso code field OK"

            quanta_label = self.get_dialog_item(
                dialog, "share", "quantalys_code", "label"
            )
            quanta_field = self.get_dialog_item(
                dialog, "share", "quantalys_code", "field"
            )
            assert isinstance(quanta_label, QtWidgets.QLabel), "Quantalys code label OK"
            assert isinstance(
                quanta_field, QtWidgets.QLineEdit
            ), "Quantalys code field OK"

            buttonbox = dialog.layout().itemAt(1).widget()
            assert isinstance(buttonbox, QtWidgets.QDialogButtonBox), "Buttonbox OK"

            button = self.get_dialog_item(dialog, "sharegroup", "button_cancel")

            # Click cancel
            qtbot.mouseClick(button, Qt.LeftButton, Qt.NoModifier)

            # Check results
            assert app_ui("share_tree").topLevelItemCount() == 6, "Element count OK"

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(0, handle_dialog)
        self.click_tree_item(app_ui("add_share"), qtbot, app_ui)

    def test_shares_add_share_confirm(self, app_ui, qtbot, qapp, app_db):
        def handle_dialog():
            # Get the different fields
            qtbot.waitUntil(lambda: qapp.activeWindow() is not None)
            dialog = qapp.activeWindow()
            name = self.get_dialog_item(dialog, "share", "name", "field")
            sync_origin = self.get_dialog_item(dialog, "share", "sync_origin", "field")
            bourso = self.get_dialog_item(dialog, "share", "bourso_code", "field")

            button = self.get_dialog_item(dialog, "sharegroup", "button_ok")

            # Set the different values
            qtbot.keyClicks(name, "New share")
            qtbot.keyClicks(sync_origin, "Boursorama")
            qtbot.keyClicks(bourso, "1rNEW")

            # Click OK
            qtbot.mouseClick(button, Qt.LeftButton, Qt.NoModifier)

            # Check results
            assert app_ui("group_ungrouped").childCount() == 2, "Element count OK"
            assert app_db.share_get_by_id(8).name == "New share"
            assert app_db.share_get_by_id(8).codes[0].value == "1rNEW"
            assert app_db.share_get_by_id(8).code_sync_origin == "1rNEW"

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(0, handle_dialog)
        self.click_tree_item(app_ui("add_share"), qtbot, app_ui)

    def test_shares_add_share_confirm_empty_name(self, app_ui, qtbot, qapp, app_db):
        def handle_dialog():
            # Get the different fields
            qtbot.waitUntil(lambda: qapp.activeWindow() is not None)
            dialog = qapp.activeWindow()

            button = self.get_dialog_item(dialog, "sharegroup", "button_ok")

            # Click OK
            qtbot.mouseClick(button, Qt.LeftButton, Qt.NoModifier)
            error_field = self.get_dialog_item(dialog, "share", "name", "error")
            dialog.close()

            # Check results
            assert error_field.text() == "Missing share name", "Error display OK"
            assert app_ui("group_ungrouped").childCount() == 1, "Element count OK"
            with pytest.raises(sqlalchemy.exc.NoResultFound):
                app_db.share_group_get_by_id(8)

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(0, handle_dialog)
        self.click_tree_item(app_ui("add_share"), qtbot, app_ui)

    def test_shares_add_share_sync_origin_no_code(self, app_ui, qtbot, qapp, app_db):
        def handle_dialog():
            # Get the different fields
            qtbot.waitUntil(lambda: qapp.activeWindow() is not None)
            dialog = qapp.activeWindow()
            name = self.get_dialog_item(dialog, "share", "name", "field")
            sync_origin = self.get_dialog_item(dialog, "share", "sync_origin", "field")

            button = self.get_dialog_item(dialog, "sharegroup", "button_ok")

            # Set the different values
            qtbot.keyClicks(name, "New share")
            qtbot.keyClicks(sync_origin, "Boursorama")

            # Click OK
            qtbot.mouseClick(button, Qt.LeftButton, Qt.NoModifier)
            error_field = self.get_dialog_item(dialog, "share", "bourso_code", "error")
            dialog.close()

            # Check results
            assert error_field.text() == "Missing code for sync", "Error display OK"
            assert app_ui("group_ungrouped").childCount() == 1, "Element count OK"
            with pytest.raises(sqlalchemy.exc.NoResultFound):
                app_db.share_group_get_by_id(8)

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(0, handle_dialog)
        self.click_tree_item(app_ui("add_share"), qtbot, app_ui)

    def test_shares_edit_share(self, app_ui, qtbot, qapp, app_db):
        def handle_dialog():
            # Get the different fields
            qtbot.waitUntil(lambda: qapp.activeWindow() is not None)
            dialog = qapp.activeWindow()
            sync_origin = self.get_dialog_item(dialog, "share", "sync_origin", "field")
            alpha = self.get_dialog_item(dialog, "share", "alpha_code", "field")
            quanta = self.get_dialog_item(dialog, "share", "quantalys_code", "field")

            button = self.get_dialog_item(dialog, "sharegroup", "button_ok")

            # Set the different values
            # Setting combobox values to an empty value is tricky
            sync_origin.setCurrentIndex(0)
            qtbot.keyClicks(quanta, "NY_WDAY")
            alpha.setText("")

            # Click OK
            qtbot.mouseClick(button, Qt.LeftButton, Qt.NoModifier)

            # Check results
            share = app_db.share_get_by_id(3)
            assert len(share.codes) == 1, "Codes are updated"
            assert share.sync_origin is None, "Sync disabled"
            assert share.codes[0].value == "NY_WDAY", "New code added"
            assert share.codes[0].origin.value["name"] == "Quantalys", "New code added"

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(0, handle_dialog)
        self.click_tree_item(app_ui("share_WDAY"), qtbot, app_ui)

    def test_shares_edit_share_code(self, app_ui, qtbot, qapp, app_db):
        def handle_dialog():
            # Get the different fields
            qtbot.waitUntil(lambda: qapp.activeWindow() is not None)
            dialog = qapp.activeWindow()
            alpha = self.get_dialog_item(dialog, "share", "alpha_code", "field")

            button = self.get_dialog_item(dialog, "sharegroup", "button_ok")

            # Set the different values
            alpha.setText("1wACN")

            # Click OK
            qtbot.mouseClick(button, Qt.LeftButton, Qt.NoModifier)

            # Check results
            share = app_db.share_get_by_id(1)
            assert len(share.codes) == 3, "Codes are updated"
            assert share.codes[2].value == "1wACN", "Code modified"

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(0, handle_dialog)
        self.click_tree_item(app_ui("share_AXA"), qtbot, app_ui)


if __name__ == "__main__":
    pytest.main(["-s", __file__])
