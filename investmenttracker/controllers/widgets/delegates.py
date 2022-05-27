import datetime

from PyQt5.QtWidgets import (
    QDateEdit,
    QItemDelegate,
)
from PyQt5.QtCore import QDate, Qt

from .sharecombobox import ShareComboBox


class DateDelegate(QItemDelegate):
    def createEditor(self, parent, option, index):
        widget = QDateEdit(parent)
        widget.setCalendarPopup(True)
        return widget

    def setEditorData(self, editor, index):
        if isinstance(editor, QDateEdit):
            editor.setDate(index.data(Qt.EditRole))
            return
        super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, QDateEdit):
            date_date = editor.date().toPyDate()
            model.setData(index, date_date, Qt.EditRole)
            return
        super().setModelData(editor, model, index)


class ShareDelegate(QItemDelegate):
    def __init__(self, parent, database):
        super().__init__(parent)
        self.database = database

    def createEditor(self, parent, option, index):
        widget = ShareComboBox(self.database, parent=parent)
        return widget

    def setEditorData(self, editor, index):
        if isinstance(editor, ShareComboBox):
            combobox_index = editor.findData(index.data(Qt.EditRole))
            editor.setCurrentIndex(combobox_index)
            return
        super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, ShareComboBox):
            share_id = editor.currentData()
            model.setData(index, share_id, Qt.EditRole)
            return
        super().setModelData(editor, model, index)
