# -*- coding: utf-8 -*-

### Copyright (C) 2008-2010 Antonio Valentino <a_valentino@users.sf.net>

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


'''Core GDAL backend functions and classes.'''

__author__   = 'Antonio Valentino <a_valentino@users.sf.net>'
__date__     = '$Date$'
__revision__ = '$Revision$'

import os

from osgeo import gdal
from PyQt4 import QtCore, QtGui

from gsdview import qt4support

from gsdview.gdalbackend import widgets
from gsdview.gdalbackend import modelitems
from gsdview.gdalbackend import gdalsupport


class GDALBackend(QtCore.QObject):
    # @TODO:
    #
    # - fix selection mess
    #
    #   * trying to re-oped an already open file should select the
    #     corresponding dataset item (no active sub-window change is expected)
    #
    # - sub-windows title and window menu

    _use_exceptions = None

    # @TODO: fix names
    @staticmethod
    def UseExceptions():
        gdal.UseExceptions()
        gdal.SetConfigOption('PYHTON_USE_EXCEPTIONS', 'TRUE')

    @staticmethod
    def DontUseExceptions():
        gdal.DontUseExceptions()
        gdal.SetConfigOption('PYHTON_USE_EXCEPTIONS', 'FALSE')

    @staticmethod
    def getUseExceptions():
        return gdal.GetConfigOption('PYHTON_USE_EXCEPTIONS', 'FALSE') == 'TRUE'

    def __init__(self, mainwin, parent=None):
        if parent is None:
            parent = mainwin
        QtCore.QObject.__init__(self, parent)
        self._mainwin = mainwin
        self._actionsmap = {}
        self._setupActions()

        self.connect(self._mainwin.treeview,
                     QtCore.SIGNAL('activated(const QModelIndex&)'),
                     self.onItemActivated)

        # @TODO: improve ptocessing tools handling and remove this workaround
        self.connect(self._mainwin.controller, QtCore.SIGNAL('finished()'),
                     self._finalize)

    def findItemFromFilename(self, filename):
        '''Serch for and return the (dataset) item corresponding to filename.

        If no item is found retirn None.

        '''

        # @NOTE: linear complexity
        # @NOTE: only scan toplevel items
        # @TODO: use an internal regidtry (set or dict) in oder to perfotm
        #        O(1) search over all nesting levels

        filename = os.path.abspath(filename)
        filename = os.path.normpath(filename)
        root = self._mainwin.datamodel.invisibleRootItem()
        for index in range(root.rowCount()):
            try:
                item = root.child(index)
                if item.filename == filename:
                    return item
            except AttributeError:
                pass
        return None

    @qt4support.overrideCursor
    def openFile(self, filename):
        item = self.findItemFromFilename(filename)
        if item:
            self._mainwin.treeview.setCurrentIndex(item.index())

            # @TODO: remove selection code
            sm = self._mainwin.treeview.selectionModel()
            sm.select(item.index(), QtGui.QItemSelectionModel.Select)

            # @TODO: maybe it is better to use an exception here
            return None
        return modelitems.datasetitem(filename)

    def itemActions(self, item):
        try:
            method = getattr(self, '_get%sActions' % item.__class__.__name__)
        except AttributeError:
            actions = self._actionsmap.get(item.__class__.__name__)
        else:
            actions = method(item)
        return actions

    def itemContextMenu(self, item):
        actions = self.itemActions(item)
        if actions:
            return qt4support.actionGroupToMenu(actions,
                                                self.tr('Context menu'),
                                                self._mainwin.treeview)

    def onItemActivated(self, index):
        defaultActionsMap = {
            modelitems.BandItem: 'actionOpenImageView',
            modelitems.SubDatasetItem: 'actionOpenSubDatasetItem',
        }
        item = self._mainwin.datamodel.itemFromIndex(index)
        for itemtype in defaultActionsMap:
            if isinstance(item, itemtype):
                actions = self._actionsmap[type(item).__name__]
                action = actions.findChild(QtGui.QAction,
                                           defaultActionsMap[itemtype])
                if action:
                    action.trigger()
                    break

    ### Actions setup #########################################################
    def _setupMajorObjectItemActions(self, actionsgroup=None):
        if actionsgroup is None:
            actionsgroup = QtGui.QActionGroup(self)

        # open metadata view
        icon = qt4support.geticon('metadata.svg', __name__)
        action = QtGui.QAction(icon, self.tr('Open &Metadata View'),
                               actionsgroup)
        action.setObjectName('actionOpenItemMetadataView')
        action.setShortcut(self.tr('Ctrl+M'))
        action.setToolTip(self.tr('Show metadata in a new window'))
        action.setStatusTip(self.tr('Show metadata in a new window'))
        self.connect(action, QtCore.SIGNAL('triggered()'),
                     self.openItemMatadataView)
        action.setEnabled(False)    # @TODO: remove

        # show properties
        # @TODO: standard info icon from gdsview package
        icon = qt4support.geticon('info.svg', 'gsdview')
        action = QtGui.QAction(icon, self.tr('&Show Properties'), actionsgroup)
        action.setObjectName('actionShowItemProperties')
        action.setShortcut(self.tr('Ctrl+S'))
        action.setToolTip(self.tr('Show the property dialog for the cutent item'))
        action.setStatusTip(self.tr('Show the property dialog for the cutent '
                                    'item'))
        self.connect(action, QtCore.SIGNAL('triggered()'),
                     self.showItemProperties)

        return actionsgroup

    def _setupBandItemActions(self, actionsgroup=None):
        if actionsgroup is None:
            actionsgroup = QtGui.QActionGroup(self)

        # open image view
        icon = qt4support.geticon('open.svg', __name__)
        action = QtGui.QAction(icon, self.tr('&Open Image View'), actionsgroup)
        action.setObjectName('actionOpenImageView')
        action.setShortcut(self.tr('Ctrl+O'))
        action.setToolTip(self.tr('Open an image view'))
        action.setStatusTip(self.tr('Open a new image view'))
        self.connect(action, QtCore.SIGNAL('triggered()'), self.openImageView)

        # @TODO: add a new action for newImageView

        # @TODO: Masked bands, Compute statistics, Compute histogram
        # @TODO: dataset --> Build overviews

        # separator
        QtGui.QAction(actionsgroup).setSeparator(True)

        self._setupMajorObjectItemActions(actionsgroup)

        return actionsgroup

    def _setupOverviewItemActions(self, actionsgroup=None):
        # @TODO: remove open
        # @TODO: remove overviews build
        #~ actionsgroup = self._setupBandItemActions()
        #~ action = actionsgroup.findChild(QtGui.QAction, 'actionBuidOverviews')
        #~ actionsgroup.removeAction(action)
        #~ return actionsgroup
        return self._setupBandItemActions(actionsgroup)

    # @TODO
    #def _setupVirtualBandItemActions(self):
    #    pass

    def _setupDatasetItemActions(self, actionsgroup=None):
        if actionsgroup is None:
            actionsgroup = QtGui.QActionGroup(self)

        self._setupMajorObjectItemActions(actionsgroup)

        # separator
        QtGui.QAction(actionsgroup).setSeparator(True)

        # build overviews
        icon = qt4support.geticon('overview.svg', __name__)
        action = QtGui.QAction(icon,
                               self.tr('&Build overviews for all raster bands'),
                               actionsgroup)
        action.setObjectName('actionBuidOverviews')
        action.setShortcut(self.tr('Ctrl+B'))
        action.setToolTip(self.tr('Build overviews for all raster bands'))
        action.setStatusTip(self.tr('Build overviews for all raster bands'))
        self.connect(action, QtCore.SIGNAL('triggered()'), self.buildOverviews)
        action.setEnabled(False)    # @TODO: remove

        # open RGB
        # @TODO: find an icon for RGB
        icon = qt4support.geticon('rasterband.svg', __name__)
        action = QtGui.QAction(icon, self.tr('Open as RGB'), actionsgroup)
        action.setObjectName('actionOpenRGBImageView')
        #action.setShortcut(self.tr('Ctrl+B'))
        action.setToolTip(self.tr('Display the dataset as an RGB image'))
        action.setStatusTip(self.tr('Open as RGB'))
        self.connect(action, QtCore.SIGNAL('triggered()'), self.openRGBImageView)
        #action.setEnabled(False)    # @TODO: remove

        # @TODO: add band, add virtual band, open GCPs view

        # separator
        QtGui.QAction(actionsgroup).setSeparator(True)

        # close
        icon = qt4support.geticon('close.svg', 'gsdview')
        action = QtGui.QAction(icon, self.tr('Close'), actionsgroup)
        action.setObjectName('actionCloseItem') # @TODO: complete
        action.setShortcut(self.tr('Ctrl+W'))
        action.setToolTip(self.tr('Close the current item'))
        action.setStatusTip(self.tr('Close the current item'))
        self.connect(action, QtCore.SIGNAL('triggered()'), self.closeItem)

        return actionsgroup

    def _setupSubDatasetItemActions(self, actionsgroup=None):
        if actionsgroup is None:
            actionsgroup = QtGui.QActionGroup(self)

        # open
        icon = qt4support.geticon('open.svg', __name__)
        action = QtGui.QAction(icon, self.tr('Open Sub Dataset'), actionsgroup)
        action.setObjectName('actionOpenSubDatasetItem')
        action.setShortcut(self.tr('Ctrl+O'))
        action.setToolTip(self.tr('Open Sub Dataset'))
        action.setStatusTip(self.tr('Open Sub Dataset'))
        self.connect(action, QtCore.SIGNAL('triggered()'), self.openSubDataset)

        # separator
        QtGui.QAction(actionsgroup).setSeparator(True)

        self._setupDatasetItemActions(actionsgroup)

        return actionsgroup

    def _setupActions(self):
        self._actionsmap['MajorObjectItem'] = self._setupMajorObjectItemActions()
        self._actionsmap['BandItem'] = self._setupBandItemActions()
        self._actionsmap['OverviewItem'] = self._setupOverviewItemActions()
        #self._actionsmap['VirtualBandItem'] = self._setupVirtualBandItemActions()
        self._actionsmap['DatasetItem'] = self._setupDatasetItemActions()
        self._actionsmap['CachedDatasetItem'] = self._actionsmap['DatasetItem']
        self._actionsmap['SubDatasetItem'] = self._setupSubDatasetItemActions()

    ### Actions enabling ######################################################
    def _getDatasetItemActions(self, item=None):
        actionsgroup = self._actionsmap['DatasetItem']

        # RGB
        action = actionsgroup.findChild(QtGui.QAction, 'actionOpenRGBImageView')
        if gdalsupport.isRGB(item):
            action.setEnabled(True)
        else:
            action.setEnabled(False)

        return actionsgroup

    # @NOTE: this is needed for correct context menu setup
    # @TODO: maybe it is possible to find a better way to handle the problem
    _getCachedDatasetItemActions = _getDatasetItemActions

    def _getBandItemActions(self, item=None):
        actionsgroup = self._actionsmap['BandItem']

        openaction = actionsgroup.findChild(QtGui.QAction, 'actionOpenImageView')
        openaction.setEnabled(True)

        if item is not None:
            assert isinstance(item, modelitems.BandItem)
            if gdal.DataTypeIsComplex(item.DataType):
                openaction.setEnabled(False)
            else:
                # @TODO: remove this to allow multiple views on the same item
                for subwin in self._mainwin.mdiarea.subWindowList():
                    if subwin.item == item:
                        openaction.setEnabled(False)
                        break

        return actionsgroup

    def _getSubDatasetItemActions(self, item=None):
        actionsgroup = self._actionsmap['SubDatasetItem']

        openaction = actionsgroup.findChild(QtGui.QAction,
                                            'actionOpenSubDatasetItem')
        openaction.setEnabled(True)

        propertyaction = actionsgroup.findChild(QtGui.QAction,
                                                'actionShowItemProperties')
        propertyaction.setEnabled(True)

        closeaction = actionsgroup.findChild(QtGui.QAction, 'actionCloseItem')
        closeaction.setEnabled(True)

        if item is not None:
            assert isinstance(item, modelitems.SubDatasetItem)
            if item.isopen():
                openaction.setEnabled(False)
            else:
                closeaction.setEnabled(False)
                propertyaction.setEnabled(False)

        return actionsgroup

    ### Major object ##########################################################
    def openItemMatadataView(self):
        # @TODO: implementation
        self._mainwin.logger.info('method not yet implemented')

    def showItemProperties(self):
        item = self._mainwin.currentItem()
        for itemtype in item.__class__.__mro__:
            name = itemtype.__name__
            assert name.endswith('Item')
            name = name[:-4] + 'InfoDialog'
            dialogclass = getattr(widgets, name, None)
            if dialogclass:
                dialog = dialogclass(item._obj) # @TODO: check
                dialog.exec_()
                break
        else:
            self._mainwin.logger.debug('unable to show info dialog for "%s" '
                                       'item class' % (item.__class__.__name__))

    ### Driver ################################################################
    ### Dataset ###############################################################
    def openRGBImageView(self, item=None):
        if item is None:
            item = self._mainwin.currentItem()
        assert isinstance(item, modelitems.DatasetItem)

        if not item.scene:
            title = self.tr('WARNING')
            msg = self.tr("This dataset can't be opened in RGB mode.")
            QtGui.QMessageBox.warning(self._mainwin, title, msg)
            return
        # only open a new view if there is no other on the item selected
        if len(item.scene.views()) == 0:
            self.newImageView(item)

    def buildOverviews(self):
        # @TODO: implementation
        self._mainwin.logger.info('method not yet implemented')

    # @TODO: add band, add virtual band, open GCPs view

    def closeItem(self):
        item = self._mainwin.currentItem()
        item.close()

    ### Sub-dataset ###########################################################
    def openSubDataset(self):
        item = self._mainwin.currentItem()
        assert isinstance(item, modelitems.SubDatasetItem)
        if item.isopen():
            return

        try:
            # Only works for CachedDatasetItems
            cachedir = os.path.dirname(item.parent().vrtfilename)
        except AttributeError:
            id_ = gdalsupport.uniqueDatasetID(item.parent())
            cachedir = os.path.join(modelitems.SubDatasetItem.CACHEDIR, id_)

        # sub-dataset index (starting from 1)
        index = item.row() - item.parent().RasterCount + 1
        cachedir = os.path.join(cachedir, 'subdataset%02d' % index)

        item.open(cachedir)

        for row in range(item.rowCount()):
            child = item.child(row)
            self._mainwin.treeview.expand(child.index())

    ### Raster Band ###########################################################
    @qt4support.overrideCursor
    def openImageView(self, item=None):
        if item is None:
            item = self._mainwin.currentItem()
        assert isinstance(item, modelitems.BandItem)

        # only open a new view if there is no other on the item selected
        if len(item.scene.views()) == 0:
            self.newImageView(item)

    def newImageView(self, item=None):
        if item is None:
            item = self._mainwin.currentItem()
        #assert isinstance(item, modelitems.BandItem)
        assert isinstance(item, (modelitems.BandItem, modelitems.DatasetItem))

        # @TODO: check if any graphics view is open on the selected item

        winlist = self._mainwin.mdiarea.subWindowList()
        if len(winlist):
            maximized = winlist[0].windowState() & QtCore.Qt.WindowMaximized
        else:
            maximized = True

	    subwin = GraphicsViewSubWindow(item)

	    self._mainwin.mdiarea.addSubWindow(subwin)
	    grephicsview = subwin.widget()
	    self._mainwin.monitor.register(grephicsview)
	    self._mainwin.mousemanager.register(grephicsview)

	    self.connect(subwin, QtCore.SIGNAL('destroyed()'),
	                 self._mainwin.subWindowClosed)

        if maximized:
            subwin.showMaximized()
        else:
            subwin.show()

        #######################################################################
        ### BEGIN #############################################################
        #missingOverviewLevels = gdalsupport.ovrComputeLevels(item)

        if not isinstance(item, modelitems.DatasetItem):
            dataset = item.parent()
        else:
            dataset = item
        assert isinstance(dataset, modelitems.DatasetItem)
        assert isinstance(dataset, modelitems.CachedDatasetItem)

        # @WARNING: use dataset for levels computation because the
        #           IMAGE_STRUCTURE metadata are not propagated from
        #           CachedDatasetItem to raster bands
        missingOverviewLevels = gdalsupport.ovrComputeLevels(dataset)

        # @NOTE: overviews are computed for all bands so I do this at
        #        application level, before a specific band is choosen.
        #        Maybe ths is not the best policy and overviews should be
        #        computed only when needed instead
        if missingOverviewLevels:
            self._mainwin.logger.debug('missingOverviewLevels: %s' %
                                                        missingOverviewLevels)

            # @TODO: temporary close the dataset; il will be re-opened
            #        after the worker process ending to loaf changes
            #del dataset

            subProc = self._mainwin.controller.subprocess
            if subProc.state() != subProc.NotRunning:
                self._mainwin.logger.warning('unable to perform overview '
                                             'computation: the subprocess '
                                             'controller is currently busy.')
                return
            else:
                self._mainwin.logger.debug('Run the subprocess.')

            # Run an external process for overviews computation
            self._mainwin.progressbar.show()
            self._mainwin.statusBar().showMessage(
                                            'Quick look image generation ...')

            vrtfilename = dataset.vrtfilename
            args = [os.path.basename(vrtfilename)]
            args.extend(map(str, missingOverviewLevels))

            # @WARNING: this is a real mess.
            #
            #           The dataset is attarched to the tool descriptor in
            #           order to be able to retrieve it in the finalization
            #           method.
            #           Finalization also reset the attribute.
            self._mainwin.controller.tool._dataset = dataset

            #self.subprocess.setEnvironmet(...)
            datasetCacheDir = os.path.dirname(vrtfilename)
            subProc.setWorkingDirectory(datasetCacheDir)
            self._mainwin.controller.run_tool(*args)

    def _finalize(self):
        # @TODO: check if opening the dataset in update mode
        #        (gdal.GA_Update) is a better solution

        dataset = getattr(self._mainwin.controller.tool, '_dataset', None)
        if not dataset:
            self._mainwin.logger.debug('unable to retrieve dataset for finalization')
            return

        self._mainwin.controller.tool._dataset = None
        dataset.reopen()
        for row in range(dataset.rowCount()):
            item = dataset.child(row)
            self._mainwin.treeview.expand(item.index())

    ### END ###################################################################
    ###########################################################################

    # @TODO: Open, Masked bands
    # @TODO: dataset --> Build overviews

    ### Overview ##############################################################
    ### Virtualband ###########################################################

### MISC ######################################################################
from gsdview.mainwin import ItemSubWindow

# @TODO: move elsewhere
class GraphicsViewSubWindow(ItemSubWindow):

    def __init__(self, item, parent=None, flags=QtCore.Qt.Widget):
        super(GraphicsViewSubWindow, self).__init__(item, parent, flags)
        title = str(item.GetDescription()).strip()
        self.setWindowTitle(title)

        scene = item.scene
        graphicsview = QtGui.QGraphicsView(scene)
        self.setWidget(graphicsview)
