import logging

from PyQt5.QtWidgets import QMainWindow, QStackedLayout, QToolBar, QWidget
from PyQt5.QtCore import Qt, QSize

import controllers.accounts


class MainWindow(QMainWindow):
    def __init__(self, database):
        super(MainWindow, self).__init__()
        self.database = database

        self.elements = {
            "Accounts": controllers.accounts.AccountsController(self),
            # TODO: Add windows for Shares, Transactions & Graphs
        }

        self.setMinimumSize(800, 600)
        self.statusBar()

        self.setWindowTitle(_("Investment Tracker"))

        self.create_layout()
        self.layout.setCurrentIndex(0)

    def create_layout(self):
        self.layout = QStackedLayout()

        for element in self.elements:
            element_window = self.elements[element].get_window()
            if element_window:
                self.layout.addWidget(element_window)

        widget = QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

        self.create_toolbar()

    def create_toolbar(self):
        # Create the toolbar itself
        self.toolbar = QToolBar(_("My main toolbar"))
        self.toolbar.movable = False
        self.toolbar.floatable = False
        self.toolbar.floating = False
        self.toolbar.orientation = Qt.Vertical
        self.toolbar.setIconSize(QSize(128, 128))

        self.addToolBar(Qt.LeftToolBarArea, self.toolbar)

        # Add buttons
        for element in self.elements:
            button = self.elements[element].get_toolbar_button()
            if button:
                self.toolbar.addAction(button)

    def display_tab(self, tab):
        self.layout.setCurrentIndex(list(self.elements).index(tab))
