
#!/usr/bin/env python
# -*- coding: utf-8 -*-


import elixir
from elixir import Entity, Field, String, Float, Integer, Date, \
                    UnicodeText, DateTime, OneToMany, ManyToMany, ManyToOne
from stocktracker  import pubsub, updater, config
from datetime      import datetime
import os 
 
    
TYPES = {None: 'n/a', 0:'stock', 1:'fund'}
#http://svn.python.org/projects/stackless/trunk/Tools/world/world
COUNTRIES = {
    "af": "Afghanistan",
    "al": "Albania",
    "dz": "Algeria",
    "as": "American Samoa",
    "ad": "Andorra",
    "ao": "Angola",
    "ai": "Anguilla",
    "aq": "Antarctica",
    "ag": "Antigua and Barbuda",
    "ar": "Argentina",
    "am": "Armenia",
    "aw": "Aruba",
    "au": "Australia",
    "at": "Austria",
    "az": "Azerbaijan",
    "bs": "Bahamas",
    "bh": "Bahrain",
    "bd": "Bangladesh",
    "bb": "Barbados",
    "by": "Belarus",
    "be": "Belgium",
    "bz": "Belize",
    "bj": "Benin",
    "bm": "Bermuda",
    "bt": "Bhutan",
    "bo": "Bolivia",
    "ba": "Bosnia and Herzegowina",
    "bw": "Botswana",
    "bv": "Bouvet Island",
    "br": "Brazil",
    "io": "British Indian Ocean Territory",
    "bn": "Brunei Darussalam",
    "bg": "Bulgaria",
    "bf": "Burkina Faso",
    "bi": "Burundi",
    "kh": "Cambodia",
    "cm": "Cameroon",
    "ca": "Canada",
    "cv": "Cape Verde",
    "ky": "Cayman Islands",
    "cf": "Central African Republic",
    "td": "Chad",
    "cl": "Chile",
    "cn": "China",
    "cx": "Christmas Island",
    "cc": "Cocos (Keeling) Islands",
    "co": "Colombia",
    "km": "Comoros",
    "cg": "Congo",
    "cd": "Congo, The Democratic Republic of the",
    "ck": "Cook Islands",
    "cr": "Costa Rica",
    "ci": "Cote D'Ivoire",
    "hr": "Croatia",
    "cu": "Cuba",
    "cy": "Cyprus",
    "cz": "Czech Republic",
    "dk": "Denmark",
    "dj": "Djibouti",
    "dm": "Dominica",
    "do": "Dominican Republic",
    "tp": "East Timor",
    "ec": "Ecuador",
    "eg": "Egypt",
    "sv": "El Salvador",
    "gq": "Equatorial Guinea",
    "er": "Eritrea",
    "ee": "Estonia",
    "et": "Ethiopia",
    "fk": "Falkland Islands (Malvinas)",
    "fo": "Faroe Islands",
    "fj": "Fiji",
    "fi": "Finland",
    "fr": "France",
    "gf": "French Guiana",
    "pf": "French Polynesia",
    "tf": "French Southern Territories",
    "ga": "Gabon",
    "gm": "Gambia",
    "ge": "Georgia",
    "de": "Germany",
    "gh": "Ghana",
    "gi": "Gibraltar",
    "gr": "Greece",
    "gl": "Greenland",
    "gd": "Grenada",
    "gp": "Guadeloupe",
    "gu": "Guam",
    "gt": "Guatemala",
    "gn": "Guinea",
    "gw": "Guinea-Bissau",
    "gy": "Guyana",
    "ht": "Haiti",
    "hm": "Heard Island and Mcdonald Islands",
    "va": "Holy See (Vatican City State)",
    "hn": "Honduras",
    "hk": "Hong Kong",
    "hu": "Hungary",
    "is": "Iceland",
    "in": "India",
    "id": "Indonesia",
    "ir": "Iran, Islamic Republic of",
    "iq": "Iraq",
    "ie": "Ireland",
    "il": "Israel",
    "it": "Italy",
    "jm": "Jamaica",
    "jp": "Japan",
    "jo": "Jordan",
    "kz": "Kazakstan",
    "ke": "Kenya",
    "ki": "Kiribati",
    "kp": "Korea, Democratic People's Republic of",
    "kr": "Korea, Republic of",
    "kw": "Kuwait",
    "kg": "Kyrgyzstan",
    "la": "Lao People's Democratic Republic",
    "lv": "Latvia",
    "lb": "Lebanon",
    "ls": "Lesotho",
    "lr": "Liberia",
    "ly": "Libyan Arab Jamahiriya",
    "li": "Liechtenstein",
    "lt": "Lithuania",
    "lu": "Luxembourg",
    "mo": "Macau",
    "mk": "Macedonia, The Former Yugoslav Republic of",
    "mg": "Madagascar",
    "mw": "Malawi",
    "my": "Malaysia",
    "mv": "Maldives",
    "ml": "Mali",
    "mt": "Malta",
    "mh": "Marshall Islands",
    "mq": "Martinique",
    "mr": "Mauritania",
    "mu": "Mauritius",
    "yt": "Mayotte",
    "mx": "Mexico",
    "fm": "Micronesia, Federated States of",
    "md": "Moldova, Republic of",
    "mc": "Monaco",
    "mn": "Mongolia",
    "ms": "Montserrat",
    "ma": "Morocco",
    "mz": "Mozambique",
    "mm": "Myanmar",
    "na": "Namibia",
    "nr": "Nauru",
    "np": "Nepal",
    "nl": "Netherlands",
    "an": "Netherlands Antilles",
    "nc": "New Caledonia",
    "nz": "New Zealand",
    "ni": "Nicaragua",
    "ne": "Niger",
    "ng": "Nigeria",
    "nu": "Niue",
    "nf": "Norfolk Island",
    "mp": "Northern Mariana Islands",
    "no": "Norway",
    "om": "Oman",
    "pk": "Pakistan",
    "pw": "Palau",
    "ps": "Palestinian Territory, Occupied",
    "pa": "Panama",
    "pg": "Papua New Guinea",
    "py": "Paraguay",
    "pe": "Peru",
    "ph": "Philippines",
    "pn": "Pitcairn",
    "pl": "Poland",
    "pt": "Portugal",
    "pr": "Puerto Rico",
    "qa": "Qatar",
    "re": "Reunion",
    "ro": "Romania",
    "ru": "Russian Federation",
    "rw": "Rwanda",
    "sh": "Saint Helena",
    "kn": "Saint Kitts and Nevis",
    "lc": "Saint Lucia",
    "pm": "Saint Pierre and Miquelon",
    "vc": "Saint Vincent and the Grenadines",
    "ws": "Samoa",
    "sm": "San Marino",
    "st": "Sao Tome and Principe",
    "sa": "Saudi Arabia",
    "sn": "Senegal",
    "sc": "Seychelles",
    "sl": "Sierra Leone",
    "sg": "Singapore",
    "sk": "Slovakia",
    "si": "Slovenia",
    "sb": "Solomon Islands",
    "so": "Somalia",
    "za": "South Africa",
    "gs": "South Georgia and the South Sandwich Islands",
    "es": "Spain",
    "lk": "Sri Lanka",
    "sd": "Sudan",
    "sr": "Suriname",
    "sj": "Svalbard and Jan Mayen",
    "sz": "Swaziland",
    "se": "Sweden",
    "ch": "Switzerland",
    "sy": "Syrian Arab Republic",
    "tw": "Taiwan, Province of China",
    "tj": "Tajikistan",
    "tz": "Tanzania, United Republic of",
    "th": "Thailand",
    "tg": "Togo",
    "tk": "Tokelau",
    "to": "Tonga",
    "tt": "Trinidad and Tobago",
    "tn": "Tunisia",
    "tr": "Turkey",
    "tm": "Turkmenistan",
    "tc": "Turks and Caicos Islands",
    "tv": "Tuvalu",
    "ug": "Uganda",
    "ua": "Ukraine",
    "ae": "United Arab Emirates",
    "gb": "United Kingdom",
    "us": "United States",
    "um": "United States Minor Outlying Islands",
    "uy": "Uruguay",
    "uz": "Uzbekistan",
    "vu": "Vanuatu",
    "ve": "Venezuela",
    "vn": "Viet Nam",
    "vg": "Virgin Islands, British",
    "vi": "Virgin Islands, U.S.",
    "wf": "Wallis and Futuna",
    "eh": "Western Sahara",
    "ye": "Yemen",
    "yu": "Yugoslavia",
    "zm": "Zambia",
    "zw": "Zimbabwe",
    }
 


def update_all_stocks():
    updater.update_stocks(Stock.query.all()+Index.query.all())
    for container in Portfolio.query.all() + Watchlist.query.all() \
                                        + Index.query.all():
        container.last_update = datetime.now()
    

###############################################################
#################     BASE CLASSES      #######################
###############################################################

class Position(object):
    tagstring = ''
    
    @property
    def type_string(self):
        return TYPES[self.stock.type]
    
    @property
    def days_gain(self):
        return self.stock.change * self.quantity
    
    @property
    def gain(self):
        stock = self.stock.price - self.price
        absolute = stock * self.quantity
        percent = round(absolute * 100 / (self.price*self.quantity),2)
        return absolute, percent

    @property
    def current_change(self):
        return self.stock.change, round(self.stock.percent,2)
    
    @property    
    def bvalue(self):
        return self.quantity * self.price
    
    @property
    def cvalue(self):
        return self.quantity * self.stock.price 
     
    @property
    def name(self):
        return self.stock.name    
    

class Container(object):

    tagstring = ''
    
    @property
    def bvalue(self):
        value = 0.0
        for pos in self.positions:
            value += pos.bvalue
        return value
    
    @property
    def cvalue(self):
        value = 0.0
        for pos in self.positions:
            value += pos.cvalue
        return value
    
    @property
    def overall_change(self):
        end = self.cvalue
        start = self.bvalue
        absolute = end - start
        if start == 0:
            percent = 0
        else:
            percent = round(100.0 / start * absolute,2)
        return absolute, percent 
    
    @property
    def current_change(self):
        change = 0.0
        for pos in self.positions:
            stock, percent = pos.current_change
            change +=stock * pos.quantity
        start = self.cvalue - change
        if start == 0.0:
            percent = 0
        else:
            percent = round(100.0 / start * change,2)
        return change, percent 
     
    def update_positions(self):
        updater.update_stocks([pos.stock for pos in self.positions])
        self.last_update = datetime.now()
        pubsub.publish("stocks.updated", self)



###############################################################
##################       Entities      ########################
###############################################################


class Exchange(Entity):
    elixir.using_options(tablename='exchange')
    name = Field(String(128))
    #stocks = OneToMany('Stock')
    

class Index(Entity, Container):
    elixir.using_options(tablename='indices')
    
    name = Field(String(128))
    positions = ManyToMany('Stock')
    isin = Field(String(16))
    price = Field(Float, default=0.0)
    change = Field(Float, default=0.0)
    date = Field(DateTime)
    exchange = ManyToOne('Exchange')
    last_update = Field(DateTime)
    yahoo_symbol = Field(String(16)) 
    
    def update_positions(self):
        #update stocks and index
        updater.update_stocks(self.positions+[self]) 
        self.last_update = datetime.now()
        pubsub.publish("stocks.updated", self)
   
    @property      
    def percent(self):
        try: 
            return round(self.change * 100 / (self.price - self.change),2)
        except:
            return 0
          
          
class Quotation(Entity):
    elixir.using_options(tablename='quotation')
    
    stock  = ManyToOne('Stock') 
    date   = Field(Date)
    open   = Field(Float)
    high   = Field(Float)
    low    = Field(Float)
    close  = Field(Float)
    vol    = Field(Integer)

         
class Stock(Entity):
    elixir.using_options(tablename='stock')
    
    isin = Field(String(16))
    exchange = ManyToOne('Exchange')
    name = Field(String(128))
    type = Field(Integer, default=0)
    currency = Field(String(8))
    yahoo_symbol = Field(String(32))        
    quotations = OneToMany('Quotation')
    price = Field(Float, default=0.0)
    date = Field(DateTime)
    change = Field(Float, default=0.0)
    
    #needed for some treeviews, e.g. news_tab
    @property
    def stock(self):
        return self
    
    @property
    def country(self):
        return COUNTRIES[self.isin[0:2].lower()]
                    
    @property      
    def percent(self):
        try: 
            return round(self.change * 100 / (self.price - self.change),2)
        except:
            return 0
    
    def update(self):
        updater.update_stocks([self])
    
    def __str__(self):
        return self.name +' | '+self.isin+' | '+self.exchange.name
    

class Watchlist(Entity, Container):
    elixir.using_options(tablename='watchlist')

    name = Field(String, primary_key=True)
    last_update = Field(DateTime)
    positions = OneToMany('WatchlistPosition')
    comment = Field(UnicodeText)
    
    def __init__(self, *args, **kwargs):
        Entity.__init__(self, *args, **kwargs)
        Container.__init__(self)
        pubsub.publish("watchlist.created",  self) 
    



class Tag(Entity, Container):
    elixir.using_options(tablename='tag')

    name = Field(String, primary_key=True)
    positions = ManyToMany('PortfolioPosition', inverse='_tags')
    
    def __init__(self, *args, **kwargs):
        Entity.__init__(self, *args, **kwargs)
        pubsub.publish("tag.created",  self) 
    

class Portfolio(Entity, Container):
    elixir.using_options(tablename='portfolio')

    name = Field(String, primary_key=True)
    last_update = Field(DateTime)
    comment = Field(UnicodeText)
    cash = Field(Float, default=0)
    positions = OneToMany('PortfolioPosition')
    transactions = OneToMany('PortfolioTransaction')
    
    def __init__(self, *args, **kwargs):
        Entity.__init__(self, *args, **kwargs)
        pubsub.publish("portfolio.created",  self) 
    
    

class PortfolioPosition(Entity, Position):
    elixir.using_options(tablename='portfolio_position')

    comment = Field(UnicodeText)
    stock = ManyToOne('Stock') 
    portfolio = ManyToOne('Portfolio')
    quantity = Field(Float)
    price = Field(Float)
    date = Field(DateTime)
    transactions = OneToMany('Transaction')
    _tags = ManyToMany('Tag')
    dividends = OneToMany('Dividend')
     
    @property
    def tagstring(self):
        ret = ''
        for t in self._tags:
            ret += t.name + ' '
        return ret 
    
    @property
    def tags(self):
        return self._tags
      
    @tags.setter
    def tags(self, tags):
        taglist = []
        for tagstring in tags:
            #ensure tag exists
            tag = Tag.query.get(tagstring)
            if tag is None:
                tag = Tag(name = tagstring)
            taglist.append(tag)
        self._tags = taglist
    


class WatchlistPosition(Entity, Position):
    elixir.using_options(tablename='watchlist_position')

    comment = Field(UnicodeText)
    stock = ManyToOne('Stock') 
    watchlist = ManyToOne('Watchlist')
    price = Field(Float)
    date = Field(DateTime)
    
    quantity = 1
    #FIXME
    tags_string =''
        

class Transaction(Entity):
    elixir.using_options(tablename='transactions')
    
    date = Field(DateTime)
    position = ManyToOne('PortfolioPosition')
    type = Field(Integer)
    quantity = Field(Integer)
    ta_costs = Field(Float)
    price = Field(Float)
      

class PortfolioTransaction(Entity):
    elixir.using_options(tablename='portolio_transaction')
    date = Field(DateTime)
    portfolio = ManyToOne('Portfolio')
    type = Field(Integer)
    quantity = Field(Integer)
    price = Field(Float)
    ta_costs = Field(Float)

class Dividend(Entity):
    elixir.using_options(tablename='dividend')
    
    date = Field(DateTime)
    positions = ManyToOne('PortfolioPosition')
    type = Field(Integer)
    shares = Field(Integer)
    ta_costs = Field(Float)
    price = Field(Float)
    

    
    
###############################################################
#################       FUNCTIONS      ########################
###############################################################
    
def commit():
    elixir.session.commit()


def flush():
    elixir.drop_all()
    elixir.create_all()
    commit()


def connect(database):
    if os.path.isfile(database):
        new = False
    else: new = True
    elixir.metadata.bind = "sqlite:///"+database
    elixir.metadata.bind.echo = False #debug ausgabe
    elixir.setup_all()
    elixir.create_all()
    if new:
        load_stocks()


def save_as(filename):
    #FIXME
    print "not implemented"


def load_stocks():
    import csv
    folder = config.getdatapath()
    files = [p for p in os.listdir(folder) if os.path.isfile(os.path.join(folder, p))] 
    
    for f in files:    
        stocks = []
        first = True
        for row in csv.reader(open(os.path.join(folder, f), "rb")):
            if first:
                exchange = Exchange.query.filter_by(name =row[3]).first()
                if exchange is None:
                    exchange = Exchange(name=row[3])
                index = Index.query.filter_by(isin=row[2], exchange=exchange).first()
                if index is None:
                    index = Index(yahoo_symbol=row[0], name=row[1], isin=row[2], exchange=exchange)
                first = False
            else:   
                exchange = Exchange.query.filter_by(name =row[3]).first()
                if exchange is None:
                    exchange = Exchange(name=row[3])
                stock = Stock.query.filter_by(isin=row[2], exchange=exchange).first()
                if stock is None:
                    stock = Stock(yahoo_symbol=row[0], name=row[1], isin=row[2], exchange=exchange)
                stocks.append(stock)
        index.positions=stocks  
