from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction


class GraphsController:
    name = "Graphs"

    def __init__(self, parent):
        self.parent = parent

    def get_toolbar_button(self, window):
        button = QAction(QIcon("assets/images/graphs.png"), _("Graphs"), window)
        button.setStatusTip(_("Analysis"))
        button.triggered.connect(lambda: window.display_tab(self.name))
        return button

    def get_display_widget(self, window):
        pass
