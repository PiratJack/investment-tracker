import gettext
import datetime

from PyQt5.QtCore import Qt

import models.transaction
from models.base import ValidationWarningException
from controllers.editcontroller import EditController

_ = gettext.gettext


class TransactionController(EditController):
    name = _("Transaction")

    fields = {
        "account_id": {
            "label": _("Account"),
            "type": "list",
            "mandatory": True,
        },
        "date": {
            "label": _("Date"),
            "type": "date",
            "mandatory": True,
        },
        "label": {
            "label": _("Label"),
            "type": "text",
        },
        "type": {
            "label": _("Type"),
            "type": "list",
            "mandatory": True,
        },
        "quantity": {
            "label": _("Asset delta"),
            "type": "positivefloat",
            "mandatory": True,
        },
        "share_id": {
            "label": _("Share"),
            "type": "sharelist",
            "mandatory": True,
        },
        "unit_price": {
            "label": _("Rate"),
            "type": "positivefloat",
            "mandatory": True,
        },
        "known_unit_price": {
            "label": _("Known rate"),
            "type": "list",
        },
        "currency_delta": {
            "label": _("Currency delta"),
            "type": "positivefloat",
            "mandatory": True,
        },
    }

    error_widgets = []

    def __init__(self, parent_controller, transaction_id=0):
        self.parent_controller = parent_controller
        self.database = parent_controller.database
        self.transaction_id = int(transaction_id)

        # Define list of values
        self.fields["account_id"]["possible_values"] = [
            (g.name, g.id)
            for g in self.database.accounts_get(with_hidden=True, with_disabled=True)
        ]
        self.fields["type"]["possible_values"] = [
            (g.value["name"], g.name) for g in models.transaction.TransactionTypes
        ]

        # Get existing data & define default field values
        if transaction_id:
            self.item = self.database.transaction_get_by_id(transaction_id)
        else:
            self.item = models.transaction.Transaction()
        self.fields["account_id"]["default"] = self.item.account_id
        self.fields["date"]["default"] = self.item.date
        self.fields["label"]["default"] = self.item.label
        if self.item.type:
            self.fields["type"]["default"] = self.item.type.name
        else:
            if "default" in self.fields["type"]:
                del self.fields["type"]["default"]
        self.fields["quantity"]["default"] = self.item.quantity
        self.fields["share_id"]["default"] = (
            self.item.share_id if self.item.share_id else 0
        )
        self.fields["unit_price"]["default"] = self.item.unit_price

        for field in self.fields.values():
            if field.get("default", 0) is None:
                del field["default"]

        # Add triggers (hide/show fields, calculations, ...)
        self.fields["account_id"]["onchange"] = self.on_change_any_value
        self.fields["share_id"]["onchange"] = self.on_change_any_value
        self.fields["type"]["onchange"] = self.on_change_type
        self.fields["quantity"]["onchange"] = self.on_change_quantity_or_unit_price
        self.fields["unit_price"]["onchange"] = self.on_change_quantity_or_unit_price
        self.fields["currency_delta"]["onchange"] = self.on_change_currency_delta

        self.fields["date"]["onchange"] = self.on_change_share_or_date
        self.fields["share_id"]["onchange"] = self.on_change_share_or_date
        self.fields["known_unit_price"]["onchange"] = self.on_change_known_unit_price

    def on_change_any_value(self):
        self.clear_errors()

    def on_change_type(self):
        # Somewhat, doing this increases the height to the wanted one
        self.window.sizeHint()

        # Hide all type-dependent fields
        value = self.fields["type"]["widget"].currentData()
        for field_id in (
            "quantity",
            "share_id",
            "unit_price",
            "known_unit_price",
            "currency_delta",
        ):
            self.fields[field_id]["widget"].hide()
            self.form_layout.labelForField(self.fields[field_id]["widget"]).hide()

        # Display type-dependent fields
        transaction_type = [
            v for v in models.transaction.TransactionTypes if v.name == value
        ]
        if transaction_type:
            transaction_type = transaction_type[0].value
            if transaction_type["has_asset"]:
                for field_id in ("quantity", "share_id"):
                    self.fields[field_id]["widget"].show()
                    self.form_layout.labelForField(
                        self.fields[field_id]["widget"]
                    ).show()

            if transaction_type["impact_currency"]:
                for field_id in ("currency_delta",):
                    self.fields[field_id]["widget"].show()
                    self.form_layout.labelForField(
                        self.fields[field_id]["widget"]
                    ).show()

            if transaction_type["has_asset"] and transaction_type["impact_currency"]:
                for field_id in ("unit_price", "known_unit_price"):
                    self.fields[field_id]["widget"].show()
                    self.form_layout.labelForField(
                        self.fields[field_id]["widget"]
                    ).show()

        self.on_change_any_value()

        # Increase height if needed
        if self.window.height() <= self.window.sizeHint().height():
            self.window.resize(self.window.sizeHint())

    # Calculate total currency impact when quantity / unit price change
    def on_change_quantity_or_unit_price(self):
        total = self.get_quantity() * self.get_unit_price()
        self.fields["currency_delta"]["widget"].setValue(total)

        self.on_change_any_value()

    # Calculate unit price when total changes
    def on_change_currency_delta(self):
        try:
            unit_price = self.get_currency_delta() / self.get_quantity()
            self.fields["unit_price"]["widget"].setValue(unit_price)
        except ZeroDivisionError:
            pass

        self.on_change_any_value()

    # Displays known share prices
    def on_change_share_or_date(self):
        date = datetime.datetime.fromisoformat(
            self.fields["date"]["widget"].date().toString(Qt.ISODate)
        )

        # Get share
        share_id = self.fields["share_id"]["widget"].currentData()
        if share_id == 0:
            return

        # Get account (for base currency)
        account_id = self.fields["account_id"]["widget"].currentData()
        if account_id == 0:
            return
        account = self.database.account_get_by_id(account_id)
        currency = account.base_currency
        if not currency:
            return

        prices = self.database.share_prices_get(
            share_id=share_id, currency=currency, start_date=date
        )
        prices = sorted(prices, key=lambda price: price.date, reverse=True)

        self.fields["known_unit_price"]["widget"].clear()
        self.fields["known_unit_price"]["widget"].addItem("", -1)
        for price in prices:
            self.fields["known_unit_price"]["widget"].addItem(price.short_name(), price)

        self.on_change_any_value()

    # User selects a known share price => update unit price
    def on_change_known_unit_price(self):
        chosen_price = self.fields["known_unit_price"]["widget"].currentData()
        if chosen_price and not isinstance(chosen_price, int):
            self.fields["unit_price"]["widget"].setValue(chosen_price.price)

        self.on_change_any_value()

    # Raise warning if cash or asset balance becomes negative
    def on_validation_end(self):
        if not self.item.account:
            account = self.database.account_get_by_id(self.item.account_id)
        else:
            account = self.item.account
        balance = account.balance_before_staged_transaction(self.item)

        if balance[0] + self.item.cash_total < 0:
            raise ValidationWarningException(
                "Cash balance negative", self.item, "currency_delta", self.item.quantity
            )
        if balance[1] + self.item.asset_total < 0:
            raise ValidationWarningException(
                "Asset balance negative", self.item, "quantity", self.item.quantity
            )

    def get_quantity(self):
        return self.fields["quantity"]["widget"].value()

    def get_unit_price(self):
        return self.fields["unit_price"]["widget"].value()

    def get_currency_delta(self):
        return self.fields["currency_delta"]["widget"].value()

    # Ensure entered data matches transaction's database fields
    def save(self):
        value = self.fields["type"]["widget"].currentData()
        transaction_type = [
            v for v in models.transaction.TransactionTypes if v.name == value
        ]
        if transaction_type:
            transaction_type = transaction_type[0].value
            if (
                not transaction_type["has_asset"]
                and transaction_type["impact_currency"]
            ):
                self.fields["quantity"]["widget"].setValue(
                    self.fields["currency_delta"]["widget"].value()
                )
                self.fields["unit_price"]["widget"].setValue(1)

        super().save()

    def close(self):
        self.window.close()
