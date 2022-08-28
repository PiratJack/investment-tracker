"""Various delegates for display in tables

Classes
----------
DateDelegate
    Displays an editable date
ShareDelegate
    Displays a dropdown of shares based on controllers.widgets.ShareComboBox
"""
import datetime

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from .sharecombobox import ShareComboBox


class DateDelegate(QtWidgets.QItemDelegate):
    """Displays an editable date

    Methods
    -------
    createEditor (parent, option, index)
        Displays a widget to edit dates
    setEditorData (editor, index)
        Sets the date in the editor, based on the model's data
    setModelData (editor, index)
        Saves the user entry in the model data
    """

    def createEditor(self, parent, option, index):
        """Displays a widget to edit dates

        Parameters
        ----------
        parent : QtWidgets.QWidget
            The parent widget (here, the table)
        option : QtWidgets.QStyleOptionViewItem
            Parameters used to draw the editor (unused in this method)
        index : QtCore.QModelIndex
            A reference to the cell being edited
        """
        widget = QtWidgets.QDateEdit(parent)
        widget.setCalendarPopup(True)
        return widget

    def setEditorData(self, editor, index):
        """Sets the date in the editor, based on the model's data

        Calls inherited method if the editor is not a QDateEdit widget

        Parameters
        ----------
        editor : QtWidgets.QWidget
            The editor of the data
        index : QtCore.QModelIndex
            A reference to the cell being edited
        """
        if isinstance(editor, QtWidgets.QDateEdit):
            value = index.data(Qt.EditRole)
            if value:
                editor.setDate(value)
            else:
                editor.setDate(datetime.datetime.now())
            return
        super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        """Saves the user entry in the model data

        Calls inherited method if the editor is not a QDateEdit widget

        Parameters
        ----------
        editor : QtWidgets.QWidget
            The editor of the data
        model : QtCore.QAbstractItemModel
            The model being edited
        index : QtCore.QModelIndex
            A reference to the cell being edited
        """
        if isinstance(editor, QtWidgets.QDateEdit):
            date_date = editor.date().toPyDate()
            model.setData(index, date_date, Qt.EditRole)
            return
        super().setModelData(editor, model, index)


class ShareDelegate(QtWidgets.QItemDelegate):
    """Displays a dropdown of shares based on controllers.widgets.ShareComboBox

    Methods
    -------
    __init__ (parent, database)
        Stores the database reference
    createEditor (parent, option, index)
        Displays a widget to edit dates
    setEditorData (editor, index)
        Sets the date in the editor, based on the model's data
    setModelData (editor, index)
        Saves the user entry in the model data
    """

    def __init__(self, parent, database):
        """Stores the database reference"""
        super().__init__(parent)
        self.database = database

    def createEditor(self, parent, option, index):
        """Displays a widget to select a share

        Parameters
        ----------
        parent : QtWidgets.QWidget
            The parent widget (here, the table)
        option : QtWidgets.QStyleOptionViewItem
            Parameters used to draw the editor (unused in this method)
        index : QtCore.QModelIndex
            A reference to the cell being edited
        """
        widget = ShareComboBox(self.database, parent=parent)
        return widget

    def setEditorData(self, editor, index):
        """Sets the share in the editor, based on the model's data

        Calls inherited method if the editor is not a ShareComboBox widget

        Parameters
        ----------
        editor : QtWidgets.QWidget
            The editor of the data
        index : QtCore.QModelIndex
            A reference to the cell being edited
        """
        if isinstance(editor, ShareComboBox):
            value = index.data(Qt.EditRole)
            if value:
                combobox_index = editor.findData(value)
                editor.setCurrentIndex(combobox_index)
            return
        super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        """Saves the user entry in the model data

        Calls inherited method if the editor is not a ShareComboBox widget

        Parameters
        ----------
        editor : QtWidgets.QWidget
            The editor of the data
        model : QtCore.QAbstractItemModel
            The model being edited
        index : QtCore.QModelIndex
            A reference to the cell being edited
        """
        if isinstance(editor, ShareComboBox):
            share_id = editor.currentData()
            model.setData(index, share_id, Qt.EditRole)
            return
        super().setModelData(editor, model, index)
