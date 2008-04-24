from PyQt4 import QtCore, QtGui

# @TODO: maybe this is not the best solution. Maybe a custom GraphicsItem
#        would be better
class GraphicsView(QtGui.QGraphicsView):
    # @TODO: improve scrolling performances
    #
    #self.graphicsView.horizontalScrollBar.connect(QtCore.SIGNAL('sliderPressed()'), self.startScrolling)
    #self.graphicsView.horizontalScrollBar.connect(QtCore.SIGNAL('sliderReleased()'), self.stopScrolling)
    #self.graphicsView.verticalScrollBar.connect(QtCore.SIGNAL('sliderPressed()'), self.startScrolling)
    #self.graphicsView.verticalScrollBar.connect(QtCore.SIGNAL('sliderReleased()'), self.stopScrolling)
    #self.graphicsView.connect(QtCore.SIGNAL('dragMoveEvent()'), self.startScrolling)
    #self.graphicsView.connect(QtCore.SIGNAL('dropEvent()'), self.stopScrolling)
    #
    #self.graphicsView.connect(QtCore.SIGNAL('mousePressEvent()'), self.startScrolling)
    #self.graphicsView.connect(QtCore.SIGNAL('mouseReleaseEvent()'), self.stopScrolling)

    def mouseMoveEvent(self, event):
        if self.dragMode() == QtGui.QGraphicsView.NoDrag:
            self.emit(QtCore.SIGNAL('mousePositionUpdated(const QPoint&)'),
                      event.pos())
            if event.buttons() & QtCore.Qt.LeftButton:
                self.emit(QtCore.SIGNAL('posMarked(const QPoint&)'), event.pos())
            #event.accept()
        return QtGui.QGraphicsView.mouseMoveEvent(self, event)

    def mousePressEvent(self, event):
        if self.dragMode() == QtGui.QGraphicsView.NoDrag:
            if event.buttons() & QtCore.Qt.LeftButton:
                self.emit(QtCore.SIGNAL('posMarked(const QPoint&)'), event.pos())
            #event.accept()
        return QtGui.QGraphicsView.mousePressEvent(self, event)

    def resizeEvent(self, event):
        self.emit(QtCore.SIGNAL('newSize(const QSize&)'), event.size())
        return QtGui.QGraphicsView.resizeEvent(self, event)

    def scale(self, sx, sy):
        QtGui.QGraphicsView.scale(self, sx, sy)
        self.emit(QtCore.SIGNAL('scaled()'))

    def resetMatrix(self):
        if not self.matrix().isIdentity():
            QtGui.QGraphicsView.resetMatrix(self)
            self.emit(QtCore.SIGNAL('scaled()'))

    # @TODO: check transform related functions

    def clearScene(self):
        scene = self.scene()
        for item in scene.items():
            scene.removeItem(item)

        scene.setSceneRect(0, 0, 1, 1)
        self.setSceneRect(scene.sceneRect())
        self.resetTransform()