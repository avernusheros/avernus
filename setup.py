#!/usr/bin/env python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-

import DistUtilsExtra.auto
import os


def update_data_path(prefix, oldvalue=None):

    try:
        fin = file('avernus/config.py', 'r')
        fout = file(fin.name + '.new', 'w')

        for line in fin:
            fields = line.split(' = ') # Separate variable from value
            if fields[0] == '__avernus_data_directory__':
                # update to prefix, store oldvalue
                if not oldvalue:
                    oldvalue = fields[1]
                    line = "%s = '%s'\n" % (fields[0], prefix)
                else: # restore oldvalue
                    line = "%s = %s" % (fields[0], oldvalue)
            fout.write(line)

        fout.flush()
        fout.close()
        fin.close()
        os.rename(fout.name, fin.name)
    except (OSError, IOError), e:
        import sys
        print ("ERROR: Can't find avernus/config.py")
        sys.exit(1)
    return oldvalue


def update_desktop_file(datadir):

    try:
        fin = file('avernus.desktop.in', 'r')
        fout = file(fin.name + '.new', 'w')

        for line in fin:
            if 'Icon=' in line:
                line = "Icon=%s\n" % (datadir + 'images/icon.png')
            fout.write(line)
        fout.flush()
        fout.close()
        fin.close()
        os.rename(fout.name, fin.name)
    except (OSError, IOError), e:
        print ("ERROR: Can't find avernus.desktop.in")
        sys.exit(1)


class InstallAndUpdateDataDirectory(DistUtilsExtra.auto.install_auto):
    def run(self):
        if self.root or self.home:
            print "WARNING: You don't use a standard --prefix installation, take care that you eventually " \
            "need to update quickly/quicklyconfig.py file to adjust __quickly_data_directory__. You can " \
            "ignore this warning if you are packaging and uses --prefix."
        previous_value = update_data_path(self.prefix + '/share/avernus/')
        update_desktop_file(self.prefix + '/share/avernus/')
        DistUtilsExtra.auto.install_auto.run(self)
        update_data_path(self.prefix, previous_value)



import avernus
DistUtilsExtra.auto.setup(
    name=avernus.__appname__,
    version=avernus.__version__,
    license='GPL v3',
    author='avernus-heros',
    author_email='xyz@gmail.com',
    description=avernus.__description__,
    download_url='https://launchpad.net/avernus/+download',
    long_description='portfolios, watchlists, tags... avernus utilizes online data sources for updating its quotations. You can view charts and other diagrams',
    url=avernus.__url__,
    cmdclass={'install': InstallAndUpdateDataDirectory}
    )
