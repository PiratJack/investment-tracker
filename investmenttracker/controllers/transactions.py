from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction


class TransactionsController:
    name = "Transactions"

    def __init__(self, parent):
        self.parent = parent

    def get_toolbar_button(self, window):
        button = QAction(
            QIcon("assets/images/transactions.png"), _("Transactions"), window
        )
        button.setStatusTip(_("Display transactions"))
        button.triggered.connect(lambda: window.display_tab(self.name))
        return button

    def get_display_widget(self, window):
        pass
