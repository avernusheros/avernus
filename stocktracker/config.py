import os, sys
from stocktracker import yahoo



TRANSACTION_BUY = 0


CATEGORY_P      = 0
CATEGORY_W      =1
WATCHLIST     = 2
PORTFOLIO     = 3
WATCHLISTITEM = 4
PORTFOLIOITEM = 5




#the used dada provider. should be changeable in future versions
DATA_PROVIDER = yahoo.Yahoo()

#arrow thresholds
TRESHHOLDS = [-2.0,-0.5,0.5,2.0]

ARROWS_LARGE = { "0" : "share/pixmaps/south48.png",
           "1" : "share/pixmaps/southeast48.png",
           "2" : "share/pixmaps/east48.png",
           "3" : "share/pixmaps/northeast48.png",
           "4" : "share/pixmaps/north48.png",
           }
ARROWS_SMALL = { "0" : "share/pixmaps/south16.png",
           "1" : "share/pixmaps/southeast16.png",
           "2" : "share/pixmaps/east16.png",
           "3" : "share/pixmaps/northeast16.png",
           "4" : "share/pixmaps/north16.png",
           }


### DATE related stuff ###

Weekday = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
  'Friday', 'Saturday', 'Sunday']

"""Second values"""
MINUTE  = 60
HOUR    = 3600
DAY     = 86400
WEEK    = 604800
# for a month and year this is not so trivial
