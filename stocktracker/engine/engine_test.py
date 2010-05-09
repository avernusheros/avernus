#!/usr/bin/env python
#First, import os and set the settings module relative to the root dir of the project.
#It is important that this is done before importing execute
import os
os.environ.setdefault('SCRAPY_SETTINGS_MODULE', 'finanzpartner.settings')
#make the project root known. This has to be adjusted according from where this is called.
import sys
sys.path.append("finanzpartner")
#import the execute function and invoke it with the appropriate commands
from scrapy.command.cmdline import execute
execute(['start.py','crawl','finanzpartner.de'])
