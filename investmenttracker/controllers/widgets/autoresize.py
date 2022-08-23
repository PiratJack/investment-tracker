"""Helper class for auto-rezising columns in tables or trees

Classes
----------
AutoResize
    Helper class for auto-rezising columns in tables or trees
"""
import gettext

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

_ = gettext.gettext


class AutoResize:
    """Helper class for auto-rezising columns in tables or trees

    Attributes
    ----------
    columns : list of dicts
        Columns to display. The size key is the only one used here

    Methods
    -------
    resizeEvent (self, event)
        Handler for resize events
    set_column_sizes (self, event)
        Resizes columns based on the columns attribute
    """

    columns = [
        {
            "name": _("ID"),
            "size": 0,
            "alignment": Qt.AlignLeft,
        },
    ]

    def resizeEvent(self, event):
        QtWidgets.QMainWindow.resizeEvent(self, event)
        self.set_column_sizes()

    def set_column_sizes(self):
        grid_width = (
            self.width() - sum([x["size"] for x in self.columns if x["size"] > 1]) - 10
        )
        for column, field in enumerate(self.columns):
            if "size" not in field:
                self.hideColumn(column)
            if field["size"] == 0:
                self.hideColumn(column)
            elif field["size"] < 1:
                self.setColumnWidth(column, int(grid_width * field["size"]))
            else:
                self.setColumnWidth(column, field["size"])
