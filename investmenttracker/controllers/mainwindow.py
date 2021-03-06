from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QSize

import controllers.accounts
import controllers.shares
import controllers.shareprices
import controllers.transactions
import controllers.graphs


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, database):
        super(MainWindow, self).__init__()
        self.database = database

        self.elements = {
            "Accounts": controllers.accounts.AccountsController(self),
            "Shares": controllers.shares.SharesController(self),
            "Share Prices": controllers.shareprices.SharePricesController(self),
            "Transactions": controllers.transactions.TransactionsController(self),
            "Graphs": controllers.graphs.GraphsController(self),
        }

        self.setMinimumSize(800, 600)
        self.statusBar()

        self.setWindowTitle(_("Investment Tracker"))

        self.create_layout()
        self.layout.setCurrentIndex(0)

    def create_layout(self):
        self.layout = QtWidgets.QStackedLayout()

        for element in self.elements:
            element_window = self.elements[element].get_display_widget()
            if element_window:
                self.layout.addWidget(element_window)

        widget = QtWidgets.QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

        self.create_toolbar()

    def create_toolbar(self):
        # Create the toolbar itself
        self.toolbar = QtWidgets.QToolBar(_("My main toolbar"))
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setOrientation(Qt.Vertical)
        self.toolbar.setIconSize(QSize(128, 128))

        self.addToolBar(Qt.LeftToolBarArea, self.toolbar)

        # Add buttons
        for element in self.elements:
            button = self.elements[element].get_toolbar_button()
            if button:
                self.toolbar.addAction(button)

    def display_tab(self, tab):
        self.layout.setCurrentIndex(list(self.elements).index(tab))
