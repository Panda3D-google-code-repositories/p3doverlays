"""
This program is a good example of using borders, as well as grouping and 
ordering overlays. 
"""

from pandac.PandaModules import *
import direct.directbase.DirectStart

from overlays import *

pixel2d = PixelNode()

panel = OverlayContainer()
panel.setPos(5, 5)
panel.reparentTo(pixel2d)

#let's give our container a geometry, so that we can see it...
panelBG = Overlay(name='panelgeom', size=(500,500))
panelBG.reparentTo(panel)

#Lets create a border for the above geometry...
#Note: We will add this later, so that it appears on top.
#Alternatively, we could use setZIndex to make it appear on top.
panelBord = LineBorder(color=Vec4(0,0,0,1))
panelBG.setBorder(panelBord)

colors = [Vec4(0.7,0.2,0.2,1), Vec4(0.2,0.2,7,1), Vec4(0.2,0.7,0.2,1)]
widgets = []
for x, c in enumerate(colors):
    ov = Overlay(name='el%d'%x, size=(75, 75), color=c)
    ov.setPos(25*x, 25*x)
    ov.reparentTo(panel)
    widgets.append(ov)
    
#Add the panel border now that the other widgets have been added to the panel
panelBord.reparentTo(panel)

#We can use padding (negative or positive) for a nice effect
bord = LineBorder(color=Vec4(0,0,0,1))
bord.reparentTo(widgets[2])
widgets[2].setBorder(bord, 2)

#Let's make the blue panel the front-most overlay
#(this means it will also appear in front of panelBord)
widgets[1].reparentTo(panel)

panel.node.ls()

fnt = TextOverlay.loadFont('res/DejaVuSans.ttf', size=12)
txt = TextOverlay(msg="Hello!", font=fnt, color=Vec4(1,1,1,1))
txt.reparentTo(panel)
x, y = widgets[1].getPos()
txt.setPos(x+5, y+5)

run()