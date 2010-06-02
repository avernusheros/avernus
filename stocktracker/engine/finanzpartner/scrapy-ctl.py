#!/usr/bin/env python

import os
os.environ.setdefault('SCRAPY_SETTINGS_MODULE', 'stocktracker.engine.finanzpartner.finanzpartner.settings')

from scrapy.command.cmdline import execute
execute()
