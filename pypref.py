#!/usr/bin/env python
# -*- coding: utf8 -*-

import os
from qgis.core import QgsProject


def readPref(txt0, arg0='pref.txt'):
    """Visszaad egy megadott parméterhez tartozó értéket
       az arg0-ként megadott paraméter fájlból"""
    #print(txt0, arg0)
    if os.path.exists(arg0):
        with open(arg0) as f:
            for line in f:
                linevals = line.split("=")
                if linevals[0] == txt0:
                    #print("%s= %s" % (linevals[0], linevals[1].rstrip('\r\n')))
                    return linevals[1].rstrip('\r\n')
            return 'None1'

    else:
        return 'None2'


def readAll(arg0='pref.txt'):
    """Visszaadja az arg0 paraméter fájl teljes tartalmát"""

    if os.path.exists(arg0):
        lines = ''
        with open(arg0) as f:
            for line in f:
                lines += line
            return lines
    else:
        return None


def writePref(txt0, txt1, arg0='pref.txt'):
    """egy megadott paraméterhez tartozó új értéket ad az arg0 paraméter fájlban"""
    if os.path.exists(arg0):
        with open(arg0) as f:
            lines = [x for x in f.readlines() if x != "\r\n"]

        fw = open(arg0, 'w')
        for line in lines:
            linevals = line.split("=")
            if txt0 == linevals[0]:
                fw.write(txt0 + '=' + txt1 + "\n")
                print("%s= %s" % (txt0, linevals[1]))
            elif line != "\r\n":
                fw.write(line)
        fw.close()
        return None

    else:
        print('path error')
        return None


def newParam(txt0, txt1, arg0='pref.txt'):
    """Új paraméter és a hozzá tartozó érték hozzáadása az arg0 paraméter fájlhoz"""

    if os.path.exists(arg0):
        with open(arg0) as f:
            for x in f.readlines():
                if x != "\r\n":
                    if txt0 == x.split("=")[0]:
                        return False

        fw = open(arg0, 'a')
        fw.write('\r\n' + txt0 + '=' + txt1)
        fw.close()
        return True

    else:
        print('path error')
        return None


def delParam(txt0, arg0='pref.txt'):
    """egy megadott paramétert és a hozzá tartozó értéket törli az arg0 paraméter fájlból"""

    if os.path.exists(arg0):
        with open(arg0) as f:
            lines = [x for x in f.readlines() if x != "\r\n"]

        fw = open(arg0, 'w')
        for line in lines:
            linevals = line.split("=")
            if txt0 != linevals[0]:
                fw.write(line)
        fw.close()
        return None

    else:
        return None


if __name__ == '__main__':
    pass
    print(readPref('img'))
    print(writePref('pkw', 'posz'))
    print(newParam('pkw', 'posz'))
    print(readAll())
