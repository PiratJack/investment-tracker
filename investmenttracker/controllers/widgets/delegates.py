"""Various delegates for display in tables

Classes
----------
DateDelegate
    Displays an editable date
ShareDelegate
    Displays a dropdown of shares
"""
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from .sharecombobox import ShareComboBox


class DateDelegate(QtWidgets.QItemDelegate):
    """Delegate for dates"""

    def createEditor(self, parent, option, index):
        widget = QtWidgets.QDateEdit(parent)
        widget.setCalendarPopup(True)
        return widget

    def setEditorData(self, editor, index):
        if isinstance(editor, QtWidgets.QDateEdit):
            value = index.data(Qt.EditRole)
            if value:
                editor.setDate(value)
            return
        super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, QtWidgets.QDateEdit):
            date_date = editor.date().toPyDate()
            model.setData(index, date_date, Qt.EditRole)
            return
        super().setModelData(editor, model, index)


class ShareDelegate(QtWidgets.QItemDelegate):
    """Delegate for shares. Uses controllers.widgets.sharecombobox as base"""

    def __init__(self, parent, database):
        super().__init__(parent)
        self.database = database

    def createEditor(self, parent, option, index):
        widget = ShareComboBox(self.database, parent=parent)
        return widget

    def setEditorData(self, editor, index):
        if isinstance(editor, ShareComboBox):
            value = index.data(Qt.EditRole)
            if value:
                combobox_index = editor.findData(value)
                editor.setCurrentIndex(combobox_index)
            return
        super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, ShareComboBox):
            share_id = editor.currentData()
            model.setData(index, share_id, Qt.EditRole)
            return
        super().setModelData(editor, model, index)
