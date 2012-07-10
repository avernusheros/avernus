# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#!/usr/bin/env python

from distutils.core import setup
from distutils.command.install_data import install_data
from distutils.command.build import build
from distutils.dep_util import newer
from distutils.log import warn, info, error

import subprocess
import glob
import os
import sys

import avernus


PO_DIR = 'po'
MO_DIR = os.path.join('build', 'mo')



class BuildData(build):

    def run (self):
        build.run (self)
        for po in glob.glob(os.path.join(PO_DIR, '*.po')):
            lang = os.path.basename(po[:-3])
            mo = os.path.join(MO_DIR, lang, 'avernus.mo')

            target_dir = os.path.dirname(mo)
            if not os.path.isdir(target_dir):
                info('creating %s' % target_dir)
                os.makedirs(target_dir)
            if newer(po, mo):
                info('compiling %s -> %s' % (po, mo))
                try:
                    rc = subprocess.call(['msgfmt', '-o', mo, po])
                    if rc != 0:
                        raise Warning, "msgfmt returned %d" % rc
                except Exception, e:
                    error("Building gettext files failed.")
                    error("Error: %s" % str(e))
                    sys.exit(1)


class InstallData(install_data):

    def run(self):
        self.data_files.extend(self.find_mo_files())
        install_data.run(self)

    def find_mo_files(self):
        data_files = []
        for mo in glob.glob(os.path.join(MO_DIR, '*', 'avernus.mo')):
            lang = os.path.basename(os.path.dirname(mo))
            dest = os.path.join('share', 'locale', lang, 'LC_MESSAGES')
            data_files.append((dest, [mo]))
        return data_files


setup(
    name=avernus.__appname__,
    version=avernus.__version__,
    license='GNU GPL v3',
    author='avernus-heros',
    author_email='wsteitz@gmail.com',
    description=avernus.__description__,
    download_url='https://launchpad.net/avernus/+download',
    url=avernus.__url__,
    scripts=['scripts/avernus', 'avernus.py'],
    data_files=[
      ('share/applications', ['data/avernus.desktop']),
      ('share/pixmaps', ['data/icons/hicolor/48x48/apps/avernus.png']),
      ('share/icons/hicolor/scalable/apps', glob.glob('data/icons/hicolor/scalable/apps/*.svg')),
      ('share/icons/hicolor/48x48/apps', glob.glob('data/icons/hicolor/48x48/apps/*.png')),
     ],
    packages = ['avernus',
                'avernus.cairoplot',
                'avernus.gui',
                'avernus.gui.account',
                'avernus.gui.portfolio',
                'avernus.data_sources',
                'avernus.controller',
                'avernus.objects',
                ],
    package_data={
                    'avernus.gui': ['*.glade', '*.ui'],
                    'avernus.gui.portfolio': ['*.glade', '*.ui'],
                    'avernus.gui.account': ['*.glade', '*.ui']
                    },
    cmdclass={'build': BuildData, 'install_data': InstallData},
   )
