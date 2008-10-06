import yahoo

#the used dada provider. should be changeable in future versions   
DATA_PROVIDER = yahoo.Yahoo()


#arrow thresholds
TRESHHOLDS = [-2.0,-0.5,0.5,2.0]

ARROWS_LARGE = { "0" : "art/south48.png",
           "1" : "art/southeast48.png",
           "2" : "art/east48.png",
           "3" : "art/northeast48.png",
           "4" : "art/north48.png",
           }
ARROWS_SMALL = { "0" : "art/south16.png",
           "1" : "art/southeast16.png",
           "2" : "art/east16.png",
           "3" : "art/northeast16.png",
           "4" : "art/north16.png",
           }

def get_arrow_type(percent, large = False):
    type = 0
    for th in TRESHHOLDS:
        if percent > th:
            type += 1
    if large:
        return ARROWS_LARGE[str(type)]
    else:
        return ARROWS_SMALL[str(type)]
