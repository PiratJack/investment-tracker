"""Main window for display. Displays a toolbar to access the different screens

Classes
----------
MainWindow
    Main window for display. Displays a toolbar to access the different screens
"""

import gettext
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QSize

import controllers.accounts
import controllers.shares
import controllers.shareprices
import controllers.transactions
import controllers.graphs
import controllers.dashboard

_ = gettext.gettext


class MainWindow(QtWidgets.QMainWindow):
    """Main window for display. Displays a toolbar to access the different screens

    Attributes
    ----------
    database : models.database.Database
        A reference to the application database
    elements : dict of Controllers
        The different screens of the app
    layout : QtWidgets.QStackedLayout
        The main layout of the window
    toolbar : QtWidgets.QToolBar
        The toolbar displayed on the left
    """

    def __init__(self, database, pluginmanager):
        """Stores subwindows, displays toolbar and creates the layout

        Parameters
        ----------
        database : models.database.Database
            A reference to the application database
        """
        super().__init__()
        self.database = database

        self.elements = {
            "Accounts": controllers.accounts.AccountsController(self),
            "Shares": controllers.shares.SharesController(self),
            "Share Prices": controllers.shareprices.SharePricesController(self),
            "Transactions": controllers.transactions.TransactionsController(self),
            "Graphs": controllers.graphs.GraphsController(self),
            "Dashboard": controllers.dashboard.DashboardController(self),
        }
        for plugin_name, plugin in pluginmanager.plugins.items():
            if hasattr(plugin, "Controller"):
                controller = plugin.Controller(self)
                self.elements[controller.code] = controller

        self.setMinimumSize(800, 600)
        self.statusBar()

        self.setWindowTitle(_("Investment Tracker"))

        self.layout = QtWidgets.QStackedLayout()
        self.toolbar = QtWidgets.QToolBar(_("My main toolbar"))

        self.create_layout()
        self.layout.setCurrentIndex(0)

    def create_layout(self):
        """Arranges all elements in the window layout"""
        for element in self.elements.values():
            element_window = element.get_display_widget()
            if element_window:
                self.layout.addWidget(element_window)

        widget = QtWidgets.QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

        self.create_toolbar()

    def create_toolbar(self):
        """Creates the toolbar based on subwindows"""
        # Create the toolbar itself
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setOrientation(Qt.Vertical)
        self.toolbar.setIconSize(QSize(64, 64))

        self.addToolBar(Qt.LeftToolBarArea, self.toolbar)

        # Add buttons
        for element in self.elements.values():
            button = element.get_toolbar_button()
            if button:
                self.toolbar.addAction(button)

    def display_tab(self, tab):
        """User clicks on toolbar item => display the subwindow"""
        self.layout.setCurrentIndex(list(self.elements).index(tab))
        self.elements[tab].reload_data()
