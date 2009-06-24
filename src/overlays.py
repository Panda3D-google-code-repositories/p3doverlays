from pandac.PandaModules import *
from direct.showbase.DirectObject import DirectObject

class GeomEdit:
    """
    A dummy base-class for editing an already generated card.
    """
    
    def startGeom(self, hasColor=False, texture=None):
        self.texture = texture
    def endGeom(self, nodeName):
        return None
    def next(self, x, y, xs, ys, uvdata=None, vertex=None, color=None):
        """
        Rewrites the quad data to the given vertex writer.
        
        @color not used
        """
        z = 0
        y = -y
        ys = -ys
        vertex.addData3f(Vec3(x, z, y))
        vertex.addData3f(Vec3(x+xs, z, y))
        vertex.addData3f(Vec3(x+xs, z, y+ys))
        vertex.addData3f(Vec3(x, z, y+ys))
        
class GeomGen(GeomEdit):
    """ An advanced card maker which can generate multiple cards
    in a single node, and which can also have its vertex data rewritten
    for fast resizing. 
    """
    
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
        
        @param vertex generally not used, unless a different vertex writer is desired
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
    def __init__(self, name=None, noNode=False):
        """ 
        The base class for all overlays, but can also act as a container
        for other overlays (i.e. a panel). This is useful when you are using
        the overlays module on its own, independent of any GUI modules.
        
        If an overlay name is not specified, it will be generated using
        the class name and a unique identifier, such as::
            OverlayContainer241222
        
        @param name: the name of this overlay (and its node)
        @param noNode: subclasses should pass True to not immediately create
            a node for this overlay
        @param static: used by subclasses
        """
        if name is None:
            name = '%s%i' % (self.__class__.__name__, id(self))
        self.name = name
        self.node = None if noNode else NodePath(self.name)
        self.x, self.y = 0, 0
        self.setZIndex(0)
        
    def setZIndex(self, order):
        """ Sets the z-Index (depth) of this overlay. Higher numbers brings an
        item closer to the front. """
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
        Sets the position of this overlay on screen, where (0, 0) 
        is the upper left and (x, y) is the lower right, where x and
        y is the window XSize/YSize. 
        """
        self.x = x
        self.y = y
        if self.node is not None: 
            self.node.setPos(x, 0, y)
    
    def getPos(self):
        """ Returns the position of this overlay as a tuple of X, Y. """
        return self.x, self.y
    
    def reparentTo(self, parent):
        """ Moves this overlay under the given parent node or overlay. """
        if isinstance(parent, OverlayContainer): 
            self.node.reparentTo(parent.node)
        else:
            self.node.reparentTo(parent)
    
    def aspectRatioChanged(self):
        """ Called to 'refit' this overlay to the newly changed aspect ratio. 
        Initially does nothing. """
        pass
   
class PixelNode(NodePath, OverlayContainer):
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
        self.setScale(2.0/base.win.getXSize(), 1, -2.0/base.win.getYSize())
            
class Overlay(OverlayContainer):
    """
    Overlays are 2D elements described in pixels, attached to the
    pixel2d node.
    """
    
    geomGen = GeomGen()
    geomEdit = GeomEdit()
    """ The default CardMaker for card-based Overlays. """
        
    def __init__(self, name=None, size=(0, 0), texture=None, 
                 texcoords=None, color=None):
        """
        Creates an overlay with the given options. If texcoords or atlas is 
        not specified, the geometry's vertices will not be generated with UV
        data from 0 to 1, i.e. any texture set on this node's overlay will
        fill to the given size.
        
        @param name: the name for this overlay and its node
        @param size: the size, included here to optionally avoid having to write 
            vertex data twice
        @param texture: the texture atlas to use
        @param texcoords: the texture coordinate for this overlay, generally a tuple of
            X/Y points
        @param color: optional color for this overlay's node
        """
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
        """
        Draws the vertices for this style.
        """
        geom.startGeom(hasColor=False, texture=self.texture)
        geom.next(0, 0, width, height, texcoords, vertex)
        return geom.endGeom(self.name)
    
    def setScale(self, xScale, yScale):
        """
        Scales the overlay. Note that the yScale given to the node will
        actually be negative (to flip the height), so that the texture 
        appears upright.
        """
        self.xScale = xScale
        self.yScale = yScale
        self.node.setScale(xScale, 1, -yScale)
    
    def getScale(self):
        return self.xScale, self.yScale
        
    def setSize(self, width, height):
        """
        Sets the size of this overlay in pixels.
        @param width: the width of this overlay
        @param height: the height of this overlay 
        """ 
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
    def __init__(self, name=None, size=(0, 0), texture=None, 
                 border=5, texcoords=None, horizontal=True,
                 color1=Vec4(1, 1, 1, 1), color2=Vec4(.75, .75, .75, 1)):
        """
        Creates a sliced overlay with the given options, for scaling
        along one axis without quality loss. Texture coordinates should be
        given of the upper left and bottom right as a tuple of (x1,y1,x2,y2).
        It's assumed that there are no gaps between the different parts.
        
        Sliced overlays use 'borders' of a fixed size, and the center is stretched
        so that the overall component fits within the given size. In the case of 
        3-sliced overlays, the 'borders' are the left/right or top/bottom parts
        for horizontal and vertical orientation, respectively. 
        
        @param name: the name for this overlay and its node
        @param size: the initial size of the overlay 
        @param texture: the texture atlas to use
        @param border: the width/height of the corners; default 5
        @param texcoords: the texture coordinate for this overlay, generally a tuple of
            X/Y points
        @param horizontal: True if the orientation is horizontal, False if vertical
        @param color1: only used if no texture is set; useful for debugging (default white)
        @param color2: only used if no texture is set; useful for debugging (default gray)
        """
        self.border = border
        self.horizontal = horizontal
        self.color1 = color1
        self.color2 = color2
        Overlay.__init__(self, name, size, texture, texcoords)
    
    def _draw(self, geom, width, height, texcoords=None, vertex=None):
        """
        Draws the vertices for this style.
        """
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
    def __init__(self, name=None, size=(0, 0), texture=None, 
                 border=5, texcoords=None, color1=Vec4(1, 1, 1, 1), 
                 color2=Vec4(.75, .75, .75, 1)):
        """
        Creates a sliced overlay with the given options, for scaling
        along X and Y axis without quality loss. Texture coordinates should be
        given of the upper left and bottom right as a tuple of (x1,y1,x2,y2).
        It's assumed that there are no gaps between the different parts -- the
        UVs for each part will be calculated according to the border size. 
                        
        @param name: the name for this overlay and its node
        @param size: the initial size of the overlay 
        @param texture: the texture atlas to use
        @param border: a tuple of top, left, bottom, right size (pixels), or a single
            size for all sides
        @param texcoords: the texture coordinate for this overlay, generally a tuple of
            X/Y points
        @param color1: only used if no texture is set; useful for debugging (default white)
        @param color2: only used if no texture is set; useful for debugging (default gray)
        """
        self.color1 = color1
        self.color2 = color2
        if not isinstance(border, tuple):
            border = border, border, border, border
        self.border = border
        self.top, self.left, self.bottom, self.right = self.border
        Overlay.__init__(self, name, size, texture, texcoords)
    
    def _draw(self, geom, width, height, texcoords=None, vertex=None):
        """
        Draws the vertices for this style.
        """
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
    Each text overlay contains a top node to hold the generated text node. 
    
    Overlays use pixelsPerUnit and scaling to generate crisp text. For the best 
    results, you should set the overlay's text size (i.e. text scale) to match 
    the pixelsPerUnit of your font. You can use AUTO_SIZE with dynamic fonts, 
    for convenience. This allows you to change the point size of the font with
    setPixelsPerUnit (being sure to clear() the font, first), then call generate()
    on the text overlay to update the text.
    
    A font height of 1.0 is a Panda standard, and using different values 
    (such as using font.setPointSize, which adjusts the height internally) may
    create undesired results with TextOverlay.
    """
    
    @staticmethod
    def loadFont(ref, size=15, spaceAdvance=None, 
                 lineHeight=None, scaleFactor=1, 
                 textureMargin=2, minFilter=Texture.FTNearest,
                 magFilter=Texture.FTNearest, 
                 renderMode=None):
        """ 
        A convenience function to load a font ready for pixel-based overlays. This
        function simply calls loadFont with the above parameters -- it is included
        for convenience. 
        
        Note that size is actually the pixelsPerUnit (for dynamic fonts). See 
        TextOverlay description for details.
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
        """ Creates a new TextOverlay with the given options. 
        
        @param name: the name for the top node in this overlay, or None to generate one
        @param msg: the text to display for this overlay
        @param textSize: the desired size of the text node, or AUTO_SIZE
        @param textGen: the TextNode to use for generation, or None 
            to create a new instance
        @param font: the font to use in this overlay (and attach to the text)
        @param color: the color of the text, default white
        @param align: the alignment of the text, default TextNode.ALeft
        @param wordwrap: the width (in pixels) for word-wrapping
        @param trimHeight: removes the initial spacing above the text, due to
            the font's line height being scaled
        @param generate: whether or not to generate() this overlay once the above
            properties have been set
        """
        OverlayContainer.__init__(self, name, noNode=True)
                
        self.node = NodePath(self.name)
        """ A node which contains the text node. """
        self.text = None
        """ The panda node generated from TextNode. """
        
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
        self.wordwrap = wordwrap
        self.textGen.setWordwrap(wordwrap / self.getTextSize())
    
    def getWordwrap(self):
        return self.wordwrap
    
    def setTextSize(self, size):
        """ 
        Sets the scale of the text node and repositions it
        to the upper left (0, 0) of the parent node.
        
        If size is AUTO_SIZE, it will attempt to resize the text
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
        isAutoSize returns True. """
        if self.isAutoSize():
            f = self.textGen.getFont()
            if isinstance(f, DynamicTextFont):
                return f.getPixelsPerUnit()
            else:
                return 30
        else:
            return self.textSize
    
    def isAutoSize(self):
        return self.textSize == TextOverlay.AUTO_SIZE
    
    def lineHeightExtra(self):
        """ Returns the line height minus 1.0 (standard Panda text height) in pixels. """
        f = self.textGen.getFont()
        return (f.getLineHeight() - 1.0) * self.getTextSize()
    
    def destroy(self):
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
        """ Clears the last text node and generates a new node using 
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