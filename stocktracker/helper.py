#!/usr/bin/env python

_ = lambda x : x

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass
try:
    import os
    import gtk
except ImportError, e:
    print "Import error in helper:", e
    sys.exit(1)

def file_browse(dialog_action, filters, file_extension="", file_name=""):
    """This function is used to browse for a file.
    It can be either a save or open dialog depending on
    what dialog_action is.
    The path to the file will be returned if the user
    selects one, however a blank string will be returned
    if they cancel or do not select one.
    dialog_action - The open or save mode for the dialog either
    gtk.FILE_CHOOSER_ACTION_OPEN, gtk.FILE_CHOOSER_ACTION_SAVE
    @param filters - list - list of  gtk.FileFilter() objects
    that will be added to the dialog.
    @param file_extension - string - The file extension that will be
    added to the filename when saving
    @param file_name - Default name when doing a save
    @returns - File Name, or None on cancel.
    """
    if (dialog_action==gtk.FILE_CHOOSER_ACTION_OPEN):
        dialog_buttons = (gtk.STOCK_CANCEL
            , gtk.RESPONSE_CANCEL
            , gtk.STOCK_OPEN
            , gtk.RESPONSE_OK)
        dlg_title = _("Open File")
    else:
        dialog_buttons = (gtk.STOCK_CANCEL
            , gtk.RESPONSE_CANCEL
            , gtk.STOCK_SAVE
            , gtk.RESPONSE_OK)
        dlg_title = _("Save File")

    file_dialog = gtk.FileChooserDialog(title=dlg_title
        , action=dialog_action
        , buttons=dialog_buttons)
    """set the filename if we are saving"""
    if (dialog_action==gtk.FILE_CHOOSER_ACTION_SAVE):
        file_dialog.set_current_name(file_name)
    #Add filters
    for filter in filters:
        file_dialog.add_filter(filter)
    if (dialog_action==gtk.FILE_CHOOSER_ACTION_OPEN):
        """Create and add the 'all files' filter"""
        filter = gtk.FileFilter()
        filter.set_name(_("All files"))
        filter.add_pattern("*")
        file_dialog.add_filter(filter)

    """Init the return value"""
    result = None
    if file_dialog.run() == gtk.RESPONSE_OK:
        result = file_dialog.get_filename()
        if (dialog_action==gtk.FILE_CHOOSER_ACTION_SAVE):
            result, extension = os.path.splitext(result)
            result = result + "." + file_extension
    file_dialog.destroy()

    return result

def show_error_dlg(error_string):
    """This Function is used to show an error dialog when an error occurs.
    @param error_string - The error string that will be displayed on the dialog.
    """
    error_dlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR
                , message_format=error_string
                , buttons=gtk.BUTTONS_OK)
    error_dlg.run()
    error_dlg.destroy()
