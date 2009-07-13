from pandac.PandaModules import *
import direct.directbase.DirectStart
from direct.task import Task

from overlays import *

class TestPowerBar(object):
    
    def __init__(self):
        self.filling = False
        
        self.pixel2d = PixelNode('g2d')
        
        self.atlas = loader.loadTexture('res/powerbar.png')
        
        self.outline = Overlay(size=(119, 52), texture=self.atlas,
                         texcoords=(0, 52, 118, 103))
        self.outline.reparentTo(self.pixel2d)
        self.outline.setPos(50, 100)
        self.outline.setZIndex(1)
        
        self.bars = Overlay(size=(119, 52), texture=self.atlas,
                         texcoords=(0, 0, 118, 51))
        self.bars.reparentTo(self.outline)
        
        #create a mask
        maskImg = PNMImage(128, 64)
        maskImg.fill(1)
        maskImg.alphaFill(1)
        self.mask = Texture()
        self.mask.load(maskImg)
        self.mask.setWrapU(Texture.WMBorderColor)
        self.mask.setWrapV(Texture.WMBorderColor)
        self.mask.setBorderColor(VBase4(1, 1, 1, 0.0))
        
        self.stage = TextureStage('ts')
        self.stage.setMode(TextureStage.MModulate)
        self.bars.node.setTexture(self.stage, self.mask)
        self.tx = float(self.mask.getXSize())
        
        def offs(l):
            for i, e in enumerate(l):
                l[i] = (self.tx - e) / self.tx
            return l
        self.offsets = offs([0, 16, 28, 44, 61, 77, 95, self.tx])
        self.setPower(0)
        
        #add some instructions
        font = TextOverlay.loadFont('res/DejaVuSans.ttf', size=13)
        self.txt = TextOverlay(msg='Use mouse wheel to power up or down, and space to fill.', 
                          font=font, color=Vec4(1,1,1,1))
        self.txt.setPos(5, 5)
        self.txt.reparentTo(self.pixel2d)

        base.accept('arrow_up', self.onChange, [1])
        base.accept('arrow_down', self.onChange, [-1])
        base.accept('wheel_up', self.onChange, [1])
        base.accept('wheel_down', self.onChange, [-1])
        base.accept('space', self.fill)

    def onChange(self, dir):
        maxIndex = len(self.offsets) - 1
        if self.filling:
            self.filling = False
            taskMgr.remove('TweenMask')
            self.setPower(maxIndex)
        self.setPower(max(0, min(self.power + dir, maxIndex)))
    
    def setPower(self, power):
        self.power = power
        self.bars.node.setTexOffset(self.stage, self.offsets[power], 0)

    def fill(self):
        if self.filling:
            taskMgr.remove('TweenMask')
        self.filling = True
        self.setPower(0)
        self.begin = 0
        self.finish = self.tx
        self.change = self.finish - self.begin
        self.duration = 120
        self.time = 0
        self.power = len(self.offsets) - 1
        self.lastOff = 0
        taskMgr.add(self.TweenMask, 'TweenMask')
    
    def TweenMask(self, task):
        x = self.easeOut(self.time, self.begin, self.change, self.duration)
        doff = (self.tx - x)/self.tx
        self.bars.node.setTexOffset(self.stage, doff, 0)
        self.time += 1
        if self.time > self.duration:
            self.filling = False
            return Task.done
        else:
            return Task.cont
    
    def easeOut(self, t, b, c, d):
        t = t/float(d)-1
        return c*(t*t*t*t*t + 1) + b
    
     
t = TestPowerBar()
run()