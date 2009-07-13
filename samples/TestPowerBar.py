from pandac.PandaModules import *
import direct.directbase.DirectStart
from direct.task import Task

from overlays import *

class TestPowerBar(object):
    
    def __init__(self):
        self.pixel2d = PixelNode('g2d')
        
        self.atlas = loader.loadTexture('res/powerbar.png')
        
        self.outline = Overlay(size=(119, 52), texture=self.atlas,
                         texcoords=(0,52,118, 103))
        self.outline.reparentTo(self.pixel2d)
        self.outline.setPos(5, 100)
        self.outline.setZIndex(1)
        
        self.bars = []
        self.bars.append( self.createBar((4, 37), (16, 50)) )
        self.bars.append( self.createBar((17, 35), (28, 50)) )
        self.bars.append( self.createBar((31, 31), (44, 49)) )
        self.bars.append( self.createBar((48, 25), (61, 47)) )
        self.bars.append( self.createBar((64, 19), (77, 47)) )
        self.bars.append( self.createBar((80, 10), (95, 48)) )
        self.bars.append( self.createBar((96, 3), (115, 49)) )
        
        self.maxPower = len(self.bars)
        self.setPower(0)
        
        font = TextOverlay.loadFont('res/DejaVuSans.ttf', size=13)
        txt = TextOverlay(msg='Use mouse wheel to power up or down.', font=font, 
                          color=Vec4(1,1,1,1))
        txt.setPos(5, 5)
        txt.reparentTo(self.pixel2d)
        
        base.accept('arrow_up', self.onWheel, [1])
        base.accept('arrow_down', self.onWheel, [-1])
        base.accept('wheel_up', self.onWheel, [1])
        base.accept('wheel_down', self.onWheel, [-1])
    
    def onWheel(self, dir):
        self.setPower(max(0, min(self.power + dir, self.maxPower)))
        
    def setPower(self, power):
        self.power = power
        for i, b in enumerate(self.bars):
            if i < power:
                    b.node.show()
            else:
                b.node.hide()
    
    def createBar(self, tex1, tex2):
        x1, y1 = tex1
        x2, y2 = tex2
        size = x2-x1+1, y2-y1+1
        o = Overlay(texture=self.atlas, texcoords=(x1, y1, x2, y2),
                         size=size)
        o.setPos(x1, y1)
        o.reparentTo(self.outline)
        return o

p = TestPowerBar()
run()