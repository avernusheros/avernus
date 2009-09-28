#!/usr/bin/env python
# -*- coding:utf-8 -*-

from distutils.core import setup
from distutils.command.install_data import install_data
import os
import glob
from subprocess import call
from src import stocktracker

PO_DIR = 'locales'
MO_DIR = os.path.join('build', 'locales')

for po in glob.glob(os.path.join(PO_DIR, '*.po')):
    lang = os.path.basename(po[:-3])[7:]
    mo = os.path.join(MO_DIR, lang, 'LC_MESSAGES', 'stocktracker.mo')
    target_dir = os.path.dirname(mo)
    if not os.path.isdir(target_dir):
        os.makedirs(target_dir)
    try:
        return_code = call(['msgfmt', '-o', mo, po])
    except OSError:
        print 'Translation not available, please install gettext'
        break
    if return_code:
        raise Warning('Error building locales')

class InstallData(install_data):
    def run(self):
        self.data_files.extend(self.find_mo_files())
        install_data.run(self)
    
    def find_mo_files(self):
        data_files = []
        for mo in glob.glob(os.path.join(MO_DIR, '*', 'LC_MESSAGES', 'stocktracker.mo')):
            lang = os.path.basename(os.path.dirname(mo))
            lang = os.path.basename(
                os.path.realpath(os.path.join(os.path.dirname(mo), '..'))
            )
            dest = os.path.join('share', 'locale', lang, 'LC_MESSAGES')
            data_files.append((dest, [mo]))
        return data_files


setup(
    name=stocktracker.__name__,
    version=stocktracker.__version__,
    author=stocktracker.__authors__ ,
    author_email=stocktracker.__mail__,
    url=stocktracker.__url__,
    description=stocktracker.__description__,
    license=stocktracker.__license__,
    packages=['stocktracker'],
    package_dir={'stocktracker': 'src'},
    data_files=[#('/usr/share/pixmaps', ['stocktracker.png']),
            ('/usr/share/applications', ['stocktracker.desktop']),
    ],
    scripts=['stocktracker'],
    cmdclass={'install_data': InstallData},
)

