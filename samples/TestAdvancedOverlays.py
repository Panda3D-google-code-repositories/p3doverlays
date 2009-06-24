"""

"""

from pandac.PandaModules import *
import direct.directbase.DirectStart
from direct.task import Task
import sys
import math

import overlays as hud

class TestAdvancedOverlays:
    def __init__(self):
        #variables for our program
        self.wordwrap1 = 200
        self.wordwrap2 = 400
        self.padding = 5
        textColor = Vec4(0.2, 0.2, 0.2, 1)
        self.lastX = 0
        self.lastY = 0
        self.hasMouse = False
        self.hoverColor = Vec4(1, 1, 1, 1)
        self.upColor = Vec4(1, 1, 1, 0.5)
        self.inside = False
        
        base.setBackgroundColor(Vec4(1, 1, 1, 1))
        
        #Since the texture has irregular insets (for the drop shadow)
        #we will need to offset the background to make the text fit nicely.
        #We can also use this for a more exact rollover effect
        self.insets = (0, 2, 4, 3)
        
        #Initialize a 'pixel node' which overlays will be reparented to
        #This inherits from both OverlayContainer and NodePath
        self.pixel2d = hud.PixelNode('g2d') 
        
        #Create a container to group our overlays
        panel = hud.OverlayContainer('panel')
        panel.reparentTo(self.pixel2d)
        panel.setPos(50, 100)
        
        #Create a sliced overlay for the panel background
        #We'll order it behind the text
        tex = loader.loadTexture('res/simple_ui.png')
        tex.setMagfilter(Texture.FTNearest)
        self.panelBg = hud.OverlaySlice9(texture=tex, 
                                         texcoords=(0, 0, 54, 53),
                                         border=(9, 9, 11, 10))
        self.panelBg.node.setColor(self.upColor)
        self.panelBg.reparentTo(panel)
        self.panelBg.setZIndex(-10)
        self.panelBg.setPos(-self.insets[1], -self.insets[0])
        
        #Convenience method to load a crisp font at size 14 pt
        font = hud.TextOverlay.loadFont('/c/Windows/Fonts/arial.ttf', size=14)
        hud.TextOverlay.defaultFont = font
        
        #Write some instructions
        txt = hud.TextOverlay(msg="Click the box to change its width",
                              color=textColor)
        txt.reparentTo(self.pixel2d)
        txt.setPos(10, 10)
        
        msg = ''.join(('Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                       ' Aenean at orci nulla. Fusce eu dignissim ligula.',
                       ' Ut elementum mauris vitae dui luctus aliquet.',
                       ' Phasellus consequat sodales rhoncus. Phasellus ut',
                       ' vestibulum enim. Nulla ornare nisi eget purus iaculis',
                       ' ac dignissim purus ullamcorper.'))
        
        #write a wordwrapped message
        self.panelTxt = hud.TextOverlay(msg=msg, color=textColor,
                                        wordwrap=self.wordwrap1)
        self.panelTxt.reparentTo(panel)
        self.panelTxt.setPos(self.padding, self.padding)
        
        self.setRollover(False)
        
        #resize the bg panel to the text
        self.updateBoxSize()
         
        #listen for mouse movement..
        taskMgr.add(self.MouseMotionTask, "MouseMotionTask")
        
        #listen for aspect ratio changes
        base.accept('mouse1', self.click)
        base.accept('aspectRatioChanged', self.pixel2d.aspectRatioChanged)
        base.accept('escape', sys.exit)
    
    def setRollover(self, b):
        #turns rollover effect on/off
        self.inside = b
        c = self.hoverColor if b else self.upColor
        self.panelBg.node.setColor(c)
    
    def updateBoxSize(self):
        #We'll use the insets so that the text will fit nicely inside the square
        w, h = self.panelTxt.getSize()
        self.panelBg.setSize(w+self.padding*2+self.insets[1]+self.insets[3], 
                             h+self.padding*2+self.insets[0]+self.insets[2])
    
    def click(self):
        #if the mouse is inside the box, consider it a click
        if self.inside:
            is1 = self.panelTxt.getWordwrap() == self.wordwrap1
            ww = self.wordwrap2 if is1 else self.wordwrap1
             
            #update the text
            self.panelTxt.setWordwrap(ww)
            self.panelTxt.generate()
            
            #resize the background to the new text size
            self.updateBoxSize()
            
            #quick hack to re-check the mouse rollover
            self.mouseMoved(self.lastX, self.lastY)
    
    def getAbsolutePos(self, overlay):
        """ Helper method to get the "absolute screen position" of the 
        given overlay (i.e. its position + the sum of its parents' position). """
        parent = overlay.node
        abx, aby = overlay.getPos()
        while parent != None:
            parent = parent.getParent()
            if parent is None or parent == self.pixel2d:
                break
            else:
                x, nil, y = parent.getPos()
                abx += x
                aby += y
        return abx, aby
    
    def render2pixel(self, x, y):
        """ Helper method to convert Panda's 2D mouse coordinates 
        to screen-space coordinates. """
        p2d = self.pixel2d.getRelativePoint(render2d, Point3(x, 0, y))
        return int(math.ceil(p2d[0])), int(math.ceil(p2d[2])) 
        
    def mouseMoved(self, x, y):
        #mouse has moved.. check if its inside our box
        w, h = self.panelBg.getSize()
        abx, aby = self.getAbsolutePos(self.panelBg)
        
        inX = x > abx+self.insets[1] and x < abx+w-self.insets[3]
        inY = y > aby+self.insets[0] and y < aby+h-self.insets[2]
        self.setRollover(inX and inY)
        
    def mouseLost(self):
        #can't find mouse, assume its no longer over our box
        self.setRollover(False)
    
    def MouseMotionTask(self, task):
        """ Listens for mouse movements.  """
        if base.mouseWatcherNode.hasMouse():
            self.hasMouse = True 
            x = base.mouseWatcherNode.getMouseX()
            y = base.mouseWatcherNode.getMouseY()
            x, y = self.render2pixel(x, y)
            if x!=self.lastX or y!=self.lastY:
                self.mouseMoved(x, y)
                self.lastX = x
                self.lastY = y
        elif self.hasMouse:
            self.hasMouse = False
            self.mouseLost()
        return Task.cont
    
t = TestAdvancedOverlays()
run()