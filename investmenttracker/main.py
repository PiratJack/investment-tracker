import gettext
import sys
import os
import PyQt5

import controllers.mainwindow
import models.database

# Define some constants
DATABASE_FILE = "sandbox.sqlite"
# DATABASE_FILE = "prod.sqlite"
LOCALE_FOLDER = "./locale"
STYLESHEET_FILE = "./assets/style/app.css"

# Setup translation
gettext.bindtextdomain("messages", LOCALE_FOLDER)
gettext.translation("messages", localedir=LOCALE_FOLDER).install()

# TODO (major): when changes happen, clear all screens & reload data
# TODO (minor): Refactor code to have a base_QTableView

# Connect to database
database = models.database.Database(DATABASE_FILE)

if __name__ == "__main__":
    # Change platform to avoid Wayland-related warning messages
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    with open(STYLESHEET_FILE, "r", encoding="UTF-8") as stylesheet:
        app.setStyleSheet(stylesheet.read())

    window = controllers.mainwindow.MainWindow(database)
    window.showMaximized()
    app.exec_()
