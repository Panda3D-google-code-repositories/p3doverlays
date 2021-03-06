from pandac.PandaModules import *
import direct.directbase.DirectStart
from direct.task import Task

import overlays

pixel2d = overlays.PixelNode('g2d')

box1 = overlays.Overlay(color=Vec4(.9, .7, .7, 1))
box1.reparentTo(pixel2d)
box1.setPos(50, 50)

textColor = Vec4(0.2,0.2,0.2,1)

#create a border and add it to the scene
bord = overlays.LineBorder(color=textColor)
bord.reparentTo(box1)

#overlays have an optional 'border' -- an overlay that
#is resized/rescaled/repositioned to match changes
box1.setBorder(bord)

myMsg = ''.join(('Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
               ' Aenean at orci nulla. Fusce eu dignissim ligula.',
               ' Ut elementum mauris vitae dui luctus aliquet.',
               ' Phasellus consequat sodales rhoncus.'))


myFont = overlays.TextOverlay.loadFont('res/DejaVuSans.ttf', size=11) 
text = overlays.TextOverlay(msg=myMsg, font=myFont,
                            color=textColor, wordwrap=250)
text.reparentTo(box1)

pad = 5
x, y = box1.getPos()
text.setPos(pad, pad)

w, h = text.getSize()
box1.setSize(w+pad*2, h+pad*2)

base.accept('aspectRatioChanged', pixel2d.aspectRatioChanged)
run()