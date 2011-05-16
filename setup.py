# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-


#!/usr/bin/env python

from distutils.core import setup
from distutils.command.install_data import install_data
from subprocess import call
import glob
import os

import avernus


DATA_DIR = "share/avernus"
PO_DIR = 'po'
MO_DIR = os.path.join('build', 'po')


def collect_packages():
    packages = []
    for dir, dirs, files in os.walk('avernus'):
        if '__init__.py' in files:
            package = '.'.join(dir.split(os.sep))
            packages.append(package)
    #print 'Pakages: ', packages
    return packages

def collect_images():
    fileList = []
    rootdir  = "data/images"
    for root, subFolders, files in os.walk(rootdir):
        dirList = []
        for file in files:
            if file.endswith(".png") or file.endswith(".svg"):
                dirList.append(os.path.join(root, file))
        if len(dirList)!=0:
            newroot = root.replace("data/", "")
            fileList.append((os.path.join(DATA_DIR, newroot), dirList))
    return fileList


def create_data_files():
    data_files = collect_images()
    data_files.append(('share/applications', ['avernus.desktop']))
    return data_files


for po in glob.glob(os.path.join(PO_DIR, '*.po')):
    pass
    lang = os.path.basename(po[:-3])
    mo = os.path.join(MO_DIR, lang, 'avernus.mo')
    target_dir = os.path.dirname(mo)
    if not os.path.isdir(target_dir):
        os.makedirs(target_dir)
    try:
        return_code = call(['msgfmt', '-o', mo, po])
    except OSError:
        print 'Translation not available, please install gettext'
        break
    if return_code:
        raise Warning('Error when building locales')


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
    license='GPL v3',
    author='avernus-heros',
    author_email='wsteitz@gmail.com',
    description=avernus.__description__,
    download_url='https://launchpad.net/avernus/+download',
    long_description='portfolios, watchlists, tags... avernus utilizes online data sources for updating its quotations. You can view charts and other diagrams',
    url=avernus.__url__,
    packages=collect_packages(),
    scripts=['bin/avernus'],
    data_files=create_data_files(),
    cmdclass={'install_data': InstallData},
     )
