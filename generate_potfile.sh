#!/bin/bash
POTFILE="po/avernus.pot"
rm $POTFILE
touch $POTFILE
find avernus/ -iname "*.glade" -exec intltool-extract --type=gettext/glade {} \;
find avernus/ \( -iname "*.py" -o -iname "*.glade.h" \) -exec xgettext -j --language=Python --keyword=_ --keyword=N_ --from-code utf-8 --output=$POTFILE {} \;
