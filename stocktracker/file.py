try:
    import cPickle
    import helper
    import gtk
except ImportError, e:
    print "Import error stocktracker cannot start:", e
    sys.exit(1)
    
    
_ = lambda x : x

FILE_EXT = "data"  
APP_NAME = "stocktracker"

class File:
    def __init__(self):
        #init file
        self.filename = None
    
    def get_browse_filter_list(self):
        """Used to get the list of gtk.FileFilter objects to use when browsing for a file.
        @returns - list - List of gtk.FileFilter objects
        """
        filter = gtk.FileFilter()
        filter.set_name(_("SPM file"))
        filter.add_pattern("*." + FILE_EXT)
        return [filter]

    def save_to_file(self, data):
        """Save the current watchlistproject to a filename
        @param filename - string - the file name to save the file too.
        @returns boolean - success or failure
        """
        try:
            file = open(self.filename, "w")
            cPickle.dump(data, file, cPickle.HIGHEST_PROTOCOL)
            file.close()
            return True
        except cPickle.PicklingError, e:
            helper.show_error_dlg(_("Error saving file: %s\r\n%s") % (self.filename, e))
            return False
        except:
            helper.show_error_dlg(_("Error saving file: %s" % self.filename))
            return False

    def load_from_file(self):
        """Try to load a project from a specific file.
        @param filename - string - the file name to load from
        @returns boolean - success or failure
        """
        try:
            file = open(self.filename, "rb")
            data = cPickle.load(file)
            file.close()
            return data
        except cPickle.UnpicklingError, e:
            helper.show_error_dlg(_("Error opening file: %s\r\n%s") % (self.filename, e))
            return False
        except:
            helper.show_error_dlg(_("Error opening file: %s" % self.filename))
            return False


