import argparse
import gettext
import logging
import PyQt5
import sys

import controllers.console
import controllers.mainwindow
import models.database

# Define some constants
DATABASE_FILE = "data.sqlite"
LOCALE_FOLDER = "./locale"

# Setup translation (before import, otherwise it fails)
gettext.bindtextdomain("messages", LOCALE_FOLDER)
gettext.translation("messages", localedir=LOCALE_FOLDER).install()

# Process commandline arguments
log_level = controllers.console.get_log_level()
logging.basicConfig(level=log_level)

# Connect to database
database = models.database.Database(DATABASE_FILE)

if __name__ == "__main__":
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    window = controllers.mainwindow.MainWindow(database)
    window.showMaximized()
    app.exec_()
