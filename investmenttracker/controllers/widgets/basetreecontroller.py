import gettext

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt


_ = gettext.gettext


class BaseTreeController(QtWidgets.QTreeWidget):
    columns = {}

    def __init__(self, parent_controller):
        super().__init__()
        self.parent_controller = parent_controller
        self.database = parent_controller.database

        self.setColumnCount(len(self.columns))
        self.setHeaderLabels([_(col["name"]) for col in self.columns])

        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.AscendingOrder)

        self.itemDoubleClicked.connect(self.on_click_edit_button)
        self.setExpandsOnDoubleClick(False)

    def resizeEvent(self, event):
        QtWidgets.QMainWindow.resizeEvent(self, event)
        self.set_column_sizes(event)

    def set_column_sizes(self, event):
        grid_width = (
            self.width() - sum([x["size"] for x in self.columns if x["size"] > 1]) - 10
        )
        for i, column in enumerate(self.columns):
            if self.columns[i]["size"] == 0:
                self.hideColumn(i)
            elif self.columns[i]["size"] < 1:
                self.setColumnWidth(i, int(grid_width * self.columns[i]["size"]))
            else:
                self.setColumnWidth(i, self.columns[i]["size"])

    # If this is not implemented in child class, use default behavior
    def on_click_edit_button(self, tree_item):
        self.setExpandsOnDoubleClick(True)
