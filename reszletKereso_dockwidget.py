# -*- coding: utf-8 -*-
"""
/***************************************************************************
 reszletKeresoDockWidget
                                 A QGIS plugin
 Kiválasztott erdőrészlet réteg elemei közötti keresés támogatása
                             -------------------
        begin                : 2017-02-16
        git sha              : $Format:%H$
        copyright            : (C) 2017 by IpolyErdoZrt
        email                : pzs.vac@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os, sys
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot, Qt, QTimer
from qgis.PyQt.QtGui import QIcon, QGuiApplication, QColor, QTextCursor
from qgis._gui import QgsRubberBand
from qgis._core import QgsExpression, QgsFeatureRequest, QgsGeometry
from qgis.core import QgsProject, QgsMapLayer, QgsVectorLayer
import qgis.utils
from .pypref import *
from .reszletPref import PrefWidget


FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'reszletKereso_dockwidget_base.ui'))


class reszletKeresoDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()
    valueChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super(reszletKeresoDockWidget, self).__init__(parent)

        self.setupUi(self)
        if os.name in ('posix','os2'):
            self.azoks.setMinimumWidth(120)
        else:
            self.azoks.setMinimumWidth(100)

        self.lyrCount = 0
        self.activeLayer = None
        self.activeLayerObj = None
        self.activeLayerCount = None
        self._activeAzok = None
        self.activeGeom = None
        self.activeHelyseg = None
        self.activeHelysegKod = None
        self.activeTag = None
        self.activeTagKod = None
        self.activeReszlet = None
        self.activeReszletKod = None
        self.activeFilter = False

        self.azokList = []
        self.helysegek = []
        self.helysegkodok = []
        self.tagok = []
        self.tagkodok = []
        self.reszletek = []
        self.reszletkodok = []

        self.timer = QTimer()

        # érdemes-e dictionary-t csinálni a kód-érték párokra építve?

        self.plugin_dir = os.path.dirname(__file__)

        self.azoks.setEnabled(False)
        self.comboHelyseg.setEnabled(False)
        self.comboTag.setEnabled(False)
        self.comboReszlet.setEnabled(False)
        self.checkHelyseg.setChecked(False)
        self.checkTag.setChecked(False)
        self.checkReszlet.setChecked(False)
        self.deletefilterB.setEnabled(False)
        self.copyB.setEnabled(False)
        self.copyN.setEnabled(False)
        self.flashB.setEnabled(False)
        self.deleteborderB.setEnabled(False)

        # Szűrőlista Tab elrejtése és a Névjegy feltöltése
        self.tabSzures.setTabVisible(1, False)
        self.nevjegyTartalom()
        self.tabSzures.setCurrentIndex(0)

        self.canvas = qgis.utils.iface.mapCanvas()
        self.rubber = QgsRubberBand(self.canvas)

        self.azoks.currentIndexChanged.connect(self.onAzoksChanged)
        self.next.clicked.connect(self.onNext)
        self.back.clicked.connect(self.onPrev)
        self.copyB.clicked.connect(self.onCopyB)
        self.copyN.clicked.connect(self.onCopyN)
        self.deletefilterB.clicked.connect(self.onDeletefilterB)
        self.preferencesB.clicked.connect(self.onPreferencesB)
        self.deleteborderB.clicked.connect(self.onDeleteborderB)
        self.flashB.clicked.connect(self.onFlashB)
        self.valueChanged.connect(self.on_valueChanged)

        self.pref = PrefWidget()
        self.h_color = QColor()

        self._clipboard = QGuiApplication.clipboard()

    def nevjegyTartalom(self):
        self.textNevjegy.append('''<h2>Erdőr&eacute;szlet Kereső plugin</h2> <p>A plugin c&eacute;lja az 
        erdőr&eacute;szletek valamely szempontok szerint előzetesen l&eacute;trehozott (szűrt, 
        &ouml;ssze&aacute;ll&iacute;tott, elmentett stb.) elemlist&aacute;in t&ouml;rt&eacute;nő m&oacute;dszeres 
        v&eacute;gigl&eacute;pked&eacute;s. Esetleg egy szempont szerint szűrni azt ami az adott r&eacute;tegben van, 
        illetve a n&eacute;ha t&ouml;bbezres elemlist&aacute;ban gyorsan megtal&aacute;lni azt az egyet, 
        amire &eacute;pp sz&uuml;ks&eacute;g van. A szűr&eacute;s &eacute;s keres&eacute;s kulcsa az AZOK k&oacute;d, 
        ami Magyarorsz&aacute;gon az erdőr&eacute;szlet azonos&iacute;t&aacute;s alap hivatkoz&aacute;sa.</p> 
        <p><strong><em>V&aacute;laszt&oacute;mezők:</em></strong></p> <p>A <span style="color: 
        #800080;"><em>"V&aacute;laszthat&oacute; r&eacute;tegek</em></span> lista az erd&eacute;szeti 
        azonos&iacute;t&oacute;val (AZOK) rendelkező r&eacute;tegeket k&iacute;n&aacute;lja fel.<br 
        />V&aacute;lasszon <span style="color: #800080;"><em>"Akt&iacute;v r&eacute;teg"</em></span>-et a lista 
        elemei k&ouml;z&uuml;l.<br />Az <em><span style="color: #800080;">"Akt&iacute;v r&eacute;teg"</span></em> 
        AZOK szerint sorbarendezett alakzatain l&eacute;ptethet oda-vissza.<br />Az elemek (erdőr&eacute;szletek) 
        szűrhetők hierarchikusan: telep&uuml;l&eacute;s, majd erdőtag, &eacute;s erdőr&eacute;szlet k&oacute;d 
        szerint.<br />A be&aacute;ll&iacute;tott szűr&eacute;si szintet v&ouml;r&ouml;s n&eacute;gysz&ouml;gek 
        jelzik.</p> <p><strong><em>Gombok:</em></strong><br /><span style="text-decoration: underline;">Szűr&eacute;s 
        felold&aacute;s:</span> a szűr&eacute;si felt&eacute;tel elt&aacute;vol&iacute;t&aacute;sa.<br /><span 
        style="text-decoration: underline;">AZOK m&aacute;sol&aacute;s:</span> az <em><span style="color: 
        #800080;">"Aktu&aacute;lis r&eacute;szlet"</span></em> AZOK k&oacute;dj&aacute;nak v&aacute;g&oacute;lapra 
        m&aacute;sol&aacute;sa.<br /><span style="text-decoration: underline;">N&Eacute;V 
        m&aacute;sol&aacute;s:</span> az <span style="color: #800080;"><em>"Aktu&aacute;lis 
        r&eacute;szlet"</em></span> nev&eacute;nek v&aacute;g&oacute;lapra m&aacute;sol&aacute;sa.<br /><span 
        style="text-decoration: underline;">Alak kiemel&eacute;s:</span> az <em><span style="color: 
        #800080;">"Aktu&aacute;lis r&eacute;szlet"</span></em> k&ouml;rvonal&aacute;nak kiemel&eacute;se, 
        r&aacute;nagy&iacute;t&aacute;s.<br /><span style="text-decoration: underline;">Kiemel&eacute;s 
        t&ouml;rl&eacute;s:</span> a kiemelt k&ouml;rvonal t&ouml;rl&eacute;se.<br /><span style="text-decoration: 
        underline;">Be&aacute;ll&iacute;t&aacute;s:</span> az alakzat kiemel&eacute;se, annak sz&iacute;ne, 
        kit&ouml;lt&eacute;s&eacute;nek &aacute;tl&aacute;tszatlans&aacute;ga &eacute;s vonalvastags&aacute;ga 
        adhat&oacute; meg.</p> <p><br />Az alakzatok kiemel&eacute;se a l&eacute;ptet&eacute;s sor&aacute;n mindig az 
        aktu&aacute;lis r&eacute;szlet k&ouml;rvonal kiemel&eacute;s&eacute;t, illetve az "Alak kiemel&eacute;se" 
        gombbal l&eacute;trehozott egyedi kiemel&eacute;st jelenti. Az egyedi kiemel&eacute;snek 
        be&aacute;ll&iacute;that&oacute; 0-100% k&ouml;z&ouml;tti &eacute;rt&eacute;kű 
        &aacute;tl&aacute;tszatlans&aacute;ga (opacit&aacute;sa) is.</p> <p>K&eacute;sz&iacute;tette: <a 
        href="mailto:pzs.vac@gmail.com?subject=Erd%C5%91r%C3%A9szlet%20Keres%C5%91 ">Pataki Zsolt</a>, 
        <a href="http://ipolyerdo.hu">Ipoly Erdő Zrt.</a> 2023.</p> <p>Verzi&oacute;: 0.3</p>''')
        self.textNevjegy.moveCursor(QTextCursor.Start)

    @property
    def activeAzok(self):
        return self._activeAzok

    #@ activeAzok.setter
    def setActiveAzok(self,text):
        self._activeAzok = text
        self._clipboard.setText(text)
        self.copyB.setEnabled(True)
        self.copyN.setEnabled(True)
        self.valueChanged.emit(text)

    @pyqtSlot(str)
    def on_valueChanged(self,text):
        if not text is None:
            pass
            ##if self.hasznalatB.isEnabled() == False:
                ##self.hasznalatB.setEnabled(True)

    def clearLayerList(self):
        self.comboLayers.clear()

    def clearHelysegek(self):
        self.activeHelyseg = None
        self.activeHelysegKod = None
        self.helysegek = []
        self.helysegkodok = []
        self.comboHelyseg.clear()
        self.comboHelyseg.setEnabled(False)
        self.checkHelyseg.setChecked(False)

    def clearTagok(self):
        self.activeTag = None
        self.activeTagKod = None
        self.tagok = []
        self.tagkodok = []
        self.comboTag.clear()
        self.comboTag.setEnabled(False)
        self.checkTag.setChecked(False)

    def clearReszlet(self):
        self.activeReszlet = None
        self.activeReszletKod = None
        self.reszletek = []
        self.reszletkodok = []
        self.comboReszlet.clear()
        self.comboReszlet.setEnabled(False)
        self.checkReszlet.setChecked(False)

    def reszletLayers(self, lrs = None):
        # az Erdőrészlet Rétegek combo feltöltése az 'azok' kódot tartalmazó poligon rétegekkel
        # első betöltéskor és réteglista változásakor fut
        # if self.activeAzok is None:
        self.clearLayerList()
        reszletLayers = []
        if lrs is None:
            layers = QgsProject.instance().mapLayers().values()
        else:
            layers = lrs

        if self.lyrCount != len(layers):
            for layer in layers:
                layerType = layer.type()
                # print(layer.name(), layerType)
                if layerType == QgsMapLayer.VectorLayer:
                    print(layerType, layer.geometryType(), layer.name())
                    if layer.geometryType() == 2:
                        print(layer.name())
                        fields = layer.fields()
                        for field in fields:
                            if field.name() in ['azok','AZOK','Azok']:
                                print(field.name(), field.typeName())
                                if field.typeName() == 'String' or field.typeName() == 'TEXT' or field.typeName() == 'varchar':
                                    reszletLayers.append(layer.name())
            reszletLayers.sort()
            for r in reszletLayers:
                self.changeLayerList(r, True)
            self.checkActiveLayer()

    def changeLayerList(self, layername, todo):
        # a teendő, ha True akkor hozzáadás, ha False akkor elvétel
        if self.comboLayers.findText(layername) == -1:
            if todo:
                self.comboLayers.addItem(layername)
        else:
            if not todo:
                self.comboLayers.removeItem(self.comboLayers.findText(layername))

    def checkActiveLayer(self):
        # első betöltéskor és réteglista változásakor fut
        if not self.activeLayer is None:
            if self.comboLayers.findText(self.activeLayer) == -1:
                #layerIndex = self.comboLayers.findText(self.activeLayer)
                #self.comboLayers.setCurrentIndex(layerIndex)
                self.clearHelysegek()
                self.clearTagok()
                self.clearReszlet()
                self.azoks.clear()
                self.activeLayerLine.clear()
                self.activeLayerLine.setStyleSheet("QLineEdit { background-color : rgb(180, 220, 80); color : black; }")
                self.activeLayer = None
                self.activeLayerObj = None
                self.reszletFelirat.setText('- - -')

    def getActiveLayer(self):
        return self.activeLayer

    @pyqtSlot(str)
    def on_activeLayerLine_textChanged(self, text):
        self.activeLayer = text
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if layer.name() == self.activeLayer:
                self.activeLayerObj = layer
        self.helysegLista()

    @pyqtSlot(str)
    def on_comboLayers_activated(self, text):
        self.clearHelysegek()
        self.clearTagok()
        self.clearReszlet()
        self.azoks.clear()
        self.activeLayerLine.setText(text)
        self.activeLayerLine.setStyleSheet("QLineEdit { background-color : black; color : yellow; }")
        self.flashB.setEnabled(True)

    def helysegLista(self):
        #törlések a szűrés feloldás esetében szükségesek
        self.clearHelysegek()
        self.clearTagok()
        self.clearReszlet()
        self.checkHelyseg.setStyleSheet("QCheckBox::indicator { background-color : white }")
        self.checkTag.setStyleSheet("QCheckBox::indicator { background-color : white }")
        self.checkReszlet.setStyleSheet("QCheckBox::indicator { background-color : white }")
        self.azoks.clear()
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if layer.name() == self.activeLayer:
                reszletLayer = layer
                self.azokList = []
                self.helysegkodok = []
                self.helysegek=[]
                # AZOK és helységkódok kigyűjtése
                reszletFeatures = reszletLayer.getFeatures()
                for rf in reszletFeatures:
                    rfAzok = rf['azok']
                    if isinstance(rfAzok,unicode):
                        if len(rfAzok)==10:
                            if not rfAzok in self.azokList:
                                self.azokList.append(rfAzok)
                            hkod = rfAzok[:4]
                            if not hkod in self.helysegkodok:
                                self.helysegkodok.append(hkod)
                self.helysegkodok.sort()
                # helységnevek kiolvasása
                for h in self.helysegkodok:
                    hnev = readPref(str(h), os.path.join(self.plugin_dir, 'kod_helynev.csv'))
                    self.helysegek.append(hnev)
                self.helysegek.sort()
                for hnev in self.helysegek:
                    if self.comboHelyseg.findText(hnev) == -1:
                        self.comboHelyseg.addItem(hnev)
                self.comboHelyseg.setEnabled(True)
                self.comboHelyseg.setCurrentIndex(0)
                # azok combo feltöltése és az aktív réteg hosszának meghatározása
                self.azokList.sort()
                self.azoks.addItems(self.azokList)
                self.azoks.setEnabled(True)
                self.indexL.setText(str(1) + "/" + str(len(self.azokList)))
                self.azoks.setCurrentIndex(0)
                self.activeLayerCount = len(self.azokList)
                self.deletefilterB.setEnabled(False)

    @pyqtSlot(str)
    def on_comboHelyseg_activated(self, text):
        self.clearTagok()
        self.clearReszlet()
        self.activeHelyseg = text
        self.activeHelysegKod = readPref(text, os.path.join(self.plugin_dir, 'helynev_kod.csv'))
        self.helysegTagok()
        self.checkHelyseg.setChecked(True)
        self.checkHelyseg.setStyleSheet("QCheckBox::indicator { background-color : red }")
        self.checkTag.setStyleSheet("QCheckBox::indicator { background-color : white }")
        self.checkReszlet.setStyleSheet("QCheckBox::indicator { background-color : white }")

    def helysegTagok(self):
        """A kiválasztott helységben található erdőtagok listájának előállítása"""
        self.azoks.clear()
        helyazoks = []
        for a in self.azokList:
            if a[:4] == self.activeHelysegKod:
                self.tagkodok.append(a[4:7])
                self.tagok.append(int(a[4:7])) # integereket teszek listába a logikus sorbarendezés érdekében
                helyazoks.append(a)
        self.azoks.addItems(helyazoks)
        self.tagok.sort()
        self.tagkodok.sort()
        for t in self.tagok:
            if self.comboTag.findText(str(t)) == -1: # a listából az integer jön, amit át kell alakítani
                self.comboTag.addItem(str(t))
        self.comboTag.setEnabled(True)
        self.indexL.setText(str(1) + "/" + str(self.azoks.count()))
        self.azoks.setCurrentIndex(0)
        if self.activeLayerCount > self.azoks.count():
            self.deletefilterB.setEnabled(True)

    @pyqtSlot(str)
    def on_comboTag_activated(self, text):
        self.clearReszlet()
        self.activeTag = text
        OOOtext = '000' + text
        self.activeTagKod = OOOtext[-3:]
        self.tagReszletek()
        self.checkTag.setChecked(True)
        self.checkTag.setStyleSheet("QCheckBox::indicator { background-color : red }")
        self.checkReszlet.setStyleSheet("QCheckBox::indicator { background-color : white }")

    def tagReszletek(self):
        self.azoks.clear()
        tagazoks = []
        for a in self.azokList:
            if a[:4] == self.activeHelysegKod:
                if a[4:7] == self.activeTagKod:
                    reszletjel = readPref(a[7:9], os.path.join(self.plugin_dir, 'kod_reszletjel.csv'))
                    if a[9] == '0':
                        self.reszletek.append(reszletjel)
                    else:
                        self.reszletek.append(reszletjel + '-' + a[9])
                    self.reszletkodok.append(a[7:])
                    tagazoks.append(a)
        self.azoks.addItems(tagazoks)
        self.reszletek.sort()
        self.reszletkodok.sort()
        for r in self.reszletek:
            if self.comboReszlet.findText(r) == -1:
                self.comboReszlet.addItem(r)
        self.comboReszlet.setEnabled(True)
        self.indexL.setText(str(1) + "/" + str(self.azoks.count()))
        self.azoks.setCurrentIndex(0)

    @pyqtSlot(str)
    def on_comboReszlet_activated(self, text):
        self.activeReszlet = text
        ridx = self.comboReszlet.findText(text)
        self.activeReszletKod = self.reszletkodok[ridx]
        self.setActiveAzok(self.activeHelysegKod + self.activeTagKod + self.activeReszletKod)
        #self.comboReszlet.setStyleSheet("QComboBox::text { background-color : rgb(180, 220, 80); color : black; }")
        self.checkReszlet.setChecked(True)
        self.checkReszlet.setStyleSheet("QCheckBox::indicator { background-color : red }")
        self.azoks.clear()
        self.azoks.addItem(self.activeAzok)
        self.indexL.setText(str(1) + "/" + str(self.azoks.count()))
        self.azoks.setCurrentIndex(0)

    def onAzoksChanged(self, index):
        #a rekordszámláló léptetése
        self.indexL.setText(str(index+1) + "/" + str(self.azoks.count()))

        if not index is None and index != -1:

            # részlet felirat összeállítás
            hnev = readPref(self.azoks.itemText(index)[:4], os.path.join(self.plugin_dir, 'kod_helynev.csv'))
            tag = str(int(self.azoks.itemText(index)[4:7]))
            reszletjel = readPref(self.azoks.itemText(index)[7:9], os.path.join(self.plugin_dir, 'kod_reszletjel.csv'))
            if self.azoks.itemText(index)[9] == '0':
                reszlet = reszletjel
            else:
                reszlet = reszletjel + '/' + self.azoks.itemText(index)[9]
            self.reszletFelirat.setText(hnev + ' ' + tag + reszlet)

            #léptetőgombok elérhetőségének szabályozása
            i = index
            imax = self.azoks.count()-1
            if imax == 0:
                self.back.setEnabled(False)
                self.next.setEnabled(False)
            else:
                if i == 0:
                    self.back.setEnabled(False)
                    self.next.setEnabled(True)
                elif i == imax:
                    self.back.setEnabled(True)
                    self.next.setEnabled(False)
                else:
                    self.back.setEnabled(True)
                    self.next.setEnabled(True)

            #a megjelenítendő erdőrészletre nagyítás, kiemelés
            if not self.azoks.itemText(index) is None:
                layers = QgsProject.instance().mapLayers().values()
                for layer in layers:
                    if layer.name() == self.activeLayer:
                        expr = QgsExpression("\"azok\"="+ self.azoks.itemText(index))
                        fs = layer.getFeatures(QgsFeatureRequest(expr))
                        ff = list(fs)[0]

                        if ff != None:
                            outline = readPref('Outline', self.plugin_dir + '\pref.txt')
                            if outline == 'True':
                                # jelolo elhelyezése
                                self.rubber.reset()
                                width = int(readPref('Outwidth', self.plugin_dir + '\pref.txt'))
                                prefcolor = readPref('Outcolor', self.plugin_dir + '\pref.txt')
                                fillcolor = QColor("transparent")
                                outcolor = QColor()
                                outcolor.setNamedColor(prefcolor)
                                self.rubber.setStrokeColor(outcolor)
                                self.rubber.setFillColor(fillcolor)
                                self.rubber.setWidth(width)
                                self.rubber.setToGeometry(ff.geometry(), layer)
                                self.deleteborderB.setEnabled(True)
                            else:
                                self.deleteborderB.setEnabled(False)

                            self.canvas.setExtent(ff.geometry().boundingBox().buffered(ff.geometry().boundingBox().height()/5))
                            self.canvas.refresh()

                            self.activeGeom = ff.geometry().asWkt()
                            print('dock: ', self.activeGeom)
                            print(QgsGeometry.fromWkt(self.activeGeom).area())

                        else:
                            print('A keresett részlet nincs a rétegben!', self.azoks.itemText(index))
                            self.activeGeom = None
                            return
            self.setActiveAzok(self.azoks.itemText(index))

    def onNext(self):
        self.azoks.setCurrentIndex(self.azoks.currentIndex() + 1)

    def onPrev(self):
        self.azoks.setCurrentIndex(self.azoks.currentIndex() - 1)

    def onPreferencesB(self):
        self.onDeleteborderB()
        self.pref.show()
        # kiemelés mindig beállítása
        outlinePref = readPref('Outline', self.plugin_dir + '\pref.txt')
        if outlinePref == 'True':
            self.pref.outlineCheck.setChecked(True)
        else:
            self.pref.outlineCheck.setChecked(False)
        # átlátszatlanság
        opacityPref = float(readPref('Opacity', self.plugin_dir + '\pref.txt'))
        self.pref.opacityLCD.display(opacityPref)
        self.pref.opacitySlider.setValue(opacityPref)
        # szín
        outColorPref = readPref('Outcolor', self.plugin_dir + '\pref.txt')
        self.h_color.setNamedColor(outColorPref)
        if self.h_color.isValid():
            print(outColorPref, 'érvényes szín')
        else:
            print(outColorPref,'nem érvényes szín')
        self.pref.szinvalasztoB.setColor(self.h_color)
        # vonalvastagság
        outWidthPref = int(readPref('Outwidth', self.plugin_dir + '\pref.txt'))
        self.pref.widthBox.setValue(outWidthPref)
        self.pref.widthLine.setLineWidth(outWidthPref)

    def onDeletefilterB(self):
            self.on_activeLayerLine_textChanged(self.activeLayer)

    def onDeleteborderB(self):
        self.deleteborderB.setEnabled(False)
        self.rubber.reset()
        self.canvas.refresh()

    def onFlashB(self):
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            if layer.name() == self.activeLayer:
                expr = QgsExpression("\"azok\"=" + self.activeAzok)
                fs = layer.getFeatures(QgsFeatureRequest(expr))
                ff = list(fs)[0]

                if ff != None:
                    # jelolo elhelyezése
                    self.rubber.reset()
                    width = int(readPref('Outwidth', self.plugin_dir + '\pref.txt'))
                    prefcolor = readPref('Outcolor', self.plugin_dir + '\pref.txt')
                    opacityPref = float(readPref('Opacity', self.plugin_dir + '\pref.txt'))
                    opacityValue = int(round(opacityPref * 2.55))
                    fillcolor = QColor()
                    fillcolor.setNamedColor(prefcolor)
                    fillcolor.setAlpha(opacityValue)
                    outcolor = QColor()
                    outcolor.setNamedColor(prefcolor)
                    # (181, 22, 45, 255)  # vörös, utolsó érték az áttetszőség, 0 = átlátszó
                    self.rubber.setStrokeColor(outcolor)
                    self.rubber.setFillColor(fillcolor)
                    self.rubber.setWidth(width)
                    self.rubber.setToGeometry(ff.geometry(), layer)

                    self.canvas.setExtent(
                        ff.geometry().boundingBox().buffered(ff.geometry().boundingBox().height() / 5))
                    self.canvas.refresh()
                    self.activeGeom = ff.geometry().asWkt()
                    self.deleteborderB.setEnabled(True)
                else:
                    print('A keresett részlet nincs a rétegben!', self.azoks.itemText(index))
                    self.activeGeom = None
                    return

    def onCopyB(self):
        if not self._activeAzok is None:
            self._clipboard.setText(self._activeAzok)

    def onCopyN(self):
        self._clipboard.setText(self.reszletFelirat.text())

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()