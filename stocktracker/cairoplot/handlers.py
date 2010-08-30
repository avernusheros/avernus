import cairo
import gtk

class Handler(object):
    """Base class for all handlers."""

    def prepare(self, plot):
        pass

    def commit(self, plot):
        """All handlers need to finalize the cairo context."""
        plot.context.show_page()


class FixedSizeHandler(Handler):
    """Base class for handlers with a fixed size."""

    def __init__(self, width, height):
        """Create with fixed width and height."""
        self.dimensions = {}
        self.dimensions[0] = width
        self.dimensions[1] = height

        # sub-classes must create a surface
        self.surface = None

    def prepare(self, plot):
        """Prepare plot to render by setting its dimensions."""
        Handler.prepare(self, plot)
        plot.dimensions = self.dimensions
        plot.context = cairo.Context(self.surface)

    def commit(self, plot):
        """Commit the plot (to a file)."""
        Handler.commit(self, plot)


class VectorHandler(FixedSizeHandler):
    """Handler to create plots that output to vector files."""

    def __init__(self, surface, *args, **kwargs):
        """Create Handler for arbitrary surfaces."""
        FixedSizeHandler.__init__(self, *args, **kwargs)
        self.surface = surface

    def commit(self, plot):
        """Writes plot to file."""
        FixedSizeHandler.commit(self, plot)
        self.surface.finish()


class PDFHandler(VectorHandler):
    """Handler to create plots that output to pdf files."""

    def __init__(self, filename, width, height):
        """Creates a surface to be used by Cairo."""
        VectorHandler.__init__(self, None, width, height)
        self.surface = cairo.PDFSurface(filename, width, height)


class PNGHandler(FixedSizeHandler):
    """Handler to create plots that output to png files."""

    def __init__(self, filename, width, height):
        """Creates a surface to be used by Cairo."""
        FixedSizeHandler.__init__(self, width, height)
        self.filename = filename
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)

    def commit(self, plot):
        """Writes plot to file."""
        FixedSizeHandler.commit(self, plot)
        self.surface.write_to_png(self.filename)


class PSHandler(VectorHandler):
    """Handler to create plots that output to PostScript files."""

    def __init__(self, filename, width, height):
        """Creates a surface to be used by Cairo."""
        VectorHandler.__init__(self, None, width, height)
        self.surface = cairo.PSSurface(filename, width, height)

class SVGHandler(VectorHandler):
    """Handler to create plots that output to svg files."""

    def __init__(self, filename, width, height):
        """Creates a surface to be used by Cairo."""
        VectorHandler.__init__(self, None, width, height)
        self.surface = cairo.SVGSurface(filename, width, height)


class GTKHandler(gtk.DrawingArea, Handler):
    
    def __init__(self, width, height, *args, **kwargs):
        """Create Handler for arbitrary surfaces."""
        Handler.__init__(self)
        gtk.DrawingArea.__init__(self)
        self.context = None
        self.plot = None
        self.set_size_request(width, height)

        # connect events for resizing/redrawing
        self.connect("expose_event", self.on_expose_event)

    def on_expose_event(self, widget, data):
        """Redraws plot if need be."""
        self.context = widget.window.cairo_create()
        if (self.plot is not None):
            self.plot.render()

    def prepare(self, plot):
        """Update plot's size and context with custom widget."""
        Handler.prepare(self, plot)
        self.plot = plot
        plot.context = self.context

        allocation = self.get_allocation()
        plot.dimensions[0] = allocation.width
        plot.dimensions[1] = allocation.height
        
