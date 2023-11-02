# -*- coding: utf-8 -*-
"""
/***************************************************************************
 reszletKereso
                                 A QGIS plugin
 Kiválasztott erdőrészlet réteg elemei közötti keresés támogatása
                              -------------------
        begin                : 2023-10-19
        github               : https://github.com/pzsolt/ReszletKereso3
        copyright            : (C) 2023 by Ipoly Erdő Zrt.
        email                : pzs.vac@gmail.com
 ***************************************************************************/
"""
import os.path
from qgis.core import QgsProject
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from .reszletKereso_dockwidget import reszletKeresoDockWidget
from .pypref import readPref
from .reszletPref import PrefWidget
from . import PLUGIN_DIR

class reszletKereso:

    def __init__(self, iface):

        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # Declare instance attributes
        self.actions = []
        self.menu = u'&Erdőrészlet Kereső'
        self.toolbar = self.iface.addToolBar(u'reszletKereso')
        self.toolbar.setObjectName(u'reszletKereso')

        self.dockwidget = False
        self.pref = PrefWidget()

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None
        self.pluginIsActive = False

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        # icon_path = ':/plugins/ErdoreszletKereso3/reszletmutato.png'
        # QIcon('{}/images/batch.png'.format(PLUGIN_DIR))
        # os.path.join(os.path.dirname(__file__), './resources/reszletmutato.png')
        self.add_action(
            QIcon('{}/reszletmutato.png'.format(PLUGIN_DIR)),
            text=u'Erdőrészlet Kereső',
            callback=self.run,
            parent=self.iface.mainWindow())

        # Preferences - A plugin felhasználói beállításai
        # iconpref_path = ':/plugins/ErdoreszletKereso3/reszletmutato.png'
        self.preferencesAction = self.add_action(
            QIcon('{}/reszletmutato.png'.format(PLUGIN_DIR)),
            text=u'Erdőrészlet Kereső beállítások',
            callback=self.preferences,
            add_to_toolbar=False,
            parent=self.iface.mainWindow())
        self.iface.mapCanvas().layersChanged.connect(self.reszletLayers)

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(u'&ErdőreszletKereso3', action)
            self.iface.removeToolBarIcon(action)


    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dockwidget = reszletKeresoDockWidget()
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            # show the dialog
            self.dockwidget.show()
            self.dockwidget.reszletLayers()

    def reszletLayers(self):
        # az Erdőrészlet Rétegek combo feltöltése az 'azok' kódot tartalmazó poligon rétegekkel
        if self.first_start is False and self.dockwidget != None:
            layers = [layer for layer in QgsProject.instance().mapLayers().values()]
            self.dockwidget.reszletLayers(layers)

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""
        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)
        self.pluginIsActive = False
        self.first_start = True

    def preferences(self):
        outlinePref = readPref('Outline', self.plugin_dir + '\pref.txt')
        if outlinePref == 'True':
            self.pref.outlineCheck.setChecked(True)
        else:
            self.pref.outlineCheck.setChecked(False)
        self.pref.show()




