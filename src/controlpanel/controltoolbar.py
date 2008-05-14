# Copyright (C) 2007, 2008 One Laptop Per Child
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import gtk
import gettext
import gobject

_ = lambda msg: gettext.dgettext('sugar', msg)

from sugar.graphics.icon import Icon
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics import iconentry
from sugar.graphics import style

class MainToolbar(gtk.Toolbar):
    """ Main
    """
    __gtype_name__ = 'MainToolbar'

    __gsignals__ = {
        'stop-clicked': (gobject.SIGNAL_RUN_FIRST,
                            gobject.TYPE_NONE,
                            ([])),
        'search-changed': (gobject.SIGNAL_RUN_FIRST,
                          gobject.TYPE_NONE,
                          ([str]))
    }
    def __init__(self):
        gtk.Toolbar.__init__(self)

        self._add_separator()

        tool_item = gtk.ToolItem()
        self.insert(tool_item, -1)
        tool_item.show()
        self._search_entry = iconentry.IconEntry()
        self._search_entry.set_icon_from_name(iconentry.ICON_ENTRY_PRIMARY,
                                              'system-search')
        self._search_entry.add_clear_button()
        self._search_entry.set_width_chars(25)
        self._search_entry.connect('changed', self.__search_entry_changed_cb)
        tool_item.add(self._search_entry)
        self._search_entry.show()

        self._add_separator(True)

        self.stop = ToolButton(icon_name='dialog-cancel')
        self.stop.set_tooltip(_('Done'))
        self.stop.connect('clicked', self.__stop_clicked_cb)
        self.stop.show()
        self.insert(self.stop, -1)
        self.stop.show()

    def get_entry(self):
        return self._search_entry
       
    def _add_separator(self, expand=False):
        separator = gtk.SeparatorToolItem()
        separator.props.draw = False
        if expand:
            separator.set_expand(True)
        else:
            separator.set_size_request(style.DEFAULT_SPACING, -1)
        self.insert(separator, -1)
        separator.show()

    def __search_entry_changed_cb(self, search_entry):
        self.emit('search-changed', search_entry.props.text)

    def __stop_clicked_cb(self, button):
        self.emit('stop-clicked')

class DetailToolbar(gtk.Toolbar):
    """ Detail
    """
    __gtype_name__ = 'DetailToolbar'

    __gsignals__ = {
        'cancel-clicked': (gobject.SIGNAL_RUN_FIRST,
                            gobject.TYPE_NONE,
                            ([])),
        'accept-clicked': (gobject.SIGNAL_RUN_FIRST,
                            gobject.TYPE_NONE,
                            ([]))
    }
    def __init__(self):
        gtk.Toolbar.__init__(self)

        self._add_separator()

        self._icon = Icon()
        self._add_widget(self._icon)
        
        self._add_separator()

        self._title = gtk.Label()
        self._add_widget(self._title)
        
        self._add_separator(True)

        cancel_button = ToolButton('dialog-cancel')
        cancel_button.set_tooltip(_('Cancel'))
        cancel_button.connect('clicked', self.__cancel_button_clicked_cb)
        self.insert(cancel_button, -1)
        cancel_button.show()

        self.accept_button = ToolButton('dialog-ok')
        self.accept_button.set_tooltip(_('Ok'))
        self.accept_button.connect('clicked', self.__accept_button_clicked_cb)
        self.insert(self.accept_button, -1)
        self.accept_button.show()

    def get_icon(self):
        return self._icon

    def get_title(self):
        return self._title

    def _add_separator(self, expand=False):
        separator = gtk.SeparatorToolItem()
        separator.props.draw = False
        if expand:
            separator.set_expand(True)
        else:
            separator.set_size_request(style.DEFAULT_SPACING, -1)
        self.insert(separator, -1)
        separator.show()

    def _add_widget(self, widget, expand=False):
        tool_item = gtk.ToolItem()
        tool_item.set_expand(expand)

        tool_item.add(widget)
        widget.show()

        self.insert(tool_item, -1)
        tool_item.show()

    def __cancel_button_clicked_cb(self, widget, data=None):
        self.emit('cancel-clicked')

    def __accept_button_clicked_cb(self, widget, data=None):
        self.emit('accept-clicked')
