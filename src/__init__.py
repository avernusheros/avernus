#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/stocktracker
#    __init__.py: Copyright 2009 Wolfgang Steitz <wsteitz(at)gmail.com>
#
#    This file is part of stocktracker.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
# -*- coding:utf-8 -*-
# Bunch of meta data, used at least in the about dialog


""" translation setup """


import locale
locale.setlocale(locale.LC_ALL, '')

import gettext
import gtk

import os
from os.path import pardir, abspath, dirname, join


__name__ = 'stocktracker'



GETTEXT_DOMAIN = 'stocktracker'
LOCALE_PATH = abspath(join(dirname(__file__), pardir, 'locales'))
if not os.path.isdir(LOCALE_PATH):
    LOCALE_PATH = '/usr/share/locale'

# setup translation
languages_used = []

lc, encoding = locale.getdefaultlocale()
if lc:
    languages_used = [lc]
lang_in_env = os.environ.get('LANGUAGE', None)
if lang_in_env:
    languages_used.extend(lang_in_env.split())

gettext.bindtextdomain(GETTEXT_DOMAIN, LOCALE_PATH)
gettext.textdomain(GETTEXT_DOMAIN)

translation = gettext.translation(GETTEXT_DOMAIN, LOCALE_PATH,
                                  languages=languages_used,
                                  fallback=True)
import __builtin__
__builtin__._ = translation.gettext



