import yahoo

#the used dada provider. should be changeable in future versions   
DATA_PROVIDER = yahoo.Yahoo()


#arrow thresholds
TRESHHOLDS = [-2.0,-0.5,0.5,2.0]

ARROWS = { "0" : "art/south.svg",
           "1" : "art/southeast.svg",
           "2" : "art/east.svg",
           "3" : "art/northeast.svg",
           "4" : "art/north.svg",
           }

def get_arrow_type(percent):
    type = 0
    for th in TRESHHOLDS:
        if percent > th:
            type += 1
    print type
    return ARROWS[str(type)]
