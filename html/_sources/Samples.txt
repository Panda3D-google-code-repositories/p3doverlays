Tools and Tutorials
=================================

This page is still under construction.

Simple Overlays
--------------------------------

The complete source code for this tutorial can be found 
`here </svn/trunk/samples/TestOverlays.py>`_.

Some Code::

    from pandac.PandaModules import *
    import direct.directbase.DirectStart
    
    import overlays
    
    pixel2d = overlays.PixelNode('g2d')
    
    box1 = overlays.Overlay(color=Vec4(.9, .7, .7, 1))
    box1.reparentTo(pixel2d)
    box1.setZIndex(-1)
    box1.setPos(50, 50)
    
    myFont = overlays.TextOverlay.loadFont('res/Aller_Rg.ttf', size=12) 
    
    myMsg = ''.join(('Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
                   ' Aenean at orci nulla. Fusce eu dignissim ligula.',
                   ' Ut elementum mauris vitae dui luctus aliquet.',
                   ' Phasellus consequat sodales rhoncus.'))
    
    text = overlays.TextOverlay(msg=myMsg, font=myFont, 
                                color=Vec4(0.2,0.2,0.2,1), wordwrap=200)
    text.reparentTo(pixel2d)
    
    pad = 5
    
    x, y = box1.getPos()
    text.setPos(x+pad, y+pad)
    
    w, h = text.getSize()
    box1.setSize(w+pad*2, h+pad*2)
    
    base.accept('aspectRatioChanged', pixel2d.aspectRatioChanged)
    
    run()

Result:

.. image:: tut1.png

Advanced Overlays
---------------------------------

The complete source code for this tutorial can be found 
`here </svn/trunk/samples/TestAdvancedOverlays.py>`_. 

This demo is similar to the first, but it adds some functionality
such as:
* Mouse picking at an overlay's 'absolute screen positions'
* Slicing a texture to create a resizable 2D element
* Grouping overlays with OverlayContainer
* Ordering overlays with z-index

``overlaytool``
---------------------------------

The ``overlaytool`` is a simple visualizer for texture slicing with
overlays, and it's also a demonstration of the power and flexibility 
of this module. All of it -- including the pointer, help window, the text,
and the resizable image itself -- was created using overlays. Working with
pixels made what would have been a difficult project a *very* simple one. 

Run it like the command line like so::

    overlaytool.py TEXTURE

Where TEXTURE is the texture to load, such as ``res/img.png``.

.. note::
    This tool was rushed -- it currently only supports Windows
    (using Arial font and win32clipboard). At a later time, a cleaner,
    cross-platform tool will be released.