#!/usr/bin/env python
# -*- coding: utf-8 -*-

# tests.py
#
# Copyright (c) 2008 Magnun Leno da Silva
#
# Author: Magnun Leno da Silva <magnun.leno@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA

import pygtk
pygtk.require('2.0')
import gtk, math, random 
from gtkcairoplot import *

def new_page(title, notebook):
    label = gtk.Label(title)
    label.show()
    
    scrolled_window = gtk.ScrolledWindow()
    scrolled_window.set_border_width(10)
    scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
    scrolled_window.show()
    #notebook.add(scrolled_window)
    notebook.append_page(scrolled_window,label)
    
    vbox = gtk.VBox(spacing=5)
    scrolled_window.add_with_viewport(vbox)
    vbox.show()
    
    return vbox
    
def run_scatter_test(notebook):
    box = new_page('ScatterPlot', notebook)
    
    # Test 1
    scatter = gtk_scatter_plot()
    data = [ (-2,10), (0,0), (0,15), (1,5), (2,0), (3,-10), (3,5) ]
    scatter.set_args({'data':data, 'width':500, 'height':500, 'grid':True, 'axis':True, 'border':20})
    #scatter1.set_property('expand', False)
    scatter.show()
    box.pack_start(scatter)
    
    # Test 2
    data = [[1,2,3,4,5],[1,1,1,1,1]]
    scatter = gtk_scatter_plot()
    scatter.set_args({'data':data, 'width':500, 'height':500, 'border':20, 'axis':True, 'grid':True})
    #scatter2.set_property('fill', False)
    scatter.show()
    box.pack_start(scatter)
    
    # Test 3
    data = [[0.5,1,2,3,4,5],[0.5,1,1,1,1,1],[10,6,10,20,10,6]]
    colors = [ (0,0,0,0.25), (1,0,0,0.75) ]
    scatter = gtk_scatter_plot()
    scatter.set_args({'data':data, 'width':500, 'height':500, 'border':20, 'axis':True, 'discrete':True,
                      'grid':True, 'circle_colors':colors})
    #scatter3.set_property('fill', False)
    scatter.show()
    box.pack_start(scatter)
    
    data = [(-1, -16, 12), (-12, 17, 11), (-4, 6, 5), (4, -20, 12), (13, -3, 21), (7, 14, 20), (-11, -2, 18), (19, 7, 18), (-10, -19, 15),
            (-17, -2, 6), (-9, 4, 10), (14, 11, 16), (13, -11, 18), (20, 20, 16), (7, -8, 15), (-16, 17, 16), (16, 9, 9), (-3, -13, 25),
            (-20, -6, 17), (-10, -10, 12), (-7, 17, 25), (10, -10, 13), (10, 13, 20), (17, 6, 15), (18, -11, 14), (18, -12, 11), (-9, 11, 14),
            (17, -15, 25), (-2, -8, 5), (5, 20, 20), (18, 20, 23), (-20, -16, 17), (-19, -2, 9), (-11, 19, 18), (17, 16, 12), (-5, -20, 15),
            (-20, -13, 10), (-3, 5, 20), (-1, 13, 17), (-11, -9, 11)]
    colors = [ (0,0,0,0.25), (1,0,0,0.75) ]
    scatter = gtk_scatter_plot()
    scatter.set_args({'data':data, 'width':500, 'height':500, 'border':20, 
                      'axis':True, 'discrete':True, 'dots':2, 'grid':True, 
                      'x_title':"x axis", 'y_title':"y axis", 'circle_colors':colors})
    #scatter4.set_property('fill', False)
    scatter.show()
    box.pack_start(scatter)
    
    #Scatter x DotLine error bars
    t = [x*0.1 for x in range(0,40)]
    f = [math.exp(x) for x in t]
    g = [10*math.cos(x) for x in t]
    h = [10*math.sin(x) for x in t]
    erx = [0.1*random.random() for x in t]
    ery = [5*random.random() for x in t]
    data = {"exp" : [t,f], "cos" : [t,g], "sin" : [t,h]}
    series_colors = [ (1,0,0), (0,0,0), (0,0,1) ]
    scatter = gtk_scatter_plot()
    scatter.set_args({'data':data, 'errorx':[erx,erx], 'errory':[ery,ery], 'width':800, 
                      'height':600, 'border':20, 'axis':True, 'discrete':False, 'dots':5, 
                      'grid':True, 'x_title':"t", 'y_title':"f(t) g(t)", 'series_legend':True, 
                      'series_colors':series_colors})
    #scatter5.set_property('fill', False)
    scatter.show()
    box.pack_start(scatter)
    
    
def run_dot_line_test(notebook):
    box = new_page('DotLine', notebook)
    
    #Default plot
    dotline = gtk_dot_line_plot()
    data = [ 0, 1, 3.5, 8.5, 9, 0, 10, 10, 2, 1 ]
    dotline.set_args({'data':data, 'width':400, 'height':300, 'border':50, 'axis':True, 'grid':True,
                       'x_title':"x axis", 'y_title':"y axis"} )
    dotline.show()
    box.pack_start(dotline)
    
    
    #Labels
    dotline = gtk_dot_line_plot()
    data = { "john" : [-5, -2, 0, 1, 3], "mary" : [0, 0, 3, 5, 2], "philip" : [-2, -3, -4, 2, 1] }
    x_labels = [ "jan/2008", "feb/2008", "mar/2008", "apr/2008", "may/2008" ]
    y_labels = [ "very low", "low", "medium", "high", "very high" ]
    dotline.set_args({'data':data, 'width':400, 'height':300, 'x_labels':x_labels,
                       'y_labels':y_labels, 'axis':True, 'grid':True,
                       'x_title':"x axis", 'y_title':"y axis", 'series_legend':True})
    dotline.show()
    box.pack_start(dotline)
    
    
    #Series legend
    dotline = gtk_dot_line_plot()
    data = { "john" : [10, 10, 10, 10, 30], "mary" : [0, 0, 3, 5, 15], "philip" : [13, 32, 11, 25, 2] }
    x_labels = [ "jan/2008", "feb/2008", "mar/2008", "apr/2008", "may/2008" ]
    dotline.set_args({'data':data, 'width':400, 'height':300, 'x_labels':x_labels, 
                       'axis':True, 'grid':True, 'series_legend':True})
    dotline.show()
    box.pack_start(dotline)

def run_function_test(notebook):
    box = new_page('Functions', notebook)
    
    #Default Plot
    function = gtk_function_plot()
    data = lambda x : x**2
    function.set_args({'data':data, 'width':400, 'height':300, 'grid':True, 'x_bounds':(-10,10), 'step':0.1})
    function.show()
    box.pack_start(function)
    
    #Discrete Plot
    function = gtk_function_plot()
    data = lambda x : math.sin(0.1*x)*math.cos(x)
    function.set_args({'data':data, 'width':800, 'height':300, 'discrete':True, 
                       'dots':True, 'grid':True, 'x_bounds':(0,80), 'x_title':"t (s)", 'y_title':"sin(0.1*x)*cos(x)"})
    function.show()
    box.pack_start(function)

    #Labels test
    function = gtk_function_plot()
    data = lambda x : [1,2,3,4,5][x]
    x_labels = [ "4", "3", "2", "1", "0" ]
    function.set_args({'data':data, 'width':400, 'height':300, 'discrete':True, 'dots':True, 'grid':True, 'x_labels':x_labels, 'x_bounds':(0,4), 'step':1})
    function.show()
    box.pack_start(function)
    
    #Multiple functions
    function = gtk_function_plot()
    data = [ lambda x : 1, lambda y : y**2, lambda z : -z**2 ]
    colors = [ (1.0, 0.0, 0.0 ), ( 0.0, 1.0, 0.0 ), ( 0.0, 0.0, 1.0 ) ]
    function.set_args({'data':data, 'width':400, 'height':300, 'grid':True, 'series_colors':colors, 'step':0.1})
    function.show()
    box.pack_start(function)

    #Gaussian
    a = 1
    b = 0
    c = 1.5
    gaussian = lambda x : a*math.exp(-(x-b)*(x-b)/(2*c*c))
    function = gtk_function_plot()
    function.set_args({'data':data, 'width':400, 'height':300, 'grid':True, 'x_bounds':(-10,10), 'step':0.1})
    function.show()
    box.pack_start(function)
    
    #Dict function plot
    function = gtk_function_plot()
    data = {'linear':lambda x : x*2, 'quadratic':lambda x:x**2, 'cubic':lambda x:(x**3)/2}
    function.set_args({'data':data, 'width':400, 'height':300, 'grid':True, 'x_bounds':(-5,5), 'step':0.1})
    function.show()
    box.pack_start(function)


def run_vertical_bar_test(notebook):
    box = new_page('VertBar', notebook)

    #Passing a dictionary
    vbar = gtk_vertical_bar_plot()
    data = { 'teste00' : [27], 'teste01' : [10], 'teste02' : [18], 'teste03' : [5], 'teste04' : [1], 'teste05' : [22] }
    vbar.set_args({'data':data, 'width':400, 'height':300, 'border':20, 'grid':True, 'rounded_corners':True})
    vbar.show()
    box.pack_start(vbar)
    
    #Display values
    vbar = gtk_vertical_bar_plot()
    data = { 'teste00' : [27], 'teste01' : [10], 'teste02' : [18], 'teste03' : [5], 'teste04' : [1], 'teste05' : [22] }
    vbar.set_args({ 'data':data, 'width':400, 'height':300, 'border':20, 'display_values':True, 'grid':True, 'rounded_corners':True})
    vbar.show()
    box.pack_start(vbar)

    #Using default, rounded corners and 3D visualization
    data = [ [0, 3, 11], [8, 9, 21], [13, 10, 9], [2, 30, 8] ]
    colors = [ (1,0.2,0), (1,0.7,0), (1,1,0) ]
    series_labels = ["red", "orange", "yellow"]
    vbar = gtk_vertical_bar_plot()
    vbar.set_args({ 'data':data, 'width':400, 'height':300, 'border':20, 'grid':True, 'rounded_corners':False, 'colors':"yellow_orange_red"})
    vbar.show()
    box.pack_start(vbar)
    
    vbar = gtk_vertical_bar_plot()
    vbar.set_args({ 'data':data, 'width':400, 'height':300, 'border':20, 'series_labels':series_labels, 'display_values':True, 'grid':True, 'rounded_corners':True, 'colors':colors})
    vbar.show()
    box.pack_start(vbar)
    
    vbar = gtk_vertical_bar_plot()
    vbar.set_args({ 'data':data, 'width':400, 'height':300, 'border':20, 'series_labels':series_labels, 'grid':True, 'three_dimension':True, 'colors':colors})
    vbar.show()
    box.pack_start(vbar)

    #Mixing groups and columns
    data = [ [1], [2], [3,4], [4], [5], [6], [7], [8], [9], [10] ]
    vbar = gtk_vertical_bar_plot()
    vbar.set_args({ 'data':data, 'width':400, 'height':300, 'border':20, 'grid':True})
    vbar.show()
    box.pack_start(vbar)

    #Using no labels, horizontal and vertical labels
    data = [[3,4], [4,8], [5,3], [9,1]]
    y_labels = [ "line1", "line2", "line3", "line4", "line5", "line6" ]
    x_labels = [ "group1", "group2", "group3", "group4" ]
    vbar = gtk_vertical_bar_plot()
    vbar.set_args({ 'data':data, 'width':600, 'height':200, 'border':20, 'grid':True})
    
    vbar = gtk_vertical_bar_plot()
    vbar.set_args({ 'data':data, 'width':600, 'height':200, 'border':20, 'grid':True, 'x_labels':x_labels})
    vbar.show()
    box.pack_start(vbar)
    
    vbar = gtk_vertical_bar_plot()
    vbar.set_args({ 'data':data, 'width':600, 'height':200, 'border':20, 'grid':True, 'y_labels':y_labels})
    vbar.show()
    box.pack_start(vbar)
    
    vbar = gtk_vertical_bar_plot()
    vbar.set_args({ 'data':data, 'width':600, 'height':200, 'border':20, 'display_values':True, 'grid':True, 'x_labels':x_labels, 'y_labels':y_labels})
    vbar.show()
    box.pack_start(vbar)
    
    #Large data set
    data = [[10*random.random()] for x in range(50)]
    x_labels = ["large label name oh my god it's big" for x in data]
    vbar = gtk_vertical_bar_plot()
    vbar.set_args({ 'data':data, 'width':1000, 'height':800, 'border':20, 'grid':True, 'rounded_corners':True, 'x_labels':x_labels})
    vbar.show()
    box.pack_start(vbar)
    
    #Stack vertical
    data = [ [6, 4, 10], [8, 9, 3], [1, 10, 9], [2, 7, 11] ]
    colors = [ (1,0.2,0), (1,0.7,0), (1,1,0) ]
    x_labels = ["teste1", "teste2", "testegrande3", "testegrande4"]
    vbar = gtk_vertical_bar_plot()
    vbar.set_args({ 'data':data, 'width':400, 'height':300, 'border':20, 'display_values':True, 'grid':True, 
                    'rounded_corners':True, 'stack':True, 'x_labels':x_labels, 'colors':colors})
    vbar.show()
    box.pack_start(vbar)
    

def run_horizontal_bar_test(notebook):
    box = new_page('HorzBar', notebook)

    #Passing a dictionary
    hbar = gtk_horizontal_bar_plot()
    data = { 'teste00' : [27], 'teste01' : [10], 'teste02' : [18], 'teste03' : [5], 'teste04' : [1], 'teste05' : [22] }
    hbar.set_args({'data':data, 'width':400, 'height':300, 'border':20, 'display_values':True, 'grid':True, 'rounded_corners':True})
    hbar.show()
    box.pack_start(hbar)
    
    #Using default, rounded corners and 3D visualization
    data = [ [0, 3, 11], [8, 9, 21], [13, 10, 9], [2, 30, 8] ]
    colors = [ (1,0.2,0), (1,0.7,0), (1,1,0) ]
    series_labels = ["red", "orange", "yellow"]
    hbar = gtk_horizontal_bar_plot()
    hbar.set_args({'data':data, 'width':400, 'height':300, 'border':20, 'grid':True, 'rounded_corners':False, 'colors':"yellow_orange_red"})
    hbar.show()
    box.pack_start(hbar)
    
    hbar = gtk_horizontal_bar_plot()
    hbar.set_args({'data':data, 'width':400, 'height':300, 'border':20, 'series_labels':series_labels, 'display_values':True, 'grid':True, 'rounded_corners':True, 'colors':colors})
    hbar.show()
    box.pack_start(hbar)

    #Mixing groups and columns
    data = [ [1], [2], [3,4], [4], [5], [6], [7], [8], [9], [10] ]
    hbar = gtk_horizontal_bar_plot()
    hbar.set_args({'data':data, 'width':400, 'height':300, 'border':20, 'grid':True})
    hbar.show()
    box.pack_start(hbar)

    #Using no labels, horizontal and vertical labels
    series_labels = ["data11", "data22"]
    data = [[3,4], [4,8], [5,3], [9,1]]
    x_labels = [ "line1", "line2", "line3", "line4", "line5", "line6" ]
    y_labels = [ "group1", "group2", "group3", "group4" ]
    hbar = gtk_horizontal_bar_plot()
    hbar.set_args({'data':data, 'width':600, 'height':200, 'border':20, 'series_labels':series_labels, 'grid':True})
    hbar.show()
    box.pack_start(hbar)
    
    hbar = gtk_horizontal_bar_plot()
    hbar.set_args({'data':data, 'width':600, 'height':200, 'border':20, 'series_labels':series_labels, 'grid':True, 'x_labels':x_labels})
    hbar.show()
    box.pack_start(hbar)
    
    hbar = gtk_horizontal_bar_plot()
    hbar.set_args({'data':data, 'width':600, 'height':200, 'border':20, 'series_labels':series_labels, 'grid':True, 'y_labels':y_labels})
    hbar.show()
    box.pack_start(hbar)
    
    hbar = gtk_horizontal_bar_plot()
    hbar.set_args({'data':data, 'width':600, 'height':200, 'border':20, 'series_labels':series_labels, 'display_values':True, 'grid':True, 'x_labels':x_labels, 'y_labels':y_labels})
    hbar.show()
    box.pack_start(hbar)
    
    #Large data set
    data = [[10*random.random()] for x in range(25)]
    x_labels = ["large label name oh my god it's big" for x in data]
    hbar = gtk_horizontal_bar_plot()
    hbar.set_args({'data':data, 'width':1000, 'height':800, 'border':20, 'grid':True, 'rounded_corners':True, 'x_labels':x_labels})
    hbar.show()
    box.pack_start(hbar)
    
    #Stack horizontal
    data = [ [6, 4, 10], [8, 9, 3], [1, 10, 9], [2, 7, 11] ]
    colors = [ (1,0.2,0), (1,0.7,0), (1,1,0) ]
    y_labels = ["teste1", "teste2", "testegrande3", "testegrande4"]
    hbar = gtk_horizontal_bar_plot()
    hbar.set_args({'data':data, 'width':400, 'height':300, 'border':20, 'display_values':True, 'grid':True, 
                   'rounded_corners':True, 'stack':True, 'y_labels':y_labels, 'colors':colors})
    hbar.show()
    box.pack_start(hbar)

def run_pie_test(notebook):
    box = new_page('PiePlot', notebook)

    #Define a new backgrond
    background = cairo.LinearGradient(300, 0, 300, 400)
    background.add_color_stop_rgb(0.0,0.7,0.0,0.0)
    background.add_color_stop_rgb(1.0,0.3,0.0,0.0)

    #Plot data
    pie = gtk_pie_plot()
    data = {"orcs" : 100, "goblins" : 230, "elves" : 50 , "demons" : 43, "humans" : 332}
    pie.set_args({'data':data, 'width':600, 'height':400})
    pie.show()
    box.pack_start(pie)
    
    pie = gtk_pie_plot()
    pie.set_args({'data':data, 'width':600, 'height':400, 'gradient':True, 'shadow':True})
    pie.show()
    box.pack_start(pie)
    
    pie = gtk_pie_plot()
    pie.set_args({'data':data, 'width':600, 'height':400, 'background':background, 'gradient':True, 'shadow':True})
    pie.show()
    box.pack_start(pie)

def run_donut_test(notebook):
    box = new_page('DonutPlot', notebook)

    #Define a new backgrond
    background = cairo.LinearGradient(300, 0, 300, 400)
    background.add_color_stop_rgb(0,0.4,0.4,0.4)
    background.add_color_stop_rgb(1.0,0.1,0.1,0.1)
    
    donut = gtk_donut_plot()
    data = {"john" : 700, "mary" : 100, "philip" : 100 , "suzy" : 50, "yman" : 50}
    #Default plot, gradient and shadow, different background
    donut.set_args({'data':data, 'width':600, 'height':400, 'inner_radius':0.3})
    donut.show()
    box.pack_start(donut)  
    
    donut = gtk_donut_plot()
    donut.set_args({'data':data, 'width':600, 'height':400, 'gradient':True, 'shadow':True, 'inner_radius':0.3})
    donut.show()
    box.pack_start(donut)  
    
    donut = gtk_donut_plot()
    donut.set_args({'data':data, 'width':600, 'height':400, 'background':background, 'gradient':True, 'shadow':True, 'inner_radius':0.3})
    donut.show()
    box.pack_start(donut)  

def run_gantt_chart_test(notebook):
    box = new_page('GanttChart', notebook)

    #Default Plot
    gantt = gtk_gantt_chart()
    pieces = [(0.5, 5.5), [(0, 4), (6, 8)], (5.5, 7), (7, 9)]
    x_labels = [ 'teste01', 'teste02', 'teste03', 'teste04']
    y_labels = [ '0001', '0002', '0003', '0004', '0005', '0006', '0007', '0008', '0009', '0010' ]
    colors = [ (1.0, 0.0, 0.0), (1.0, 0.7, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0) ]
    gantt.set_args({'pieces':pieces, 'width':500, 'height':350, 'x_labels':x_labels, 'y_labels':y_labels, 'colors':colors})
    gantt.show()
    box.pack_start(gantt)


def run_themes_test(notebook):
    box = new_page('Themes', notebook)

    theme = gtk_vertical_bar_plot()
    data = [[1,2,3,4,5,6,7,8,9,10,11,12,13,14]]
    theme.set_args({'data':data, 'width':400, 'height':300, 'border':20, 'grid':True, 'colors':"rainbow"})
    theme.show()
    box.pack_start(theme)
    
    
    theme = gtk_vertical_bar_plot()
    data = [[1,2,3,4,5,6,7,8,9,10,11,12,13,14]]
    theme.set_args({'data':data, 'width':400, 'height':300, 'background':"white light_gray", 'border':20, 'grid':True, 'colors':"rainbow"})
    theme.show()
    box.pack_start(theme)
    
    theme = gtk_function_plot()
    data = [ lambda x : 1, lambda y : y**2, lambda z : -z**2 ]
    theme.set_args({'data':data, 'width':400, 'height':300, 'grid':True, 'series_colors':["red", "orange", "yellow"], 'step':0.1})
    theme.show()
    box.pack_start(theme)
    
    #Scatter x DotLine
    t = [x*0.1 for x in range(0,40)]
    f = [math.exp(x) for x in t]
    g = [10*math.cos(x) for x in t]
    h = [10*math.sin(x) for x in t]
    erx = [0.1*random.random() for x in t]
    ery = [5*random.random() for x in t]
    data = {"exp" : [t,f], "cos" : [t,g], "sin" : [t,h]}
    series_colors = [ (1,0,0), (0,0,0) ]
    theme = gtk_scatter_plot()
    theme.set_args({'data':data, 'errorx':[erx,erx], 'errory':[ery,ery], 'width':800, 'height':600, 'border':20, 
                    'axis':True, 'discrete':False, 'dots':5, 'grid':True, 
                    'x_title':"t", 'y_title':"f(t) g(t)", 'series_legend':True, 'series_colors':["red", "blue", "orange"]})
    theme.show()
    box.pack_start(theme)

def run():
    window = gtk.Window()
    window.set_default_size(800,600)
    window.connect("delete-event", gtk.main_quit)
    window.set_title("CairoPlot Examples")
    
    notebook = gtk.Notebook()
    notebook.set_scrollable(True)
    window.add(notebook)
    notebook.show()
    
    
    #### Tests ####
    # Line plotting
    run_scatter_test(notebook)
    run_dot_line_test(notebook)
    run_function_test(notebook)
        
    # Bar plotting
    run_vertical_bar_test(notebook)
    run_horizontal_bar_test(notebook)
        
    # Pie plotting
    run_pie_test(notebook)
    run_donut_test(notebook)
        
    # Others
    run_gantt_chart_test(notebook)
    run_themes_test(notebook)
    #### End of tests ####
    
    window.present()
    gtk.main()

if __name__ == '__main__':
    run()
