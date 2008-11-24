#!/usr/bin/python

'''This script parses commandline options for stocktracker and hands 
them off to the apropriate application object.
'''

import sys
from getopt import gnu_getopt, GetoptError

try:
    version_info = sys.version_info
    assert version_info >= (2, 5)
except:
    print >> sys.stderror, 'stocktracker needs python >= 2.5'
    sys.exit(1)

# Used in error messages and is passed on the the app as
# the command to call to spawn a new instance.
executable = 'stocktracker'

# All commandline options in various groups
longopts = ('verbose', 'debug')
cmdopts = ('help', 'version', 'gui')
guiopts = ()
shortopts = {
    'v': 'version', 'h': 'help',
    'V': 'verbose', 'D': 'debug',
}

# Inline help 
usagehelp = '''\
usage: stocktracker
'''
optionhelp = '''\
General Options:
  --gui       run the gui (this is the default)
  --verbose   print information to terminal
  --debug     print debug messages
  --version   print version and exit
  --help      print this text

Go to 'www.stocktracker.launchpad.net' for more help.
'''


class UsageError(Exception):
    pass

def main(argv):
    '''
    Run the main program.
    '''
    # Let getopt parse the option list
    short = ''.join(shortopts.keys())
    long = list(longopts)
    long.extend(cmdopts)

    opts, args = gnu_getopt(argv[1:], short, long)

    # First figure out which command to execute
    try:
        cmd = opts[0][0].lstrip('-')
        if cmd in shortopts:
            cmd = shortopts[cmd]
        assert cmd in cmdopts
        opts.pop(0)
    except:
        cmd = 'gui' # default command

    # If it is a simple command execute it and return
    if cmd == 'version':
        import stocktracker
        print 'stocktracker %s\n' % stocktracker.__version__
        print stocktracker.__copyright__, '\n'
        print stocktracker.__license__
        return
    elif cmd == 'help':
        print usagehelp.replace('stocktracker', executable)
        print optionhelp
        return

    # Now figure out which options are allowed for this command
    allowedopts = list(longopts)
    if cmd == 'gui':
        allowedopts.extend(guiopts)
    
    # Convert options into a proper dict
    optsdict = {'executable': executable}
    for o, a in opts:
        o = o.lstrip('-')
        if o in shortopts:
            o = shortopts[o]

        if o+'=' in allowedopts:
            optsdict[o] = a
        elif o in allowedopts:
            optsdict[o] = True
        else:
            raise GetoptError, ("--%s no allowed in combination with --%s" % (o, cmd), o)

    # Now we can start the application
    if cmd == 'gui':
        import stocktracker
        app = stocktracker.stocktracker(**optsdict)
        app.start()
    else:
        pass


if __name__  == '__main__':
    executable = sys.argv[0]
    try:
        main(sys.argv)
    except GetoptError, err:
        print >>sys.stderr, executable+':', err
        sys.exit(1)
    except UsageError, err:
        print >>sys.stderr, usagehelp.replace('stocktracker', executable)
        sys.exit(1)
    else:
        sys.exit(0)
