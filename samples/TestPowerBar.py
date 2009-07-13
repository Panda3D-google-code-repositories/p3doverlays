from pandac.PandaModules import *
import direct.directbase.DirectStart
from direct.task import Task

from overlays import *

class TestPowerBar(object):
    
    def __init__(self):
        self.pixel2d = PixelNode('g2d')
        
        self.atlas = loader.loadTexture('res/powerbar.png')
        self.mask = loader.loadTexture('res/powerbar_mask.png')
        
        self.outline = Overlay(size=(119, 52), texture=self.atlas,
                         texcoords=(0, 52, 118, 103))
        self.outline.reparentTo(self.pixel2d)
        self.outline.setPos(50, 100)
        self.outline.setZIndex(1)
        
        self.bars = Overlay(size=(119, 52), texture=self.atlas,
                         texcoords=(0, 0, 118, 51))
        self.bars.reparentTo(self.outline)
        
        self.stage = TextureStage('ts')
        self.stage.setMode(TextureStage.MModulate)
        self.bars.node.setTexture(self.stage, self.mask)
        self.mask.setWrapU(Texture.WMBorderColor)
        self.mask.setWrapV(Texture.WMBorderColor)
        self.mask.setBorderColor(VBase4(1, 1, 1, 0.0))
        self.tx = float(self.mask.getXSize())
        
        def offs(l):
            for i, e in enumerate(l):
                l[i] = (self.tx - e) / self.tx
            return l
        self.offsets = offs([0, 16, 28, 44, 61, 77, 95, 115])
        self.setPower(0)
        
        #add some instructions
        font = TextOverlay.loadFont('res/DejaVuSans.ttf', size=13)
        txt = TextOverlay(msg='Use mouse wheel to power up or down.', 
                          font=font, color=Vec4(1,1,1,1))
        txt.setPos(5, 5)
        txt.reparentTo(self.pixel2d)
        
        base.accept('arrow_up', self.onChange, [1])
        base.accept('arrow_down', self.onChange, [-1])
        base.accept('wheel_up', self.onChange, [1])
        base.accept('wheel_down', self.onChange, [-1])

    def onChange(self, dir):
        maxIndex = len(self.offsets) - 1
        self.setPower(max(0, min(self.power + dir, maxIndex)))
    
    def setPower(self, power):
        self.power = power
        self.bars.node.setTexOffset(self.stage, self.offsets[power], 0)

t = TestPowerBar()
run()