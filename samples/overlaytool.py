'''
Created on 18-Jun-09

@author: Matt
'''
from pandac.PandaModules import *
import direct.directbase.DirectStart
from direct.task import Task

import sys
import math

from overlays import *

import win32clipboard as w
import win32con

class OverlayTool(object):
    
    """ Change these to be cross-platform later... """
    def getClipboard(self): 
        w.OpenClipboard() 
        d=w.GetClipboardData(win32con.CF_TEXT) 
        w.CloseClipboard() 
        return d 
     
    def setClipboard(self, aType, aString): 
        w.OpenClipboard()
        w.EmptyClipboard()
        w.SetClipboardData(aType,aString) 
        w.CloseClipboard()
    
    def __init__(self, tex, bgColor=Vec4(1, 1, 1, 1)):
        self.tex = tex
        self.bgColor = bgColor
        self.ROW_COL_MAX = 1000
        self.lastPointerScale = 1
        self.zoomMax = 14
        self.zoomAmt = 1
        self.zoomMin = .25
        self.measureWidth = 0
        self.measureHeight = 0
        self.shiftDown = False
        
        #create an image for getting RGB values
        #self.image = PNMImage()
        #tex.store(self.image)
        
        #mouse x/y
        self.lastX = 0 
        self.lastY = 0
        
        #"status bar" label
        self.statusPrefix = 'Pres H for help\nClipboard: '
        
        #texture stuff
        self.tex.setMagfilter(Texture.FTNearest)
        self.tx, self.ty = self.tex.getXSize(), self.tex.getYSize()
        self.moveDrag = False
        self.measureDrag = False
        self.measureStartPoint = (0, 0)
        
        self.px, self.py = 0, 0
        
        #base.setBackgroundColor(bgColor)
        
        #create an overlay
        self.pixel2d = PixelNode('hud')
        
        self.tex.setBorderColor(Vec4(0, 0, 0, 1))
        
        self.overlay = Overlay(texture=self.tex, size=(self.tx, self.ty))
        self.overlay.setZIndex(-10)
        self.overlay.reparentTo(self.pixel2d)
        self.overlay.node.setTransparency(True)
        
        self.overlayBG = Overlay(size=(self.tx, self.ty), color=bgColor)
        self.overlayBG.setZIndex(-11)
        self.overlayBG.reparentTo(self.pixel2d)
        
        pointerCol = Vec4(1, 0, 0, 0.7)
        self.pointer = Overlay(size=(1, 1))
        self.pointer.node.setColor(pointerCol)
        self.pointer.setPos(self.px, self.py)
        self.pointer.reparentTo(self.pixel2d)
        
        gridColor = Vec4(1, 0, 0, 0.4)
        self.gridRow = Overlay(size=(1, 1))
        self.gridRow.node.setColor(gridColor)
        self.gridRow.reparentTo(self.pixel2d)
        self.gridRow.setZIndex(90)
        
        self.gridCol = Overlay(size=(1, 1))
        self.gridCol.node.setColor(gridColor)
        self.gridCol.reparentTo(self.pixel2d)
        self.gridCol.setZIndex(90)
        
        self.setShowGridRow(False)
        self.setShowGridCol(False)
        #TODO: simply scale the pointer based on mouse measure
        #TODO: shift / alt to create rows / heights -- simply scale and then scale back when key is released
                    
        labelFont = TextOverlay.loadFont("/c/Windows/Fonts/arial.ttf", size=13)
        
        #we can use this to avoid having to pass it to all TextOverlays
        TextOverlay.defaultFont = labelFont
        
        #create our instructions, initially hidden
        #we create this first so that the rest of the text overlays can use
        #a font of size 13
        self.helpOverlay = self.createHelpOverlay()
        self.helpOverlay.node.hide()
        self.helpVisible = False
        
        #sets the font size to use in generating text
        #will do nothing unless createHelpOverlay() changes the font size
        TextOverlay.setFontSize(labelFont, 13)
        
        #now let's create some text on top
        self.text = TextOverlay(msg=self.statusPrefix, color=Vec4(0, 0, 0, 1))
        self.text.reparentTo(self.pixel2d)
        self.text.setZIndex(10)
        
        #some text to display coordinates
        self.coordsText = TextOverlay(msg="(0, 0)", color=Vec4(0, 0, 0, 1))
        self.coordsText.setPos(5, 5)
        self.coordsText.reparentTo(self.pixel2d)
        self.coordsText.setZIndex(10)
        
        self.sizeText = TextOverlay(color=Vec4(0, 0, 0, 1))
        self.sizeText.setPos(5, self.coordsText.getSize()[1]+10)
        self.sizeText.reparentTo(self.pixel2d)
        self.sizeText.setZIndex(10)
        
        #faded background so we can see our text
        textBGColor = Vec4(1, 1, 1, 0.6)
        self.textBG = Overlay(color=textBGColor)
        self.textBG.reparentTo(self.pixel2d)
        self.textBGHeight = 45
        self.textBG.setZIndex(9)
        
        self.upperBG = Overlay(color=textBGColor)
        self.upperBG.setSize(self.coordsText.getSize()[0]+90, 50)
        self.upperBG.reparentTo(self.pixel2d) 
        self.upperBG.setZIndex(9)
        self.upperBGWidth = self.upperBG.getSize()[0]
        
        self.clearClipboard()
        self.view_reset()
        
        zin = [1, lambda s: s <= self.zoomMax]
        zout = [-1, lambda s: s >= self.zoomMin]
        base.accept('wheel_up', self.zoom, zin)
        base.accept('wheel_down', self.zoom, zout)
        base.accept('=', self.zoom, zin)   #support mice w/o wheels
        base.accept('-', self.zoom, zout)
        base.accept('space', self.pushClipboard)
        base.accept('backspace', self.popClipboard)
        base.accept('delete', self.popClipboard)
        base.accept('escape', self.clearClipboard)
        base.accept('mouse3', self.setMoveDrag, [True])
        base.accept('mouse3-up', self.setMoveDrag, [False])
        base.accept('mouse1', self.setMeasureDrag, [True])
        base.accept('mouse1-up', self.setMeasureDrag, [False])
        base.accept('mouse2', self.view_reset)
        base.accept('r', self.view_reset)
        base.accept('h', self.toggleHelp)
        base.accept('aspectRatioChanged', self.aspectRatioChanged)
        base.accept('shift', self.setShowGridRow, [True])
        base.accept('shift-up', self.setShowGridRow, [False])
        base.accept('alt', self.setShowGridCol, [True])
        base.accept('alt-up', self.setShowGridCol, [False])
        
        taskMgr.add(self.MouseMotionTask, "MouseMotionTask")
    
    def getRGB(self, x, y):
        if x > 0 and y > 0 and x < self.tx and y < self.ty:
            r = self.image.getRedVal(x, y)
            g = self.image.getGreenVal(x, y)
            b = self.image.getBlueVal(x, y)
            return r, g, b
        else:
            return None
    
    def createHelpOverlay(self):
        #instructions
        tpColor = TextProperties()
        tpColor.setTextColor(Vec4(1, 1, 1, 1))
        
        tpMgr = TextPropertiesManager.getGlobalPtr()
        tpMgr.setProperties("h", tpColor)
        self.helpText = '\1h\1Overlay Tool - Help\2\n(press H to toggle)\n\n' \
                    + '\1h\1Mouse Wheel -\2 zoom in/out\n' \
                    + '\1h\1Right Mouse Button -\2 move the texture atlas\n' \
                    + '\1h\1Middle Mouse Button -\2 reset the view\n' \
                    + '\1h\1Left Mouse Button -\2 drag to measure\n' \
                    + '\1h\1Shift / Alt -\2 toggle row/column guides\n' \
                    + '\1h\1Space -\2 add point or size to clipboard\n' \
                    + '\1h\1Delete -\2 remove last clipboard entry\n' \
                    + '\1h\1Escape -\2 reset the clipboard\n\n' \
                    + 'The Overlay Tool helps you quickly visualize and' \
                    + ' set up texture atlas coordinates for your overlays.'
        
        panel = OverlayContainer('helpPane')
        panel.reparentTo(self.pixel2d)
        
        #width and padding
        width = 325
        c = 5 
        
        bg = Overlay(color=Vec4(0, 0, 0, 0.85))
        bg.reparentTo(panel)
        bg.setZIndex(100)
        
        helpText = TextOverlay(msg=self.helpText, 
                                wordwrap=width, color=Vec4(.75, .75, .75, 1))
        helpText.reparentTo(self.pixel2d)
        helpText.setPos(c, c)
        helpText.reparentTo(panel)
        helpText.setZIndex(101)
        
        self.helpWidth, self.helpHeight = helpText.getSize()
        bg.setSize(self.helpWidth+c*2, self.helpHeight+c*2)
        return panel
    
    #called on load -- skips us having to re-write it all at overlay creation
    def aspectRatioChanged(self):
        winx = base.win.getXSize()
        winy = base.win.getYSize()
        
        self.pixel2d.aspectRatioChanged()
        self.text.setPos(5, winy-self.text.getSize()[1]-5)
        self.textBG.setSize(winx, self.textBGHeight)
        self.textBG.setPos(0, winy-self.textBG.getSize()[1])
        self.helpOverlay.setPos(winx/2-self.helpWidth/2, 
                                winy/2-self.helpHeight/2)
        
    def popClipboard(self):
        str = self.text.textGen.getText()
        x = str.rfind('(')
        if x != -1:
            str = str[:x].rstrip()
            #test again to add a space
            x = str.rfind('(')
            if x == -1:
                str = ' '.join((str, ''))
            self.text.textGen.setText(str)
            self.text.generate()
            self.setClipboard(win32con.CF_TEXT, str[str.rfind(':'):].lstrip())
        
    #TODO: Output modes:
    # NOT REALLY IMPORTANT, because most uses will be for THEMES rather than raw Overlays
    #  Clipboard: (13 x 14) (16, 16) etc
    #  Clipboard: corners=5 texcoords=(0, 0, 50, 50) size=(15, 15) 
    #  Clipboard: corners=(5, 12) texcoords=(0, 0, 50, 50) size=(25, 25)
    
    def pushClipboard(self):
        str = self.getClipboard()
        nx, ny = 0, 0
        if self.measureDrag:
            nx, ny = self.measureWidth, self.measureHeight
        else:
            nx, ny = self.getPixelPos()
        
        delim = ' x ' if self.measureDrag else ', '
        pStr = '(%d%s%d)' % (nx, delim, ny)
        self.setClipboard(win32con.CF_TEXT, ' '.join((str, pStr)))
        self.text.textGen.appendText('%s ' % pStr)
        self.text.generate()
    
    def clearClipboard(self):
        self.setClipboard(win32con.CF_TEXT, "")
        if self.text.textGen.getText() != self.statusPrefix:
            self.text.textGen.setText(self.statusPrefix)
            self.text.generate()
    
    def zoom(self, mult, func):
        oldS,ys = self.overlay.getScale()
        s = math.floor(oldS+self.zoomAmt*mult)
        if func(s): #func is a min or max check
            x, y = self.pointer.getPos()
            self.overlay.setScale(s, s)
            self.overlayBG.setScale(s, s)
            self.pointer.setScale(s, s)
            self.pointer.setPos(x-self.px, y-self.py)
            self.move_pointer(self.lastX, self.lastY)
            
            self.lastPointerScale = s
            self.setMeasureDrag(False)
            #TODO: fix zoom so it is centered
            
    def move_pointer(self, x, y):
        s, ys = self.overlay.getScale()
        s = float(s)
        ox, oy = self.overlay.getPos()
        nx = int((x-ox) / s)*s
        ny = int((y-oy) / s)*s
        pixelX, pixelY = int(nx/s), int(ny/s)
        if self.measureDrag:
            #gets current pixel
            px, py = pixelX+1, pixelY+1
            xSize = px-self.measureStartPoint[0]
            ySize = py-self.measureStartPoint[1] if not self.shiftDown else xSize
            self.pointer.setScale(s*xSize, 
                                  s*ySize)
            self.measureWidth = abs(xSize)
            self.measureHeight = abs(ySize)
            str = 'Size: %d x %d' % ( self.measureWidth, self.measureHeight )
            if self.sizeText.textGen.getText() != str:
                self.sizeText.textGen.setText(str)
                self.sizeText.generate()
        else:
            self.pointer.setPos(nx + ox, ny + oy)
        
        self.gridRow.setPos(0, ny + oy)
        self.gridCol.setPos(nx + ox, 0)
        
        xs, ys = self.pointer.getScale()
        self.gridRow.setScale(self.ROW_COL_MAX, ys)
        self.gridCol.setScale(xs, self.ROW_COL_MAX)
        
        #rgb = self.getRGB(pixelX, pixelY)
        #rgbStr = ''
        #if rgb is not None:
        #    rgbStr = ', rgb=(%d, %d, %d)' % rgb
        
        str = '(%d, %d)' % (pixelX, pixelY) 
        if self.coordsText.textGen.getText() != str:
            self.coordsText.textGen.setText(str)
            self.coordsText.generate()
        
    def setShowGridRow(self, b):
        self.shiftDown = b
        if b and not self.measureDrag:
            self.gridRow.node.show()
        else:
            self.gridRow.node.hide()
    
    def setShowGridCol(self, b):
        if b and not self.measureDrag:
            self.gridCol.node.show()
        else:
            self.gridCol.node.hide()
            
    def view_reset(self):
        self.overlay.setScale(1, 1)
        self.overlayBG.setScale(1, 1)
        self.pointer.setScale(1, 1)
        s, ys = self.overlay.getScale()
        w, h = s*self.tx, s*self.ty
        self.overlay.setPos(abs(base.win.getXSize()/2-w/2),
                            abs(base.win.getYSize()/2-h/2))
        x, y = self.overlay.getPos()
        self.overlayBG.setPos(x, y)
        
    def getPixelPos(self):
        x, y = self.lastX, self.lastY
        s, ys = self.overlay.getScale()
        s = float(s)
        ox, oy = self.overlay.getPos()
        nx = int((x-ox) / s)
        ny = int((y-oy) / s)
        return nx, ny
        
    def mouseMoved(self, x, y):
        if self.moveDrag:
            ox, oy = self.overlay.getPos()
            dx = math.floor(self.lastX-x)
            dy = math.floor(self.lastY-y)
            self.overlay.setPos(ox-dx, oy-dy)
            self.overlayBG.setPos(ox-dx, oy-dy)
            x, y = self.pointer.getPos()
            self.pointer.setPos(x-dx, y-dy)
        else:
            self.move_pointer(x, y)
            
    def mouseLost(self):
        self.setMeasureDrag(False)
        self.setMoveDrag(False)
        
    #Task to move the camera
    def MouseMotionTask(self, task):
        if base.mouseWatcherNode.hasMouse():
            x = base.mouseWatcherNode.getMouseX()
            y = base.mouseWatcherNode.getMouseY()
            p2d = self.pixel2d.getRelativePoint(render2d, Point3(x, 0, y))
            x = int(math.ceil(p2d[0]))
            y = int(math.ceil(p2d[2]))
            if x!=self.lastX or y!=self.lastY:
                self.mouseMoved(x, y)
                self.lastX = x
                self.lastY = y
        else:
            self.mouseLost()
        return Task.cont
    
    def setMoveDrag(self, b):
        self.moveDrag = b
    
    def setMeasureDrag(self, b):
        self.measureDrag = b
        if b:
            self.measureStartPoint = self.getPixelPos()
            self.lastPointerScale = self.pointer.getScale()[0]
            self.setShowGridRow(False)
            self.setShowGridCol(False)
            self.measureWidth = 0
            self.measureHeight = 0
        else:
            self.pointer.setScale(self.lastPointerScale, 
                                  self.lastPointerScale)            
            self.move_pointer(self.lastX, self.lastY)
            if self.sizeText.textGen.getText() != "":
                self.sizeText.textGen.setText("")
                self.sizeText.generate()
    
    def toggleHelp(self):
        self.helpVisible = not self.helpVisible
        if self.helpVisible:
            self.helpOverlay.node.show()
        else:
            self.helpOverlay.node.hide()


if __name__ == '__main__':
    #debug
    sys.argv.append('res/simple_ui.png')
    
    if len(sys.argv) <= 1:
        print 'Format:\n    overlaytool myTexture.png'
    tex = loader.loadTexture(sys.argv[1])
    print tex.getXSize(), tex.getYSize()
    o = OverlayTool(tex)
    run()