import os
import sys
import pytest
import datetime
import sqlalchemy.exc
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
                position = 3 if get_ui("display_disabled").isChecked() else 2
                return get_ui("account_tree").topLevelItem(position)

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

    def get_dialog_item(self, dialog, field, role=None):
        positions = {
            "account": 0,
            "date": 1,
            "label": 2,
            "type": 3,
            "quantity": 4,
            "share": 5,
            "unit_price": 6,
            "known_unit_price": 7,
            "currency_delta": 8,
            "button_ok": 2,
            "button_cancel": 1,
        }
        form_widget = dialog.layout().itemAt(0).widget()
        form_layout = form_widget.layout()
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

    def click_tree_item(self, item, qtbot, app_ui):
        if item.parent():
            item.parent().setExpanded(True)
        topleft = app_ui("account_tree").visualItemRect(item).topLeft()
        qtbot.mouseClick(
            app_ui("account_tree").viewport(), Qt.LeftButton, Qt.NoModifier, topleft
        )

    def click_table_cell(self, row, col, qtbot, app_ui, double_click=False):
        y_position = app_ui("table").rowViewportPosition(row) + 5
        x_position = app_ui("table").columnViewportPosition(col) + 10
        point = QtCore.QPoint(x_position, y_position)
        if double_click:
            # First click is for focusing on table, then double-click on cell
            qtbot.mouseClick(
                app_ui("table").viewport(), Qt.LeftButton, Qt.NoModifier, point
            )
            qtbot.mouseDClick(
                app_ui("table").viewport(), Qt.LeftButton, Qt.NoModifier, point
            )
        else:
            qtbot.mouseClick(
                app_ui("table").viewport(), Qt.LeftButton, Qt.NoModifier, point
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
        self.click_table_cell(1, 5, qtbot, app_ui)

    def test_transactions_add_transaction_cancel(self, app_ui, qtbot, qapp, app_db):
        def handle_dialog():
            # Get the different fields
            dialog = qapp.activeWindow()
            account_label = self.get_dialog_item(dialog, "account", "label")
            account = self.get_dialog_item(dialog, "account", "field")
            date_label = self.get_dialog_item(dialog, "date", "label")
            date = self.get_dialog_item(dialog, "date", "field")
            label_label = self.get_dialog_item(dialog, "label", "label")
            label = self.get_dialog_item(dialog, "label", "field")
            transaction_type_label = self.get_dialog_item(dialog, "type", "label")
            transaction_type = self.get_dialog_item(dialog, "type", "field")
            quantity_label = self.get_dialog_item(dialog, "quantity", "label")
            quantity = self.get_dialog_item(dialog, "quantity", "field")
            share_label = self.get_dialog_item(dialog, "share", "label")
            share = self.get_dialog_item(dialog, "share", "field")
            unit_price_label = self.get_dialog_item(dialog, "unit_price", "label")
            unit_price = self.get_dialog_item(dialog, "unit_price", "field")
            known_price_label = self.get_dialog_item(
                dialog, "known_unit_price", "label"
            )
            known_price = self.get_dialog_item(dialog, "known_unit_price", "field")
            cash_delta_label = self.get_dialog_item(dialog, "currency_delta", "label")
            cash_delta = self.get_dialog_item(dialog, "currency_delta", "field")

            button_cancel = self.get_dialog_item(dialog, "button_cancel")

            assert isinstance(account_label, QtWidgets.QLabel), "Account label OK"
            assert isinstance(account, QtWidgets.QComboBox), "Account OK"
            assert isinstance(date_label, QtWidgets.QLabel), "Date label OK"
            assert isinstance(date, QtWidgets.QDateEdit), "Date OK"
            assert isinstance(label_label, QtWidgets.QLabel), "Label label OK"
            assert isinstance(label, QtWidgets.QLineEdit), "Label OK"
            assert isinstance(transaction_type_label, QtWidgets.QLabel), "Type label OK"
            assert isinstance(transaction_type, QtWidgets.QComboBox), "Type OK"
            assert isinstance(quantity_label, QtWidgets.QLabel), "Quantity label OK"
            assert isinstance(quantity, QtWidgets.QDoubleSpinBox), "Quantity OK"
            assert isinstance(share_label, QtWidgets.QLabel), "Share label OK"
            assert isinstance(share, QtWidgets.QComboBox), "Share OK"
            assert isinstance(unit_price_label, QtWidgets.QLabel), "Unit price label OK"
            assert isinstance(unit_price, QtWidgets.QDoubleSpinBox), "Unit price OK"
            assert isinstance(
                known_price_label, QtWidgets.QLabel
            ), "Known price label OK"
            assert isinstance(known_price, QtWidgets.QComboBox), "Known price OK"
            assert isinstance(cash_delta_label, QtWidgets.QLabel), "Cash delta label OK"
            assert isinstance(cash_delta, QtWidgets.QDoubleSpinBox), "Cash delta OK"

            # Click Cancel & select various elements (this triggers the restore of selection)
            qtbot.mouseClick(button_cancel, Qt.LeftButton, Qt.NoModifier)
            self.click_tree_item(app_ui("main_account"), qtbot, app_ui)
            self.click_tree_item(app_ui("account_historyACN"), qtbot, app_ui)

            # Check results
            with pytest.raises(sqlalchemy.exc.NoResultFound):
                app_db.transaction_get_by_id(15)

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(200, handle_dialog)
        index = app_ui("table").model.index(0, 0)
        self.click_table_cell(
            app_ui("table").model.rowCount(index) - 1, 0, qtbot, app_ui
        )

    def test_transactions_add_transaction_double_click(
        self, app_ui, qtbot, qapp, app_db
    ):
        def handle_dialog():
            # Get the different fields
            dialog = qapp.activeWindow()
            button_cancel = self.get_dialog_item(dialog, "button_cancel")
            account = self.get_dialog_item(dialog, "account", "field")

            # Check existing values
            assert account.currentText() == "", "Account OK"

            # Click Cancel
            qtbot.mouseClick(button_cancel, Qt.LeftButton, Qt.NoModifier)

            # Check results
            with pytest.raises(sqlalchemy.exc.NoResultFound):
                app_db.transaction_get_by_id(15)

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(200, handle_dialog)
        # Double-click on "add transaction" (twice to handle focus properly)
        y_position = app_ui("table").rowViewportPosition(5) + 5
        x_position = app_ui("table").columnViewportPosition(0) + 10
        point = QtCore.QPoint(x_position, y_position)
        qtbot.mouseDClick(
            app_ui("table").viewport(), Qt.LeftButton, Qt.NoModifier, point
        )
        qtbot.mouseDClick(
            app_ui("table").viewport(), Qt.LeftButton, Qt.NoModifier, point
        )

    def test_transactions_add_transaction(self, app_ui, qtbot, qapp, app_db):
        def handle_dialog():
            # Get the different fields
            dialog = qapp.activeWindow()
            account = self.get_dialog_item(dialog, "account", "field")
            date = self.get_dialog_item(dialog, "date", "field")
            label = self.get_dialog_item(dialog, "label", "field")
            transaction_type = self.get_dialog_item(dialog, "type", "field")
            quantity = self.get_dialog_item(dialog, "quantity", "field")
            share = self.get_dialog_item(dialog, "share", "field")
            unit_price = self.get_dialog_item(dialog, "unit_price", "field")
            cash_delta = self.get_dialog_item(dialog, "currency_delta", "field")

            button_ok = self.get_dialog_item(dialog, "button_ok")

            # Enter data
            account.setCurrentText("Main account")
            date.setDate(datetime.date(2023, 6, 15))
            label.setText("Test transaction")
            transaction_type.setCurrentText("Asset buy / subscription")
            quantity.setValue(31)
            share.setCurrentText("Accenture (NYSE:ACN)")
            unit_price.setValue(100)

            # Check calculation of cash delta
            assert cash_delta.value() == 3100, "Total cash impact OK"

            # Click OK & filter on the main account
            qtbot.mouseClick(button_ok, Qt.LeftButton, Qt.NoModifier)
            self.click_tree_item(app_ui("main_account"), qtbot, app_ui)

            # Check results
            index = app_ui("table").model.index(1, 1)
            assert app_ui("table").model.rowCount(index) == 7, "Row count OK"
            assert app_ui("table_5_0") == "Main account", "Account name OK"
            assert app_ui("table_5_1") == 15, "Transaction ID OK"
            assert app_ui("table_5_2") == QtCore.QDate(
                2023, 6, 15
            ), "Transaction date OK"
            assert (
                app_ui("table_5_3") == "Asset buy / subscription"
            ), "Transaction type OK"
            assert app_ui("table_5_4") == "Test transaction", "Transaction label OK"
            assert app_ui("table_5_5") == "31,00000", "Transaction # shares OK"
            assert (
                app_ui("table_5_6") == "Accenture (NYSE:ACN)"
            ), "Transaction share name OK"
            assert app_ui("table_5_7") == "71,00000", "Transaction Balance (shares) OK"
            assert app_ui("table_5_8") == "100,00 EUR", "Transaction unit price OK"
            assert app_ui("table_5_9") == "-3\u202f100,00 EUR", "Transaction # cash OK"
            assert app_ui("table_5_10") == "10,00 EUR", "Transaction Balance (cash) OK"
            # Check save is done in DB
            app_db.transaction_get_by_id(15)

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(200, handle_dialog)
        index = app_ui("table").model.index(0, 0)
        self.click_table_cell(
            app_ui("table").model.rowCount(index) - 1, 0, qtbot, app_ui
        )

    def test_transactions_add_transaction_negative_cash(
        self, app_ui, qtbot, qapp, app_db
    ):
        def handle_dialog():
            # Get the different fields
            dialog = qapp.activeWindow()
            account = self.get_dialog_item(dialog, "account", "field")
            date = self.get_dialog_item(dialog, "date", "field")
            label = self.get_dialog_item(dialog, "label", "field")
            transaction_type = self.get_dialog_item(dialog, "type", "field")
            quantity = self.get_dialog_item(dialog, "quantity", "field")
            share = self.get_dialog_item(dialog, "share", "field")
            unit_price = self.get_dialog_item(dialog, "unit_price", "field")

            button_ok = self.get_dialog_item(dialog, "button_ok")

            # Enter data
            account.setCurrentText("Main account")
            date.setDate(datetime.date(2023, 6, 15))
            label.setText("Test transaction")
            transaction_type.setCurrentText("Asset buy / subscription")
            quantity.setValue(310)
            share.setCurrentText("Accenture (NYSE:ACN)")
            unit_price.setValue(100)

            # Click OK & check error messages
            qtbot.mouseClick(button_ok, Qt.LeftButton, Qt.NoModifier)
            cash_error = self.get_dialog_item(dialog, "currency_delta", "error")
            assert cash_error.text() == "Cash balance negative", "Error message OK"
            dialog.close()

            # Check save is done in DB
            with pytest.raises(sqlalchemy.exc.NoResultFound):
                app_db.transaction_get_by_id(15)

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(200, handle_dialog)
        index = app_ui("table").model.index(0, 0)
        self.click_table_cell(
            app_ui("table").model.rowCount(index) - 1, 0, qtbot, app_ui
        )

    def test_transactions_add_transaction_negative_asset(
        self, app_ui, qtbot, qapp, app_db
    ):
        def handle_dialog():
            # Get the different fields
            dialog = qapp.activeWindow()
            account = self.get_dialog_item(dialog, "account", "field")
            date = self.get_dialog_item(dialog, "date", "field")
            label = self.get_dialog_item(dialog, "label", "field")
            transaction_type = self.get_dialog_item(dialog, "type", "field")
            quantity = self.get_dialog_item(dialog, "quantity", "field")
            share = self.get_dialog_item(dialog, "share", "field")
            unit_price = self.get_dialog_item(dialog, "unit_price", "field")

            button_ok = self.get_dialog_item(dialog, "button_ok")

            # Enter data
            account.setCurrentText("Main account")
            date.setDate(datetime.date(2023, 6, 15))
            label.setText("Test transaction")
            transaction_type.setCurrentText("Asset sell")
            quantity.setValue(310)
            share.setCurrentText("Accenture (NYSE:ACN)")
            unit_price.setValue(100)

            # Click OK & check error messages
            qtbot.mouseClick(button_ok, Qt.LeftButton, Qt.NoModifier)
            quantity_error = self.get_dialog_item(dialog, "quantity", "error")
            assert quantity_error.text() == "Asset balance negative", "Error message OK"
            dialog.close()

            # Check save is done in DB
            with pytest.raises(sqlalchemy.exc.NoResultFound):
                app_db.transaction_get_by_id(15)

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(200, handle_dialog)
        index = app_ui("table").model.index(0, 0)
        self.click_table_cell(
            app_ui("table").model.rowCount(index) - 1, 0, qtbot, app_ui
        )

    def test_transactions_add_transaction_known_price(
        self, app_ui, qtbot, qapp, app_db
    ):
        def handle_dialog():
            # Get the different fields
            dialog = qapp.activeWindow()
            account = self.get_dialog_item(dialog, "account", "field")
            date = self.get_dialog_item(dialog, "date", "field")
            transaction_type = self.get_dialog_item(dialog, "type", "field")
            share = self.get_dialog_item(dialog, "share", "field")
            known_unit_price = self.get_dialog_item(dialog, "known_unit_price", "field")

            button_cancel = self.get_dialog_item(dialog, "button_cancel")

            # Share filled in, account empty
            transaction_type.setCurrentText("Asset buy / subscription")
            share.setCurrentText("Accenture (NYSE:ACN)")
            date.setDate(datetime.date(2023, 6, 15))
            assert known_unit_price.count() == 0, "No known price"

            # Account now filled in
            account.setCurrentText("Main account")
            date.setDate(datetime.date.today())
            assert known_unit_price.count() == 2, "1 known price (+ 1 empty value)"

            # Close dialog
            qtbot.mouseClick(button_cancel, Qt.LeftButton, Qt.NoModifier)

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(200, handle_dialog)
        index = app_ui("table").model.index(0, 0)
        self.click_table_cell(
            app_ui("table").model.rowCount(index) - 1, 0, qtbot, app_ui
        )

    def test_transactions_add_transaction_known_price_select(
        self, app_ui, qtbot, qapp, app_db
    ):
        def handle_dialog():
            # Get the different fields
            dialog = qapp.activeWindow()
            account = self.get_dialog_item(dialog, "account", "field")
            date = self.get_dialog_item(dialog, "date", "field")
            transaction_type = self.get_dialog_item(dialog, "type", "field")
            share = self.get_dialog_item(dialog, "share", "field")
            known_unit_price = self.get_dialog_item(dialog, "known_unit_price", "field")
            unit_price = self.get_dialog_item(dialog, "unit_price", "field")

            button_cancel = self.get_dialog_item(dialog, "button_cancel")

            # Generate known prices
            transaction_type.setCurrentText("Asset buy / subscription")
            share.setCurrentText("Accenture (NYSE:ACN)")
            account.setCurrentText("Main account")
            date.setDate(datetime.date.today() + datetime.timedelta(days=-1))

            known_unit_price.setCurrentIndex(1)
            assert unit_price.value() == 10, "Known price is selected"

            # Close dialog
            qtbot.mouseClick(button_cancel, Qt.LeftButton, Qt.NoModifier)

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(200, handle_dialog)
        index = app_ui("table").model.index(0, 0)
        self.click_table_cell(
            app_ui("table").model.rowCount(index) - 1, 0, qtbot, app_ui
        )

    def test_transactions_edit_transaction(self, app_ui, qtbot, qapp, app_db):
        def handle_dialog():
            # Get the different fields
            dialog = qapp.activeWindow()
            account = self.get_dialog_item(dialog, "account", "field")
            date = self.get_dialog_item(dialog, "date", "field")
            label = self.get_dialog_item(dialog, "label", "field")
            transaction_type = self.get_dialog_item(dialog, "type", "field")
            quantity = self.get_dialog_item(dialog, "quantity", "field")
            share = self.get_dialog_item(dialog, "share", "field")
            unit_price = self.get_dialog_item(dialog, "unit_price", "field")

            button_ok = self.get_dialog_item(dialog, "button_ok")

            # Check existing values
            assert account.currentText() == "Main account", "Account OK"
            assert date.date().toString(Qt.ISODate) == "2020-04-15", "Date OK"
            assert label.text() == "Get funded", "Label OK"
            assert transaction_type.currentText() == "Company funding - Cash", "Type OK"
            assert quantity.value() == 100, "Quantity OK"
            assert share.currentText() == "Euro (EUR)", "Share OK"
            assert unit_price.value() == 1, "Unit price OK"

            # Enter data
            label.setText("Get well funded")
            quantity.setValue(150)

            # Click OK & filter on the main account
            qtbot.mouseClick(button_ok, Qt.LeftButton, Qt.NoModifier)
            self.click_tree_item(app_ui("main_account"), qtbot, app_ui)

            # Check results
            index = app_ui("table").model.index(1, 1)
            assert app_ui("table").model.rowCount(index) == 6, "Row count OK"
            assert app_ui("table_4_4") == "Get well funded", "Transaction label OK"
            assert app_ui("table_4_5") == "-", "Transaction # shares OK"
            assert app_ui("table_4_9") == "150,00 EUR", "Transaction # cash OK"
            assert (
                app_ui("table_4_10") == "3\u202f160,00 EUR"
            ), "Transaction Balance (cash) OK"
            # Check save is done in DB
            transaction = app_db.transaction_get_by_id(5)
            assert transaction.label == "Get well funded", "Transaction label updated"

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(200, handle_dialog)
        self.click_tree_item(app_ui("main_account"), qtbot, app_ui)
        self.click_table_cell(4, 0, qtbot, app_ui, True)

    def test_transactions_copy_transaction(self, app_ui, qtbot, qapp, app_db):
        def handle_dialog():
            # Get the different fields
            dialog = qapp.activeWindow()
            account = self.get_dialog_item(dialog, "account", "field")
            date = self.get_dialog_item(dialog, "date", "field")
            label = self.get_dialog_item(dialog, "label", "field")
            transaction_type = self.get_dialog_item(dialog, "type", "field")
            quantity = self.get_dialog_item(dialog, "quantity", "field")
            share = self.get_dialog_item(dialog, "share", "field")
            unit_price = self.get_dialog_item(dialog, "unit_price", "field")

            button_ok = self.get_dialog_item(dialog, "button_ok")

            # Check existing values
            assert account.currentText() == "Main account", "Account OK"
            assert date.date().toString(Qt.ISODate) == "2020-04-15", "Date OK"
            assert label.text() == "Get funded", "Label OK"
            assert transaction_type.currentText() == "Company funding - Cash", "Type OK"
            assert quantity.value() == 100, "Quantity OK"
            assert share.currentText() == "Euro (EUR)", "Share OK"
            assert unit_price.value() == 1, "Unit price OK"

            # Enter data
            label.setText("Get well funded")
            quantity.setValue(150)

            # Click OK & filter on the main account
            qtbot.mouseClick(button_ok, Qt.LeftButton, Qt.NoModifier)
            self.click_tree_item(app_ui("main_account"), qtbot, app_ui)

            # Check results
            index = app_ui("table").model.index(1, 1)
            assert app_ui("table").model.rowCount(index) == 7, "Row count OK"
            assert app_ui("table_5_4") == "Get well funded", "Transaction label OK"
            assert app_ui("table_5_5") == "-", "Transaction # shares OK"
            assert app_ui("table_5_9") == "150,00 EUR", "Transaction # cash OK"
            assert (
                app_ui("table_5_10") == "3\u202f260,00 EUR"
            ), "Transaction Balance (cash) OK"
            # Check save is done in DB
            transaction = app_db.transaction_get_by_id(15)
            assert transaction.label == "Get well funded", "Transaction label updated"

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(200, handle_dialog)
        self.click_tree_item(app_ui("main_account"), qtbot, app_ui)
        self.click_table_cell(4, 11, qtbot, app_ui)

    def test_transactions_copy_transaction_cancel(self, app_ui, qtbot, qapp, app_db):
        def handle_dialog():
            # Get the different fields
            dialog = qapp.activeWindow()
            button_cancel = self.get_dialog_item(dialog, "button_cancel")

            # Click cancel, then click on tree twice to refresh the screen
            qtbot.mouseClick(button_cancel, Qt.LeftButton, Qt.NoModifier)
            index = app_ui("table").model.index(1, 1)
            self.click_tree_item(app_ui("main_account"), qtbot, app_ui)
            self.click_tree_item(app_ui("main_account"), qtbot, app_ui)

            # Check results
            assert app_ui("table").model.rowCount(index) == 6, "Row count OK"
            with pytest.raises(sqlalchemy.exc.NoResultFound):
                app_db.transaction_get_by_id(15)

        # Trigger the display of the dialog (click on label)
        QtCore.QTimer.singleShot(200, handle_dialog)
        self.click_tree_item(app_ui("main_account"), qtbot, app_ui)
        self.click_table_cell(4, 11, qtbot, app_ui)

    def test_transactions_delete_transaction_confirm(
        self, app_ui, qtbot, app_db, monkeypatch
    ):
        # Monkeypatch to approve automatically
        monkeypatch.setattr(
            QtWidgets.QMessageBox,
            "critical",
            lambda *args, **kwargs: QtWidgets.QMessageBox.Yes,
        )

        # Trigger the display of the dialog (click on label)
        self.click_tree_item(app_ui("main_account"), qtbot, app_ui)
        index = app_ui("table").model.index(1, 1)
        self.click_table_cell(4, 12, qtbot, app_ui)
        # Check results
        assert app_ui("table").model.rowCount(index) == 5, "Row count OK"
        with pytest.raises(sqlalchemy.exc.NoResultFound):
            app_db.transaction_get_by_id(5)

    def test_transactions_delete_transaction_cancel(
        self, app_ui, qtbot, app_db, monkeypatch
    ):
        # Monkeypatch to cancel automatically
        monkeypatch.setattr(
            QtWidgets.QMessageBox,
            "critical",
            lambda *args, **kwargs: QtWidgets.QMessageBox.No,
        )

        # Trigger the display of the dialog (click on label)
        self.click_tree_item(app_ui("main_account"), qtbot, app_ui)
        index = app_ui("table").model.index(1, 1)
        self.click_table_cell(4, 12, qtbot, app_ui)
        # Check results
        assert app_ui("table").model.rowCount(index) == 6, "Row count OK"
        assert app_db.transaction_get_by_id(5) is not None, "Transaction still exists"


if __name__ == "__main__":
    pytest.main(["-s", __file__])
