#!/usr/bin/env python
import gtk, cairo, time, calendar


def _get_extremum_length(list, max = True):
    """get the longest/shortest item of a list without changing the list"""
    op = None
    if max:
        op = lambda a,b: a > b
    else:
        op = lambda a,b: a < b
    if len(list) == 1:
        return list[0]
    res = list[0]
    for item in list:
        if op(len(item),len(res)):
            res = item
    return item

Weekday = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
  'Friday', 'Saturday', 'Sunday']

"""Second values"""
MINUTE  = 60
HOUR    = 3600
DAY     = 86400
WEEK    = 604800
# for a month and year this is not so trivial

def getDayOfWeekFromTime(value):
    return Weekday[makeTupleFromTime[6]]

def makeTimeTuple(timeString, format = "%m/%d/%Y %H:%M:%S"):
    return time.strptime(timeString, format)

def makeTimeFromTuple(tuple):
    return time.mktime(tuple)

def makeTupleFromTime(aTime):
    return time.localtime(aTime)

def _makeMonthSecondsFromTime(aTime):
    tuple   = makeTupleFromTime(aTime)
    month   = tuple[1]
    year    = tuple[0]
    return calendar.monthrange(year, month)[1] * DAY

def makeDayDifference(aTime, bTime):
    return _makeDifference(aTime, bTime, DAY)

def makeMinuteDifference(aTime, bTime):
    return _makeDifference(aTime, bTime, MINUTE)

def makeHourDifference(aTime, bTime):
    return _makeDifference(aTime, bTime, MINUTE)

def makeWeekDifference(aTime, bTime):
    return _makeDifference(aTime, bTime, WEEK)

def makeYearDifference(aTime, bTime):
    aYears = makeTupleFromTime(aTime)[0]
    bYears = makeTupleFromTime(bTime)[0]
    return aYears - bYears

def makeMonthDifference(aTime, bTime):
    aMonth = makeTupleFromTime(aTime)[1]
    bMonth = makeTupleFromTime(bTime)[1]
    yearMonths = makeYearDifference(aTime, bTime) * 12
    return yearMonths + (aMonth - bMonth)

def _makeDifference(aTime, bTime, scale):
    return int(aTime - bTime) / scale

def makeScaleListFromTimelist(list):
    """constructs a list of scale points for the plot from the list of times"""
    list.sort()
    pivot = list[0]
    scales = [l - pivot for l in list[1:]]
    erg = [0]
    erg.extend(scales)
    return erg

def _normalizeScales(list, unit):
    return [int(item / unit) for item in list]

def normalizeToMinutes(list):
    return _normalizeScales(list, MINUTE)

def normalizeToHours(list):
    return _normalizeScales(list, HOUR)

def normalizeToDays(list):
    return _normalizeScales(list, DAY)

def normalizeToWeeks(list):
    return _normalizeScales(list, WEEK)

def makePlotGraph(scaleList, values):
    erg = []
    if not len(scaleList) == len(values):
        raise Exception("Unequal list lenght in makePlotGraph")
    for i in range(0,len(values)):
        erg.append((scaleList[i], values[i]))
    return erg


class Plot(gtk.DrawingArea):


    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.connect('expose_event', self.expose)
        self.plot_rect = (0, 0, 0, 0)  # n-s-e-w

        # background color of the graph area
        self.bgcolor   = (1, 1, 1)

        # list of graphs to plot. A graph is a list of tuples (x,y)
        self._graphs   = []

        # list of discrete points to draw on each scale
        self._x_scale  = xrange(11)
        self._y_scale  = xrange(11)

        # Strings representing the axis units
        self._x_unit   = "x unit"
        self._y_unit   = "y unit"

        # Switch whether to draw the area beneath the graph
        self.fill_plot = True

        self.colors    = [( 0,  0, .7, .8),
                          ( 0, .7,  0, .8),
                          ( 0, .7, .7, .8),
                          ( 0,  0,  0, .8),
                          ( 0,  0, .7, .8),
                          ( 0, .7,  0, .8),
                          ( 0, .7, .7, .8),
                          (.7,  0,  0, .8),
                          (.7,  0, .7, .8),
                          (.7, .7,  0, .8),
                          (.7, .7, .7, .8),
                          (.7,  0,  0, .8),
                          (.7,  0, .7, .8),
                          (.7, .7,  0, .8),
                          (.7, .7, .7, .8),
                          (.0, .0, .0, .8)]


    def expose(self, widget, event):
        """ Called upon the expose event of the widget """
        # get our drawing context
        self.context = widget.window.cairo_create()
        # limit our drawing context to the area that needs actual redrawing
        self.context.rectangle(event.area.x,
                               event.area.y,
                               event.area.width,
                               event.area.height)
        # clip it
        self.context.clip()
        # now draw!
        self.draw(self.context)
        return False


    def refresh(self):
        if self.window:
            self.window.invalidate_rect(self.get_allocation(), False)


    def update_font(self, context):
        """adjusts the font to the context"""
        rect      = self.get_allocation()
        font_size = max(min(rect.height / 40, rect.width / 30), 10)
        context.select_font_face('Arial', cairo.FONT_SLANT_NORMAL)
        context.set_font_size(font_size)


    def update_plot_size(self, context):
        """adjust the text sizes to the context"""
        self.update_font(context)

        # Calculate the width of the longest x and y caption.

        x_text = '%s' % max(self._x_scale)
        y_text = '%s' % max(self._y_scale)

        # add the length of the unit texts
        if self._x_unit is not None:
            x_text += ' %s' % self._x_unit
        if self._y_unit is not None:
            y_text += ' %s' % self._y_unit

        # Calculate the plot dimensions.
        x_bx, x_by, x_w, x_h = context.text_extents(x_text)[0:4]
        y_bx, y_by, y_w, y_h = context.text_extents(y_text)[0:4]
        rect           = self.get_allocation()
        west           = 10 + y_w - y_bx
        east           = rect.width - (x_w - x_bx) / 2 - 4
        north          = 12
        south          = rect.height - (x_h - x_by)
        self.plot_rect = (north, south, east, west)


    def p2w(self, plot_x, plot_y):
        widget_x = plot_x + self.plot_rect[3]
        widget_y = self.plot_rect[1] - plot_y
        return (widget_x, widget_y)


    def draw_canvas(self, context):
        # Draw the canvas background.
        context.save()
        context.rectangle(self.plot_rect[3],
                          self.plot_rect[0],
                          self.plot_rect[2] - self.plot_rect[3],
                          self.plot_rect[1] - self.plot_rect[0])
        context.set_source_rgb(*self.bgcolor)
        context.fill()
        context.restore()


    def draw_axis(self, context, x1, y1, x2, y2):
        horizontal = x2 > x1

        # Draw the dash.
        context.save()
        context.set_line_width(.9)
        context.move_to(x1, y1)
        context.line_to(x2, y2)
        context.stroke()
        context.restore()

        # Draw the arrow head.
        context.save()
        head_len   = 10
        head_width = 2
        if horizontal:
            context.move_to(x2 - head_len, y2 - head_width)
            context.line_to(x2, y2)
            context.line_to(x2 - head_len, y2 + head_width)
        else:
            context.move_to(x2 - head_width, y2 + head_len)
            context.line_to(x2, y2)
            context.line_to(x2 + head_width, y2 + head_len)
        context.stroke()
        context.restore()


    def draw_scale(self, context):
        # Draw an annotated scale.
        scale_size = 3
        padding    = 3
        h          = self.plot_rect[1] - self.plot_rect[0]
        w          = self.plot_rect[2] - self.plot_rect[3]

        # X axis scale.
        context.save()
        min_x = min(self._x_scale)
        #print self._x_scale
        unit  = w / (max(self._x_scale) - min_x)
        for val in self._x_scale:
            x, y = self.p2w(unit * (val - min_x), -padding)
            context.move_to(x, y)
            x, y = self.p2w(unit * (val - min_x), padding)
            context.line_to(x, y)

            caption = '%s' % val
            if self._x_unit is not None and val == self._x_scale[-1]:
                caption = '%s %s' % (val, self._x_unit)
            x_bearing, y_bearing, width, height = context.text_extents(caption)[:4]
            x, y = self.p2w(unit * (val - min_x) - width / 2 - x_bearing,
                            -scale_size - padding + y_bearing)
            context.move_to(x, y)
            context.show_text(caption)
        context.stroke()
        context.restore()

        # Y axis scale.
        min_y = min(self._y_scale)
        unit  = h / (max(self._y_scale) - min_y)
        for val in self._y_scale:
            if val != self._y_scale[0]:
                context.save()
                context.set_dash([1, 1])
                context.set_line_width(.6)
                x, y = self.p2w(-padding, unit * (val - min_y))
                context.move_to(x, y)
                x, y = self.p2w(w, unit * (val - min_y))
                context.line_to(x, y)
                context.stroke()
                context.restore()

            caption = '%s' % val
            # Draw the caption of the unit only on the last one
            if self._y_unit is not None:
                if val == self._y_scale[-1]:
                    caption = '%s %s' % (val, self._y_unit)
                else:
                    caption = '%s' % (val)
            x_bearing, y_bearing, width, height = context.text_extents(caption)[:4]
            x, y = self.p2w(-scale_size - padding - width - x_bearing,
                            unit * (val - min_y) + height / 2 + y_bearing)
            context.move_to(x, y)
            context.show_text(caption)


    def draw_graphs(self, context):

        h      = self.plot_rect[1] - self.plot_rect[0]
        w      = self.plot_rect[2] - self.plot_rect[3]
        min_x  = min(self._x_scale)
        min_y  = min(self._y_scale)
        x_unit = w / (max(self._x_scale) - min_x)
        y_unit = h / (max(self._y_scale) - min_y)

        print "Graphs: ", self.graphs

        for n, graph in enumerate(self._graphs):

            if len(graph) == 0:
                return

            # Create the path.
            context.save()
            context.set_source_rgba(*self.colors[n % len(self.colors)])
            x, y = self.p2w(x_unit * (graph[0][0] - min_x), 0)
            context.move_to(x, y)
            for x, y in graph:
                x, y = self.p2w(x_unit * (x - min_x), y_unit * (y - min_y))
                context.line_to(x, y)
            x, y = self.p2w(x_unit * (graph[-1][0] - min_x), 0)
            context.line_to(x, y)

            # Draw it.
            path = context.copy_path()
            context.set_line_width(2)
            context.stroke()
            if self.fill_plot:
                context.append_path(path)
                context.set_source_rgba(*self.colors[n % len(self.colors)])
                context.fill()
            context.restore()


    def draw(self, context):
        # Draw the canvas background.
        self.update_plot_size(context)
        self.draw_canvas(context)

        # Draw x and y axis.
        self.draw_axis(context,
                       self.plot_rect[3] - 5,
                       self.plot_rect[1],
                       self.plot_rect[2],
                       self.plot_rect[1])
        self.draw_axis(context,
                       self.plot_rect[3],
                       self.plot_rect[1] + 5,
                       self.plot_rect[3],
                       self.plot_rect[0])

        self.draw_scale(context)
        self.draw_graphs(context)


    def get_graphs(self):
        """
        Getter for the graphs attribute.
        """
        return self._graphs


    def set_graphs(self, graphs):
        """
        Setter for the graphs attribute.

        graphs -- a list of tuples (x, y)
        """
        self._graphs = graphs
        self.refresh()


    def set_x_scale(self, scale):
        """
        Setter for the x_scale attribute.

        scale -- a list of integers
        """
        self._x_scale = scale
        self.refresh()


    def set_y_scale(self, scale):
        """
        Setter for the y_scale attribute.

        scale -- a list of integers
        """
        self._y_scale = scale
        self.refresh()


    def set_x_unit(self, unit):
        """
        Setter for the x_scale attribute.

        unit -- a string
        """
        self._x_unit = unit
        self.refresh()


    def set_y_unit(self, unit):
        """
        Setter for the y_scale attribute.

        unit -- a string
        """
        self._y_unit = unit
        self.refresh()


    graphs  = property(get_graphs, set_graphs)
    x_scale = property(None, set_x_scale)
    y_scale = property(None, set_y_scale)
    x_unit  = property(None, set_x_unit)
    y_unit  = property(None, set_y_unit)



class Graph(Plot):

    def drawPoints(self, points):
        self.graphs.append(points)

class StockGraph(Graph):

    def setScaleFromDates(self, dates, unit):
        scales = makeScaleListFromTimelist(dates)
        scales = _normalizeScales(scales, unit)
        self._x_scale = scales
        return scales

    def setValuesFromValues(self, values):
        #print values
        self._y_scale = values

    def drawTimeValues(self, tuples, unit):
        xs = [int(t[0]) for t in tuples]
        ys = [int(t[1]) for t in tuples]
        xs = self.setScaleFromDates(xs, unit)
        self.setValuesFromValues(ys)
        self.drawPoints(makePlotGraph(xs, ys))



if __name__ == "__main__":
    def button_pressed(plot, event):
        plot.graphs.append([(1, 120), (3, 120), (5, 90)])
        plot.x_unit = 'km'
        plot.y_unit = 'bpm'

    window       = gtk.Window()
    plot         = StockGraph()
    #plot.graphs  = [[(1, 120), (3, 150), (5, 80), (6, 180), (8, 100)]]
    #plot.x_scale = xrange(11)
    #plot.y_scale = xrange(0, 201, 20)

    window.add(plot)
    window.connect("destroy", gtk.main_quit)
    #plot.connect("button_press_event", button_pressed)
    plot.set_events(gtk.gdk.BUTTON_PRESS_MASK)
    window.show_all()

    aTime = makeTimeFromTuple(makeTimeTuple("10/15/2008 18:36:00"))
    bTime = makeTimeFromTuple(makeTimeTuple("11/13/2007 14:38:23"))
    cTime = makeTimeFromTuple(makeTimeTuple("10/17/2007 14:38:23"))
    timeList = [aTime, bTime, cTime]
    #scaleList = makeScaleListFromTimelist(timeList)
    #dayList = normalizeToDays(scaleList)
    #values = [1,2,3]
    #graphPlot = makePlotGraph(dayList, values)
    #plot.graphs = [graphPlot]
    #plot.x_scale = dayList
    #plot.y_scale = values
    plot.drawTimeValues([(aTime, 1), (bTime, 3), (cTime, 5)], WEEK)
    gtk.main()

"""Format String options: http://www.python.org/doc/2.5.2/lib/module-time.html"""
