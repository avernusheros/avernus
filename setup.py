#!/usr/bin/env python
# -*- coding: utf-8 -*-

###################### DO NOT TOUCH THIS (HEAD TO THE SECOND PART) ######################

try:
    import DistUtilsExtra.auto
except ImportError:
    import sys
    print >> sys.stderr, 'To build stocktracker you need https://launchpad.net/python-distutils-extra'
    sys.exit(1)

assert DistUtilsExtra.auto.__version__ >= '2.10', 'needs DistUtilsExtra.auto >= 2.10'
import os


def update_data_path(prefix, oldvalue=None):

    try:
        fin = file('stocktracker/config.py', 'r')
        fout = file(fin.name + '.new', 'w')

        for line in fin:            
            fields = line.split(' = ') # Separate variable from value
            if fields[0] == '__stocktracker_data_directory__':
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
        print ("ERROR: Can't find stocktracker/config.py")
        sys.exit(1)
    return oldvalue


def update_desktop_file(datadir):

    try:
        fin = file('stocktracker.desktop.in', 'r')
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
        print ("ERROR: Can't find stocktracker.desktop.in")
        sys.exit(1)


class InstallAndUpdateDataDirectory(DistUtilsExtra.auto.install_auto):
    def run(self):
        if self.root or self.home:
            print "WARNING: You don't use a standard --prefix installation, take care that you eventually " \
            "need to update quickly/quicklyconfig.py file to adjust __quickly_data_directory__. You can " \
            "ignore this warning if you are packaging and uses --prefix."
        previous_value = update_data_path(self.prefix + '/share/stocktracker/')
        update_desktop_file(self.prefix + '/share/stocktracker/')
        DistUtilsExtra.auto.install_auto.run(self)
        update_data_path(self.prefix, previous_value)

        
##################################################################################
###################### YOU SHOULD MODIFY ONLY WHAT IS BELOW ######################
##################################################################################


DistUtilsExtra.auto.setup(
    name='stocktracker',
    version='0.5',
    license='GPL v3',
    author='stocktracker-heros',
    author_email='xyz@gmail.com',
    description='A lightweight program to easily track your investments.',
    download_url='https://launchpad.net/stocktracker/+download',
    long_description='portfolios, watchlists, tags... stocktracker utilizes online data sources for updating its quotations. You can view charts and other diagrams',
    url='https://launchpad.net/stocktracker',
    cmdclass={'install': InstallAndUpdateDataDirectory}
    )

