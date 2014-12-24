# -*- coding: utf-8 -*-

### Copyright (C) 2008-2014 Antonio Valentino <antonio.valentino@tiscali.it>

### This file is part of GSDView.

### GSDView is free software; you can redistribute it and/or modify
### it under the terms of the GNU General Public License as published by
### the Free Software Foundation; either version 2 of the License, or
### (at your option) any later version.

### GSDView is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.

### You should have received a copy of the GNU General Public License
### along with GSDView; if not, write to the Free Software
### Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA.


'''Zoom tool.'''


import logging

from qt import QtCore, QtWidgets, QtGui

from gsdview import qt4support


class ZoomTool(QtCore.QObject):
    DEFAULT_FACTOR = 1.2

    def __init__(self, view=None, parent=None, **kwargs):
        super(ZoomTool, self).__init__(parent, **kwargs)
        self.factor = self.DEFAULT_FACTOR

        self._view = view

        self.actions = self._setupActions()

    def _setupActions(self):
        actions = QtWidgets.QActionGroup(self)

        # Zoom in
        icon = qt4support.geticon('zoom-in.svg', 'gsdview')
        QtWidgets.QAction(
            icon, self.tr('Zoom In'), actions,
            objectName='zoomInAction',
            statusTip=self.tr('Zoom In'),
            shortcut=QtGui.QKeySequence(self.tr('Ctrl++')),
            triggered=self.zoomIn)

        # Zoom out
        icon = qt4support.geticon('zoom-out.svg', 'gsdview')
        QtWidgets.QAction(
            icon, self.tr('Zoom Out'), actions,
            objectName='zoomOutAction',
            statusTip=self.tr('Zoom Out'),
            shortcut=QtGui.QKeySequence(self.tr('Ctrl+-')),
            triggered=self.zoomOut)

        # Zoom fit
        icon = qt4support.geticon('zoom-fit.svg', 'gsdview')
        QtWidgets.QAction(
            icon, self.tr('Zoom Fit'), actions,
            objectName='zoomFitAction',
            statusTip=self.tr('Zoom to fit the window size'),
            triggered=self.zoomFit)

        # Zoom 100
        icon = qt4support.geticon('zoom-100.svg', 'gsdview')
        QtWidgets.QAction(
            icon, self.tr('Zoom 100%'), actions,
            objectName='zoom100Action',
            statusTip=self.tr('Original size'),
            triggered=self.zoom100)

        # Manual Zoom
        #icon = QtGui.QIcon() #qt4support.geticon('zoom-100.svg', 'gsdview')
        #QtWidgets.QWidgetAction(
        #    icon, self.tr('Zoom 100%'), actions,
        #    statusTip=self.tr('Original size'),
        #    triggered=self.zoom100)

        return actions

    def currentview(self):
        return self._view

    @QtCore.Slot()
    def zoomIn(self):
        view = self.currentview()
        if view:
            view.scale(self.factor, self.factor)

    @QtCore.Slot()
    def zoomOut(self):
        view = self.currentview()
        if view:
            factor = 1. / self.factor
            view.scale(factor, factor)

    @QtCore.Slot()
    def zoomFit(self):
        view = self.currentview()
        if view:
            view.fitInView(view.sceneRect(), QtCore.Qt.KeepAspectRatio)

    @QtCore.Slot()
    def zoom100(self):
        view = self.currentview()
        if view:
            view.setMatrix(QtWidgets.QMatrix())


class AppZoomTool(ZoomTool):
    def __init__(self, app, **kwargs):
        super(AppZoomTool, self).__init__(None, app, **kwargs)
        self.app = app

    def currentview(self):
        subwin = self.app.mdiarea.currentSubWindow()
        try:
            view = subwin.widget()
        except AttributeError as e:
            logging.debug(str(e))
        else:
            if isinstance(view, QtWidgets.QGraphicsView):
                return view
            else:
                return None
