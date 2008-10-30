import os, sys
import yahoo



TRANSACTION_BUY = 0


CATEGORY_P      = 0
CATEGORY_W      =1
WATCHLIST     = 2
PORTFOLIO     = 3
WATCHLISTITEM = 4
PORTFOLIOITEM = 5




#the used dada provider. should be changeable in future versions   
DATA_PROVIDER = yahoo.Yahoo()

PATH = os.path.join(sys.path[0], "../")

#arrow thresholds
TRESHHOLDS = [-2.0,-0.5,0.5,2.0]

ARROWS_LARGE = { "0" : os.path.join(PATH, "share/pixmaps/south48.png"),
           "1" : os.path.join(PATH, "share/pixmaps/southeast48.png"),
           "2" : os.path.join(PATH, "share/pixmaps/east48.png"),
           "3" : os.path.join(PATH, "share/pixmaps/northeast48.png"),
           "4" : os.path.join(PATH, "share/pixmaps/north48.png"),
           }
ARROWS_SMALL = { "0" : os.path.join(PATH,"share/pixmaps/south16.png"),
           "1" : os.path.join(PATH, "share/pixmaps/southeast16.png"),
           "2" : os.path.join(PATH, "share/pixmaps/east16.png"),
           "3" : os.path.join(PATH, "share/pixmaps/northeast16.png"),
           "4" : os.path.join(PATH, "share/pixmaps/north16.png"),
           }

