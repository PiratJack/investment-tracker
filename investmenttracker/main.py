"""Main application module"""

import logging
import gettext
import sys
import os
import platformdirs
import PyQt5

import controllers.mainwindow
import models.database
import models.pluginmanager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Define some constants
PLUGIN_FOLDER = os.path.join(os.path.dirname(__file__), "plugins")
DATABASE_FILE = "sandbox.sqlite"
if "--real" in sys.argv:
    os.makedirs(
        platformdirs.user_data_dir("piratjack-investment-tracker", "PiratJack"),
        exist_ok=True,
    )
    DATABASE_FILE = (
        platformdirs.user_data_dir("piratjack-investment-tracker", "PiratJack")
        + "/prod.sqlite"
    )
LOCALE_FOLDER = os.path.dirname(os.path.realpath(__file__)) + "/locale"
STYLESHEET_FILE = os.path.dirname(os.path.realpath(__file__)) + "/assets/style/app.css"

# Setup translation
gettext.bindtextdomain("messages", LOCALE_FOLDER)
gettext.translation("messages", localedir=LOCALE_FOLDER).install()

# Load plugins
pluginmanager = models.pluginmanager.PluginManager(PLUGIN_FOLDER)
pluginmanager.find_plugins()

# Connect to database
database = models.database.Database(DATABASE_FILE, pluginmanager)

if __name__ == "__main__":
    # Change platform to avoid Wayland-related warning messages
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    with open(STYLESHEET_FILE, "r", encoding="UTF-8") as stylesheet:
        app.setStyleSheet(stylesheet.read())

    window = controllers.mainwindow.MainWindow(database, pluginmanager)
    window.showMaximized()
    app.exec_()
