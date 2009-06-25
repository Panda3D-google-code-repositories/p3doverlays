'''
Created on 19-Jun-09

@author: Matt
'''
from pandac.PandaModules import *
import direct.directbase.DirectStart
from direct.task import Task

import overlays

soldierSheet = loader.loadTexture('res/soldier_sheet.png')
soldierSize = (16, 28)

base.setBackgroundColor(.7, .7, .7, 1)

#root node for overlays
pixel2d = overlays.PixelNode('g2d')

fnt = overlays.TextOverlay.loadFont('res/DejaVuSans.ttf', size=12)
text = overlays.TextOverlay(msg='Press space to walk', font=fnt)
text.reparentTo(pixel2d)
text.setPos(5, 5)

soldier = overlays.OverlayContainer('soldier')
soldier.reparentTo(pixel2d)

#creates a hidden overlay and adds it to the soldier container
def addSoldierState(x1, y1, x2, y2):
    o = overlays.Overlay(texture=soldierSheet, 
                            texcoords=(x1, y1, x2, y2),
                            size=soldierSize)
    o.node.hide()
    o.reparentTo(soldier)
    return o

right_idle = addSoldierState(0, 40, 15, 66)
right_walk1 = addSoldierState(35, 39, 50, 66)
right_walk2 = addSoldierState(70, 39, 85, 66)

#show the idling state
right_idle.node.show()

soldier.setPos(50, 50)

box = overlays.Overlay(size=(300, 300), color=Vec4(0.2, 0.7, 0.2, 1)) 
box.setZIndex(-1)
box.reparentTo(pixel2d)

moving = False
timer = 0
currentState = right_idle

def anim_walk_right():
    global currentState
    next = right_walk2 if currentState == right_walk1 else right_walk1
    currentState.node.hide()
    currentState = next
    currentState.node.show()

def moveTask(task):
    global timer
    if moving:
        delta = globalClock.getDt()
        d = 0.8 #+ delta*0.3
        #swap animation
        if task.time - timer > 0.25:
            anim_walk_right()
            timer = task.time
        x, y = soldier.getPos()
        x, y = x+d, y+d
        w, h = currentState.getSize()
        bw, bh = box.getSize()
        if x+w > bw:
            x = 0
        if y+h > bh:
            y = 0
        soldier.setPos(round(x), round(y))
    else:
        timer = -100
        if currentState != right_idle:
            currentState.node.hide()
            right_idle.node.show()
            x, y = soldier.getPos()
            soldier.setPos(round(x), round(y))
    return Task.cont

taskMgr.add(moveTask, 'MoveTask')

def setMoving(b):
    global moving
    moving = b

base.accept('space', setMoving, [True])
base.accept('space-up', setMoving, [False])
base.accept('aspectRatioChanged', pixel2d.aspectRatioChanged)
run()