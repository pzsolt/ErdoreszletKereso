# -*- coding: utf-8 -*-

import os
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtGui import QColor
from .pypref import writePref, readPref

FROM_PREF, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'preferences.ui'))

# betolti es elemzi (parse) a QtDesigner 'ui' fajlt, majd osztályt hoz létre, ami tobbszor is peldanyosithato ujboli xml feldolgozas nelkul

class PrefWidget(QtWidgets.QDialog, FROM_PREF):
    def __init__(self, parent=None):
        super(PrefWidget, self).__init__(parent)
        self.setupUi(self)
        self.h_color = QColor()

        self.outlineCheck.clicked.connect(self.onOutline)
        self.savePref.clicked.connect(self.onSavePref)
        self.cancelPref.clicked.connect(self.onCancelPref)
        self.widthBox.valueChanged.connect(self.onWidthChanged)
        self.opacitySlider.valueChanged.connect(self.onOpacityChange)

    def onOutline(self):
        pass

    def onWidthChanged(self):
        self.widthLine.setLineWidth(self.widthBox.value())

    def onOpacityChange(self):
        self.opacityLCD.display(self.opacitySlider.value())

    def onSavePref(self):
        writePref('Outcolor', self.szinvalasztoB.color().name(), os.path.join(os.path.dirname(__file__), 'pref.txt'))
        writePref('Outwidth', str(self.widthBox.value()), os.path.join(os.path.dirname(__file__), 'pref.txt'))
        writePref('Opacity', str(self.opacitySlider.value()), os.path.join(os.path.dirname(__file__), 'pref.txt'))
        if self.outlineCheck.isChecked():
            writePref('Outline', 'True', os.path.join(os.path.dirname(__file__), 'pref.txt'))
        else:
            writePref('Outline', 'False', os.path.join(os.path.dirname(__file__), 'pref.txt'))
            self.rubber.reset()
            self.canvas.refresh()
        self.close()

    def onCancelPref(self):
        self.close()

