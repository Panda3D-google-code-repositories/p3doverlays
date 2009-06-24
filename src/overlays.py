from pandac.PandaModules import *

class GeomEdit:
    """ A base class used only for editing geometry made with GeomGen. """
    
    def startGeom(self, hasColor=False, texture=None):
        self.texture = texture
    def endGeom(self, nodeName):
        return None
    def next(self, x, y, xs, ys, uvdata=None, vertex=None, color=None):
        """
        Rewrites the quad data to the given vertex writer. ``uvdata`` and 
        ``color`` is ignored when editing.
        """
        z = 0
        y = -y
        ys = -ys
        vertex.addData3f(Vec3(x, z, y))
        vertex.addData3f(Vec3(x+xs, z, y))
        vertex.addData3f(Vec3(x+xs, z, y+ys))
        vertex.addData3f(Vec3(x, z, y+ys))
        
class GeomGen(GeomEdit):
    """ Used for initially generating geometry. """
    
    def startGeom(self, hasColor=False, texture=None):
        """
        Called to start creating card geometry. 
        Vertex colours will not be stored if hasColor is left False; this 
        will result in a single-colour geometry. To colour sub-cards differently, 
        use has hasColor=True.
        """
        self.texture = texture
        self.hasColor = hasColor
        format = GeomVertexFormat.getV3c4t2() if hasColor else GeomVertexFormat.getV3t2()
        self.vdata = GeomVertexData('quad', format, Geom.UHStatic)
        self.vertex = GeomVertexWriter(self.vdata, 'vertex')
        self.pigment = None if not hasColor else GeomVertexWriter(self.vdata, 'color')
        self.uv = GeomVertexWriter(self.vdata, 'texcoord')
        self.prim = GeomTriangles(Geom.UHStatic)
        self.n = 0
    
    def next(self, x, y, xs, ys, uvdata=None, vertex=None, color=None):
        """
        Adds a sub-card (a quad) to the current geometry.
        The positions are based on Panda3D's render2d coordinate system: (-1, -1) is bottom 
        left and (1, 1) is top right.
         
        Use the converter methods to pass standard 'screen' position and size -- however,
        it is recommended that the card's upper left corner remains at (0, 0) in 
        world space in order to take full advantage of Node.setPos().
        
        Once all sub-cards have been added, generate the Node via _endGeometry.
        
        When generating, ``vertex`` is generally not used (unless a different vertex 
        writer is desired).
        """
        
        #write vertex data using parent class
        if vertex is None:
            vertex = self.vertex
        GeomEdit.next(self, x, y, xs, ys, uvdata, vertex, color)
        
        #write the rest of the data
        if self.hasColor and color is None:
            color = Vec4(1,1,1,1)
        if self.hasColor:
            self.pigment.addData4f(color)
            self.pigment.addData4f(color)
            self.pigment.addData4f(color)
            self.pigment.addData4f(color)
        u, v, us, vs = 0, -0, 1, -1
        if uvdata is not None and self.texture is not None:
            #1,1  0,1  0,0  1,0
            tx = float(self.texture.getXSize())
            ty = float(self.texture.getYSize())
            u, v, us, vs = uvdata
            u, v, us, vs = (u)/tx, 1-(v)/ty, (us+1)/tx, 1-(vs+1)/ty
            
        self.uv.addData2f(u,v)
        self.uv.addData2f(us,v)
        self.uv.addData2f(us,vs)
        self.uv.addData2f(u,vs)
        
        self.prim.addVertices(self.n, self.n+1, self.n+2)
        self.prim.addVertices(self.n+2, self.n+3, self.n)
        self.prim.closePrimitive()
        self.n += 4
        
    def endGeom(self, nodeName):
        """
        Finishes creating the geometry and returns a node.
        """
        geom = Geom(self.vdata)
        geom.addPrimitive(self.prim)
        
        node = GeomNode("gui_geom")
        node.addGeom(geom)
        
        nodepath = NodePath(nodeName)
        nodepath.attachNewNode(node)
        if self.texture is not None:
            nodepath.setTexture(self.texture)
        nodepath.setTransparency(False)
        nodepath.setDepthWrite(False)
        nodepath.setDepthTest(False)
        nodepath.setTwoSided(True)
        nodepath.setAttrib(LightAttrib.makeAllOff())
        nodepath.setBin("fixed", 0)
        return nodepath

class OverlayContainer(object):
    """ 
    The base class for all overlays, but can also act as a container
    for other overlays (i.e. a panel).
    
    If an overlay name is not specified, it will be generated using
    the class name and a unique identifier, such as::
        
        OverlayContainer241222
    
    You can create your own overlays by extending ``OverlayContainer``
    and passing ``noNode`` as ``True`` (which allows you to create the node).
    After you call this constructor, you can use ``self.name`` to retrieve
    the potentially generated name.
    """
    def __init__(self, name=None, noNode=False):
    
        if name is None:
            name = '%s%i' % (self.__class__.__name__, id(self))
        self.name = name
        self.node = None if noNode else NodePath(self.name)
        self.x, self.y = 0, 0
        self.setZIndex(0)
        
    def setZIndex(self, order):
        """ Sets the z-Index (depth) of this overlay. Higher numbers brings an
        item closer to the front.
        
        .. note:: 
            Under the hood, this simply calls ``setBin('fixed', order)`` on
            the node. """
        self.zIndex = order
        if self.node is not None:
            self.node.setBin('fixed', order)
    
    def getZIndex(self):
        return self.zIndex

    def destroy(self):
        """ Destroys this overlay and removes its node. Any further calls to setPos
        or other node-related methods will raise exceptions. """
        if self.node is not None:
            self.node.removeNode()
            self.node = None
    
    def setPos(self, x, y):
        """
        Sets the position of this overlay in pixels, where (0, 0) 
        is the upper left.
        
        .. note:: 
            Under the hood, this simply calls ``setPos(x, 0, y)`` on the 
            node. Reparenting this to :class:`PixelNode`
            allows us to set its position in screen-space coordinates.
        """
        self.x = x
        self.y = y
        if self.node is not None: 
            self.node.setPos(x, 0, y)
    
    def getPos(self):
        """ Returns the position of this overlay as a tuple of ``(x, y)``,
        in pixels. """
        return self.x, self.y
    
    def reparentTo(self, parent):
        """ Moves this overlay under the given parent node or overlay. """
        if self.node is not None:
            if isinstance(parent, OverlayContainer): 
                self.node.reparentTo(parent.node)
            else:
                self.node.reparentTo(parent)
       
class PixelNode(NodePath, OverlayContainer):
    """
    PixelNode is the root node for all overlays (and 2D elements in general). 
    Overlays should be reparented to this node.

    If ``name`` is not specified, one will be generated. If ``parent`` is not
    specified, Panda's ``render2d`` node will be used.

    .. note::
        Under the hood, PixelNode is a NodePath that is positioned in the upper
        left corner (-1, 0, 1) and scaled to enable pixel positioning (its size
        is 2.0/windowXSize by -2.0/windowYSize). 
    """
    
    def __init__(self, name=None, parent=None):
        OverlayContainer.__init__(self, name)
        NodePath.__init__(self, self.name)
        if parent is None:
            parent = render2d
        self.node = self
        self.reparentTo(parent)
        self.setPos(-1,0,1) #the upper left corner
        self.aspectRatioChanged()

    def aspectRatioChanged(self):
        """
        Called to notify the node that the aspect ratio has been changed. This
        is generally used like so::
            base.accept('aspectRatioChanged', pixelNode.aspectRatioChanged)
        """
        self.setScale(2.0/base.win.getXSize(), 1, -2.0/base.win.getYSize())
            
class Overlay(OverlayContainer):
    """
    Creates an overlay with the given options. If ``texcoords`` or 
    ``atlas`` is not specified, the geometry's vertices will not be 
    generated with UV data from 0 to 1, so that the texture fills to 
    the overlay size.
    
    As with other overlays, if ``name`` is not specified, it will be generated.
    The ``size`` of the overlay can be included at creation to avoid the need to 
    re-write the vertices later. If ``color`` is specified, it will be set on the
    resulting NodePath. 
    
    The ``texcoords`` parameter is a tuple of texture coordinates given in pixels,
    see the tutorials for further details.
    """
        
    geomGen = GeomGen()
    geomEdit = GeomEdit()
        
    def __init__(self, name=None, size=(0, 0), texture=None, 
                 texcoords=None, color=None):
        OverlayContainer.__init__(self, name, noNode=True)
        
        self.texture = texture
        self.width, self.height = size
        self.node = self._draw(Overlay.geomGen, self.width, self.height, texcoords)
        self.node.setTransparency(True)
        if color is not None:
            self.node.setColor(color)
        self.xScale, self.yScale = 1, 1
        self.node.setScale(self.xScale, 1, -self.yScale)
        
    def _draw(self, geom, width, height, texcoords=None, vertex=None):
        geom.startGeom(hasColor=False, texture=self.texture)
        geom.next(0, 0, width, height, texcoords, vertex)
        return geom.endGeom(self.name)
    
    def setScale(self, xScale, yScale):
        """
        Applies the given scale to the overlay, where (1, 1) is a 100% x 
        and y scale (normal).
        """
        self.xScale = xScale
        self.yScale = yScale
        self.node.setScale(xScale, 1, -yScale)
    
    def getScale(self):
        """ Returns the scale of the overlay. """
        return self.xScale, self.yScale
        
    def setSize(self, width, height):
        """ Sets the size of this overlay in pixels. """ 
        if self.width != width or self.height != height:
            vdata = self.node.getChildren()[0].node().modifyGeom(0).modifyVertexData()
            vertex = GeomVertexWriter(vdata, 'vertex')
            vertex.setRow(0)
            vertex.setColumn(0)
            self.width = width
            self.height = height
            self._draw(Overlay.geomEdit, width, height, vertex=vertex)
    
    def getSize(self):
        """ Returns the size of this overlay in pixels, as a tuple of width, height. """
        return self.width, self.height

class OverlaySlice3(Overlay):
    """
    Creates a sliced overlay with the given options, for scaling
    along one axis without quality loss.
    
    Sliced overlays are a single geometry with multiple parts. 3-sliced
    geometries use 3 parts: the center and its two borders. This overlay is useful
    for elements such as scrollbars and sliders.
     
    The ``texcoords`` argument is a tuple of the upper-left and lower-right pixels
    to slice. The default width/height of the ``border`` is 5, and it's assumed
    that there are no gaps between parts. The actual texture coordinates of each
    part will be determined based on the given ``border`` and ``texcoords`` values, and
    whether or not the result should be ``horizontal``.
    """
    
    def __init__(self, name=None, size=(0, 0), texture=None, 
                 border=5, texcoords=None, horizontal=True,
                 color1=Vec4(1, 1, 1, 1), color2=Vec4(.75, .75, .75, 1)):
        self.border = border
        self.horizontal = horizontal
        self.color1 = color1
        self.color2 = color2
        Overlay.__init__(self, name, size, texture, texcoords)
    
    def _draw(self, geom, width, height, texcoords=None, vertex=None):
        uv1, uv2, uv3 = None, None, None
        hasTex = texcoords is not None and self.texture is not None
        if hasTex:
            x1, y1, x2, y2 = texcoords
            #TODO: support tuple of borders for greater flexibility
            if self.horizontal:
                uv1 = (x1, y1, x1+self.border-1, y2)
                uv2 = (x1+self.border, y1, x2-self.border, y2)
                uv3 = (x2-self.border+1, y1, x2, y2)
            else:
                uv1 = (x1, y1, x2, y1+self.border-1)
                uv2 = (x1, y1+self.border, x2, y2-self.border)
                uv3 = (x1, y2-self.border+1, x2, y2)
        #helpful for debugging
        colr1 = None if hasTex else self.color1
        colr2 = None if hasTex else self.color2 
        
        geom.startGeom(hasColor=not hasTex, texture=self.texture)
        if self.horizontal:
            geom.next(0, 0, self.border, height, uv1, vertex, colr1)
            geom.next(self.border, 0, width-self.border*2, height, 
                      uv2, vertex, colr2)
            geom.next(width-self.border, 0, self.border, height, 
                      uv3, vertex, colr1)
        else:
            geom.next(0, 0, width, self.border, uv1, vertex, colr1)
            geom.next(0, self.border, width, height-self.border*2, 
                      uv2, vertex, colr2)
            geom.next(0, height-self.border, width, self.border, 
                      uv3, vertex, colr1)
        return geom.endGeom(self.name)
    
class OverlaySlice9(Overlay):
    """
    Creates a sliced overlay with the given options, for scaling
    along X and Y axis without quality loss.
    
    Sliced overlays are a single geometry with multiple parts. 9-sliced
    geometries use 9 parts: four corners, the center and the surrounding edges. 
    This overlay is useful for elements such as dialogs, buttons and decorated panels.
     
    The ``texcoords`` argument is a tuple of the upper-left and lower-right pixels
    to slice. The default size of the ``border`` edges is 5, and it's assumed
    that there are no gaps between parts. The actual texture coordinates of each
    part will be determined based on the given ``border`` and ``texcoords`` values.
    
    Unlike 3-sliced overlays, 9-slicing uses a more flexible ``border`` to support
    edges of different sizes. It expects a tuple of `(top, left, bottom, right)` edges,
    or a single number to use for all edges.
    """
    
    def __init__(self, name=None, size=(0, 0), texture=None, 
                 border=5, texcoords=None, color1=Vec4(1, 1, 1, 1), 
                 color2=Vec4(.75, .75, .75, 1)):
        self.color1 = color1
        self.color2 = color2
        if not isinstance(border, tuple):
            border = border, border, border, border
        self.border = border
        self.top, self.left, self.bottom, self.right = self.border
        Overlay.__init__(self, name, size, texture, texcoords)
    
    def _draw(self, geom, width, height, texcoords=None, vertex=None):
        uvtl, uvtop, uvtr = None, None, None
        uvleft, uvcenter, uvright = None, None, None
        uvbl, uvbottom, uvbr = None, None, None
        
        hasTex = texcoords is not None and self.texture is not None
        if hasTex:
            x1, y1, x2, y2 = texcoords
            uvtl = (x1, y1, x1+self.left-1, y1+self.top-1)
            uvtop = (x1+self.left, y1, x2-self.right, y1+self.top-1)
            uvtr = (x2-self.right+1, y1, x2, y1+self.top-1)
            
            uvleft = (x1, y1+self.top, x1+self.left-1, y2-self.bottom-1)
            uvcenter = (x1+self.left, y1+self.top, x2-self.right, y2-self.bottom-1)
            uvright = (x2-self.right+1, y1+self.top, x2, y2-self.bottom-1)
            
            uvbl = (x1, y2-self.bottom, x1+self.left-1, y2)
            uvbottom = (x1+self.left, y2-self.bottom, x2-self.right, y2)
            uvbr = (x2-self.right+1, y2-self.bottom+1, x2, y2)
        
        #helpful for debugging
        colr1 = None if hasTex else self.color1
        colr2 = None if hasTex else self.color2 
        
        w, h = width, height
        
        geom.startGeom(hasColor=not hasTex, texture=self.texture)
        #top
        geom.next(self.left, 0, w-self.left-self.right, self.top, uvtop, 
                  vertex, colr2)
        geom.next(0, 0, self.left, self.top, uvtl, vertex, colr1)
        geom.next(w-self.right, 0, self.right, self.top, uvtr,
                  vertex, colr1)
        #mid
        midh = h-self.bottom-self.top
        geom.next(0, self.top, self.left, midh, uvleft, vertex, colr2)
        geom.next(self.left, self.top, w-self.left-self.right, midh, uvcenter, 
                  vertex, colr1)
        geom.next(w-self.right, self.top, self.right, midh, uvright, 
                  vertex, colr2)
        #bottom
        by = h-self.bottom
        geom.next(0, by, self.left, self.bottom, uvbl, vertex, colr1)
        geom.next(self.left, by, w-self.left-self.right, self.bottom, 
                  uvbottom, vertex, colr2)
        geom.next(w-self.right, by, self.right, self.bottom, uvbr, 
                  vertex, colr1)
        return geom.endGeom(self.name)

class TextOverlay(OverlayContainer):
    """ 
    TextOverlay provides a simple manner of displaying crisp text as an overlay.
    Each text overlay contains: a TextNode for generation, a 'top' node, and the
    actual text node (if it exists) parented to the 'top node'.
    
    Overlays use pixelsPerUnit and scaling to generate crisp text. For the best 
    results, you should set the overlay's text size (i.e. text scale) to match 
    the pixelsPerUnit of your font. You can use :const:`AUTO_SIZE` (the default
    text size) to scale the generated text to its pixels per unit -- or 30 if the
    font is not dynamic. Manually setting the size with :func:`setTextSize` 
    is more useful for static fonts, or when you wish to scale the font 
    regardless of its pixels per unit. 
    
    A font height of 1.0 is a Panda standard, and using different values 
    (such as using font.setPointSize, which adjusts the height internally) may
    create undesired results with TextOverlay.
    
    If ``msg`` is specified and ``generate`` is not False, a text node will be generated
    after the properties are set. 
    
    If no ``textGen`` is specified, one will be created. Likewise, if ``font`` is not 
    specified, the ``defaultFont`` will be used if it has been set, otherwise 
    ``textGen``'s default font will be used. The ``color`` is the color for the text
    generator, as is ``align`` and ``wordwrap``.
    
    .. note::
        Wordwrap is given in pixels, and it is assumed to be the desired width
        of the overlay. Using :func:`getSize` with wordwrapping will return the
        wordwrapping, not the frame of the text.
        
    The ``lineHeight`` of a font is initially trimmed, as to remove the extra space 
    above most fonts. Set this to ``False`` if you're having problems
    with text y-offset.
    """
    
    @staticmethod
    def loadFont(ref, size=15, spaceAdvance=None, 
                 lineHeight=None, scaleFactor=1, 
                 textureMargin=2, minFilter=Texture.FTNearest,
                 magFilter=Texture.FTNearest, 
                 renderMode=None):
        """ 
        This function simply calls loadFont with the above parameters -- it is included
        for convenience. 
        
        Note that ``size`` is actually the pixelsPerUnit (for dynamic fonts). See 
        main description for details.
        """
        return loader.loadFont(ref, spaceAdvance=spaceAdvance,
                                    lineHeight=lineHeight, 
                                    pixelsPerUnit=size,
                                    scaleFactor=scaleFactor,
                                    textureMargin=textureMargin,
                                    minFilter=minFilter, magFilter=magFilter)
        
    @staticmethod
    def setFontSize(font, size):
        """
        A convenience function to set the pixelsPerUnit of a dynamic font, if 
        necessary. This function will do nothing if the font is static.
        
        .. note:: 
            This method uses ``Font.clear()`` which wastes memory in Panda 1.6.2
            and early; use it scarcely or not at all. Newer versions of Panda should
            include an easy way to copy fonts for caching, as well as a fix to ensure
            that no associations to the old font pages stay around. 
        """
        if isinstance(font, DynamicTextFont):
            ppu = font.getPixelsPerUnit()
            if ppu != size:
                font.clear()
                font.setPixelsPerUnit(size)
    
    defaultFont = None
    """ Newly created TextOverlays will use this if no font is specified. """
    
    AUTO_SIZE = 'auto'
    """ The text overlay will attempt to set the text size to the pixelsPerUnit
    of the current font. If the current font is not dynamic, it will set
    the text size to 30 (which is the default from egg-mkfont).
    """
    
    def __init__(self, name=None, msg=None, textSize=AUTO_SIZE,
                 textGen=None, font=None, color=Vec4(1, 1, 1, 1), 
                 align=TextNode.ALeft, wordwrap=None, trimHeight=True, 
                 generate=True):
        OverlayContainer.__init__(self, name, noNode=True)
                
        self.node = NodePath(self.name)
        """ A node which contains the text node. """
        self.text = None
        """ The panda node generated from ``TextNode``. """
        
        self.setZIndex(0)
        
        tnn = '%s_text' % self.name
        self.textGen = textGen or TextNode(tnn)
        self.textGen.setName(tnn)
        
        self.trimHeight = trimHeight
        self.setTextSize(textSize)
        
        font = TextOverlay.defaultFont if font is None else font
        if font is not None:
            self.textGen.setFont(font)
        if msg is not None:
            self.textGen.setText(msg)
        self.textGen.setAlign(align)
        self.textGen.setTextColor(color)
        if wordwrap is not None:
            self.setWordwrap(wordwrap)
        if generate and msg is not None:
            self.generate()
    
    def setWordwrap(self, wordwrap):
        """ Sets the wordwrap, in pixels. """
        self.wordwrap = wordwrap
        self.textGen.setWordwrap(wordwrap / self.getTextSize())
    
    def getWordwrap(self):
        """ Returns the wordwrap, in pixels. """
        return self.wordwrap
    
    def setTextSize(self, size):
        """ 
        Sets the scale of the text node and repositions it
        to fit in the upper left (0, 0) of the parent node.
        
        If size is :const:`AUTO_SIZE`, it will attempt to resize the text
        to the current font's pixels per units (or default to size 30 
        for static fonts).
        """
        self.textSize = size
        
        if self.text is not None:
            scale = self.getTextSize() #gets the scale
            self.text.setScale(scale, 1, -scale)
            yoff = 0
            if self.trimHeight:
                yoff = self.lineHeightExtra()
            off = self.textGen.getTop() * scale - yoff
            self.text.setPos(0, 0, off)
    
    def getTextSize(self):
        """ Returns the text size, or attempts to find it if
        :func:`isAutoSize` returns ``True``. """
        if self.isAutoSize():
            f = self.textGen.getFont()
            if isinstance(f, DynamicTextFont):
                return f.getPixelsPerUnit()
            else:
                return 30
        else:
            return self.textSize
    
    def isAutoSize(self):
        """ Returns ``True`` if :data:`AUTO_SIZE` is on. """
        return self.textSize == TextOverlay.AUTO_SIZE
    
    def lineHeightExtra(self):
        """ Returns the line height minus 1.0 (standard Panda text height) in pixels. """
        f = self.textGen.getFont()
        return (f.getLineHeight() - 1.0) * self.getTextSize()
    
    def destroy(self):
        """ Destroys this overlay. """
        self.destroyText()
        self.textGen.removeNode()
        self.textGen = None
        OverlayContainer.destroy(self)
    
    def detachText(self):
        """ Detaches the rendered text node without destroying it, returning
        the text node or None if one did not exist. This also sets this overlay's
        text node to None. """
        if self.text is not None:
            self.text.detachNode()
            self.text = None
        
    def destroyText(self):
        """ Destroys the text node (not the textGen) if it exists. """
        if self.text is not None:
            self.text.removeNode()
            self.text = None
    
    def generate(self):
        """ Destroys the last text node and generates a new node using 
        this overlay's textGen. The new node will be resized to the
        current text size. """
        self.destroyText()
        self.text = NodePath(self.textGen.generate())
        self.text.reparentTo(self.node)
        f = self.textGen.getFont()
        if isinstance(f, DynamicTextFont):
            tw = f.getPageXSize()
            th = f.getPageYSize()
            self.text.setTexOffset(TextureStage.getDefault(), 0.4/tw, -0.4/th)
        self.setTextSize(self.textSize)
        
    def getSize(self):
        """ Returns the size of the text node, in pixels. If
        word-wrapping is set on the textGen, it will be assumed to be the
        desired width.        
        
        Note that no setSize function exists -- use 
        setScale() if you wish to scale the overlay, setTextScale() to set
        point size, or use word-wrapping to set the text box width in pixels 
        (and the height will be computed accordingly). """
        ppu = self.getTextSize()
        h = self.textGen.getHeight() * ppu
        if self.textGen.hasWordwrap():
            w = self.textGen.getWordwrap() * ppu
        else:
            w = self.textGen.getWidth() * ppu
        yoff = 0
        #HACK: add a little for the bottom bit (below baseline) so that
        #the font won't spill out of the returned height
        # For now we will use the 'extra line height', which seems to work
        #well, but if the user requested trimHeight be turned off, then we
        #can simply ignore this
        if not self.trimHeight:
            yoff = self.lineHeightExtra()
        return round(w), round(h+yoff)