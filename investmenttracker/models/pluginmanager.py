"""Loads & manages plugins

Classes
----------
PluginManager
    Loads & manages plugins
"""

import os
import gettext
import logging
import importlib

_ = gettext.gettext
logger = logging.getLogger(__name__)


class PluginManager:
    """Loads & manages plugins

    Attributes
    ----------
    plugin_folder : str
        Where plugins are stored
    plugins : dict of modules
        Python modules used as plugins

    Methods
    -------
    __init__
        Loads plugins within the designated folder
    find_plugins (path)
        Reads a given folder to find plugins to load
    """

    plugins = {}

    def __init__(self, path):
        """Loads plugins within the designated folder"""
        logger.debug("PluginManager.init")
        self.plugin_folder = path

    def find_plugins(self):
        """Reads a given folder to find plugins to load

        Parameters
        ----------
        path : str
            The path to explore (will do nothing if it's not a folder)
        """
        logger.debug(f"PluginManager.find_plugins")
        for element in os.listdir(self.plugin_folder):
            full_path = os.path.join(self.plugin_folder, element)
            module_name = element[:-3]
            if os.path.isfile(full_path):
                if full_path.lower().endswith(".py"):
                    self.plugins[module_name] = importlib.import_module(
                        "plugins." + module_name, "plugins"
                    )
        logger.debug(f"PluginManager.find_plugins done : {self.plugins.keys()}")
