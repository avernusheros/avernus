from avernus.cairoplot import plots


HORZ = 0
VERT = 1
NORM = 2

# Function definition

def scatter_plot(name,
                 data   = None,
                 errorx = None,
                 errory = None,
                 width  = 640,
                 height = 480,
                 background = "white light_gray",
                 border = 0,
                 axis = False,
                 dash = False,
                 discrete = False,
                 dots = False,
                 grid = False,
                 series_legend = False,
                 x_labels = None,
                 y_labels = None,
                 x_bounds = None,
                 y_bounds = None,
                 z_bounds = None,
                 x_title  = None,
                 y_title  = None,
                 series_colors = None,
                 circle_colors = None):

    """
        - Function to plot scatter data.

        - Parameters

        data - The values to be ploted might be passed in a two basic:
               list of points:       [(0,0), (0,1), (0,2)] or [(0,0,1), (0,1,4), (0,2,1)]
               lists of coordinates: [ [0,0,0] , [0,1,2] ] or [ [0,0,0] , [0,1,2] , [1,4,1] ]
               Notice that these kinds of that can be grouped in order to form more complex data
               using lists of lists or dictionaries;
        series_colors - Define color values for each of the series
        circle_colors - Define a lower and an upper bound for the circle colors for variable radius
                        (3 dimensions) series
    """

    plot = plots.ScatterPlot( name, data, errorx, errory, width, height, background, border,
                        axis, dash, discrete, dots, grid, series_legend, x_labels, y_labels,
                        x_bounds, y_bounds, z_bounds, x_title, y_title, series_colors, circle_colors )
    plot.render()
    plot.commit()

def dot_line_plot(name,
                  data,
                  width,
                  height,
                  background = "white light_gray",
                  border = 0,
                  axis = False,
                  dash = False,
                  dots = False,
                  grid = False,
                  series_legend = False,
                  x_labels = None,
                  y_labels = None,
                  x_bounds = None,
                  y_bounds = None,
                  x_title  = None,
                  y_title  = None,
                  series_colors = None):
    """
        - Function to plot graphics using dots and lines.

        dot_line_plot (name, data, width, height, background = "white light_gray", border = 0, axis = False, grid = False, x_labels = None, y_labels = None, x_bounds = None, y_bounds = None)

        - Parameters

        name - Name of the desired output file, no need to input the .svg as it will be added at runtim;
        data - The list, list of lists or dictionary holding the data to be plotted;
        width, height - Dimensions of the output image;
        background - A 3 element tuple representing the rgb color expected for the background or a new cairo linear gradient.
                     If left None, a gray to white gradient will be generated;
        border - Distance in pixels of a square border into which the graphics will be drawn;
        axis - Whether or not the axis are to be drawn;
        dash - Boolean or a list or a dictionary of booleans indicating whether or not the associated series should be drawn in dashed mode;
        dots - Whether or not dots should be drawn on each point;
        grid - Whether or not the gris is to be drawn;
        series_legend - Whether or not the legend is to be drawn;
        x_labels, y_labels - lists of strings containing the horizontal and vertical labels for the axis;
        x_bounds, y_bounds - tuples containing the lower and upper value bounds for the data to be plotted;
        x_title - Whether or not to plot a title over the x axis.
        y_title - Whether or not to plot a title over the y axis.

        - Examples of use

        data = [0, 1, 3, 8, 9, 0, 10, 10, 2, 1]
        CairoPlot.dot_line_plot('teste', data, 400, 300)

        data = { "john" : [10, 10, 10, 10, 30], "mary" : [0, 0, 3, 5, 15], "philip" : [13, 32, 11, 25, 2] }
        x_labels = ["jan/2008", "feb/2008", "mar/2008", "apr/2008", "may/2008" ]
        CairoPlot.dot_line_plot( 'test', data, 400, 300, axis = True, grid = True,
                                  series_legend = True, x_labels = x_labels )
    """
    plot = plots.DotLinePlot( name, data, width, height, background, border,
                        axis, dash, dots, grid, series_legend, x_labels, y_labels,
                        x_bounds, y_bounds, x_title, y_title, series_colors )
    plot.render()
    plot.commit()

def function_plot(name,
                  data,
                  width,
                  height,
                  background = "white light_gray",
                  border = 0,
                  axis = True,
                  dots = False,
                  discrete = False,
                  grid = False,
                  series_legend = False,
                  x_labels = None,
                  y_labels = None,
                  x_bounds = None,
                  y_bounds = None,
                  x_title  = None,
                  y_title  = None,
                  series_colors = None,
                  step = 1):

    """
        - Function to plot functions.

        function_plot(name, data, width, height, background = "white light_gray", border = 0, axis = True, grid = False, dots = False, x_labels = None, y_labels = None, x_bounds = None, y_bounds = None, step = 1, discrete = False)

        - Parameters

        name - Name of the desired output file, no need to input the .svg as it will be added at runtim;
        data - The list, list of lists or dictionary holding the data to be plotted;
        width, height - Dimensions of the output image;
        background - A 3 element tuple representing the rgb color expected for the background or a new cairo linear gradient.
                     If left None, a gray to white gradient will be generated;
        border - Distance in pixels of a square border into which the graphics will be drawn;
        axis - Whether or not the axis are to be drawn;
        grid - Whether or not the gris is to be drawn;
        dots - Whether or not dots should be shown at each point;
        x_labels, y_labels - lists of strings containing the horizontal and vertical labels for the axis;
        x_bounds, y_bounds - tuples containing the lower and upper value bounds for the data to be plotted;
        step - the horizontal distance from one point to the other. The smaller, the smoother the curve will be;
        discrete - whether or not the function should be plotted in discrete format.

        - Example of use

        data = lambda x : x**2
        CairoPlot.function_plot('function4', data, 400, 300, grid = True, x_bounds=(-10,10), step = 0.1)
    """

    plot = plots.FunctionPlot( name, data, width, height, background, border,
                         axis, discrete, dots, grid, series_legend, x_labels, y_labels,
                         x_bounds, y_bounds, x_title, y_title, series_colors, step )
    plot.render()
    plot.commit()

def pie_plot( name, data, width, height, background = "white light_gray", gradient = False, shadow = False, colors = None ):

    """
        - Function to plot pie graphics.

        pie_plot(name, data, width, height, background = "white light_gray", gradient = False, colors = None)

        - Parameters

        name - Name of the desired output file, no need to input the .svg as it will be added at runtim;
        data - The list, list of lists or dictionary holding the data to be plotted;
        width, height - Dimensions of the output image;
        background - A 3 element tuple representing the rgb color expected for the background or a new cairo linear gradient.
                     If left None, a gray to white gradient will be generated;
        gradient - Whether or not the pie color will be painted with a gradient;
        shadow - Whether or not there will be a shadow behind the pie;
        colors - List of slices colors.

        - Example of use

        teste_data = {"john" : 123, "mary" : 489, "philip" : 890 , "suzy" : 235}
        CairoPlot.pie_plot("pie_teste", teste_data, 500, 500)
    """

    plot = plots.PiePlot( name, data, width, height, background, gradient, shadow, colors )
    plot.render()
    plot.commit()

def donut_plot(name, data, width, height, background = "white light_gray", gradient = False, shadow = False, colors = None, inner_radius = -1):

    """
        - Function to plot donut graphics.

        donut_plot(name, data, width, height, background = "white light_gray", gradient = False, inner_radius = -1)

        - Parameters

        name - Name of the desired output file, no need to input the .svg as it will be added at runtim;
        data - The list, list of lists or dictionary holding the data to be plotted;
        width, height - Dimensions of the output image;
        background - A 3 element tuple representing the rgb color expected for the background or a new cairo linear gradient.
                     If left None, a gray to white gradient will be generated;
        shadow - Whether or not there will be a shadow behind the donut;
        gradient - Whether or not the donut color will be painted with a gradient;
        colors - List of slices colors;
        inner_radius - The radius of the donut's inner circle.

        - Example of use

        teste_data = {"john" : 123, "mary" : 489, "philip" : 890 , "suzy" : 235}
        CairoPlot.donut_plot("donut_teste", teste_data, 500, 500)
    """

    plot = plots.DonutPlot(name, data, width, height, background, gradient, shadow, colors, inner_radius)
    plot.render()
    plot.commit()

def gantt_chart(name, pieces, width, height, x_labels, y_labels, colors):

    """
        - Function to generate Gantt Charts.

        gantt_chart(name, pieces, width, height, x_labels, y_labels, colors):

        - Parameters

        name - Name of the desired output file, no need to input the .svg as it will be added at runtim;
        pieces - A list defining the spaces to be drawn. The user must pass, for each line, the index of its start and the index of its end. If a line must have two or more spaces, they must be passed inside a list;
        width, height - Dimensions of the output image;
        x_labels - A list of names for each of the vertical lines;
        y_labels - A list of names for each of the horizontal spaces;
        colors - List containing the colors expected for each of the horizontal spaces

        - Example of use

        pieces = [ (0.5,5.5) , [(0,4),(6,8)] , (5.5,7) , (7,8)]
        x_labels = [ 'teste01', 'teste02', 'teste03', 'teste04']
        y_labels = [ '0001', '0002', '0003', '0004', '0005', '0006', '0007', '0008', '0009', '0010' ]
        colors = [ (1.0, 0.0, 0.0), (1.0, 0.7, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0) ]
        CairoPlot.gantt_chart('gantt_teste', pieces, 600, 300, x_labels, y_labels, colors)
    """

    plot = plots.GanttChart(name, pieces, width, height, x_labels, y_labels, colors)
    plot.render()
    plot.commit()

def vertical_bar_plot(name,
                      data,
                      width,
                      height,
                      background = "white light_gray",
                      border = 0,
                      display_values = False,
                      grid = False,
                      rounded_corners = False,
                      stack = False,
                      three_dimension = False,
                      series_labels = None,
                      x_labels = None,
                      y_labels = None,
                      x_bounds = None,
                      y_bounds = None,
                      colors = None):
    #TODO: Fix docstring for vertical_bar_plot
    """
        - Function to generate vertical Bar Plot Charts.

        bar_plot(name, data, width, height, background, border, grid, rounded_corners, three_dimension,
                 x_labels, y_labels, x_bounds, y_bounds, colors):

        - Parameters

        name - Name of the desired output file, no need to input the .svg as it will be added at runtime;
        data - The list, list of lists or dictionary holding the data to be plotted;
        width, height - Dimensions of the output image;
        background - A 3 element tuple representing the rgb color expected for the background or a new cairo linear gradient.
                     If left None, a gray to white gradient will be generated;
        border - Distance in pixels of a square border into which the graphics will be drawn;
        grid - Whether or not the gris is to be drawn;
        rounded_corners - Whether or not the bars should have rounded corners;
        three_dimension - Whether or not the bars should be drawn in pseudo 3D;
        x_labels, y_labels - lists of strings containing the horizontal and vertical labels for the axis;
        x_bounds, y_bounds - tuples containing the lower and upper value bounds for the data to be plotted;
        colors - List containing the colors expected for each of the bars.

        - Example of use

        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        CairoPlot.vertical_bar_plot ('bar2', data, 400, 300, border = 20, grid = True, rounded_corners = False)
    """

    plot = plots.VerticalBarPlot(name, data, width, height, background, border,
                           display_values, grid, rounded_corners, stack, three_dimension,
                           series_labels, x_labels, y_labels, x_bounds, y_bounds, colors)
    plot.render()
    plot.commit()

def horizontal_bar_plot(name,
                       data,
                       width,
                       height,
                       background = "white light_gray",
                       border = 0,
                       display_values = False,
                       grid = False,
                       rounded_corners = False,
                       stack = False,
                       three_dimension = False,
                       series_labels = None,
                       x_labels = None,
                       y_labels = None,
                       x_bounds = None,
                       y_bounds = None,
                       colors = None):

    #TODO: Fix docstring for horizontal_bar_plot
    """
        - Function to generate Horizontal Bar Plot Charts.

        bar_plot(name, data, width, height, background, border, grid, rounded_corners, three_dimension,
                 x_labels, y_labels, x_bounds, y_bounds, colors):

        - Parameters

        name - Name of the desired output file, no need to input the .svg as it will be added at runtime;
        data - The list, list of lists or dictionary holding the data to be plotted;
        width, height - Dimensions of the output image;
        background - A 3 element tuple representing the rgb color expected for the background or a new cairo linear gradient.
                     If left None, a gray to white gradient will be generated;
        border - Distance in pixels of a square border into which the graphics will be drawn;
        grid - Whether or not the gris is to be drawn;
        rounded_corners - Whether or not the bars should have rounded corners;
        three_dimension - Whether or not the bars should be drawn in pseudo 3D;
        x_labels, y_labels - lists of strings containing the horizontal and vertical labels for the axis;
        x_bounds, y_bounds - tuples containing the lower and upper value bounds for the data to be plotted;
        colors - List containing the colors expected for each of the bars.

        - Example of use

        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        CairoPlot.bar_plot ('bar2', data, 400, 300, border = 20, grid = True, rounded_corners = False)
    """

    plot = plots.HorizontalBarPlot(name, data, width, height, background, border,
                             display_values, grid, rounded_corners, stack, three_dimension,
                             series_labels, x_labels, y_labels, x_bounds, y_bounds, colors)
    plot.render()
    plot.commit()

def stream_chart(name,
                 data,
                 width,
                 height,
                 background = "white light_gray",
                 border = 0,
                 grid = False,
                 series_legend = None,
                 x_labels = None,
                 x_bounds = None,
                 y_bounds = None,
                 colors = None):

    #TODO: Fix docstring for horizontal_bar_plot
    plot = plots.StreamChart(name, data, width, height, background, border,
                       grid, series_legend, x_labels, x_bounds, y_bounds, colors)
    plot.render()
    plot.commit()
