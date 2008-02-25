# Copyright (C) 2006-2007 Red Hat, Inc.
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

import logging

import gtk
import gobject
import hippo

from sugar.graphics import animator
from sugar.graphics import style
from sugar.graphics import palettegroup
from sugar.clipboard import clipboardservice

from view.frame.eventarea import EventArea
from view.frame.activitiestray import ActivitiesTray
from view.frame import activitiestray2
from view.frame.zoomtray import ZoomTray
from view.frame.friendstray import FriendsTray
from view.frame.devicestray import DevicesTray
from view.frame.framewindow import FrameWindow
from view.frame.clipboardpanelwindow import ClipboardPanelWindow
from model.shellmodel import ShellModel

_FRAME_HIDING_DELAY = 500

class _Animation(animator.Animation):
    def __init__(self, frame, end):
        start = frame.current_position
        animator.Animation.__init__(self, start, end)
        self._frame = frame

    def next_frame(self, current):
        self._frame.move(current)

class _MouseListener(object):
    def __init__(self, frame):
        self._frame = frame
        self._hide_sid = 0

    def mouse_enter(self):
        self._show_frame()

    def mouse_leave(self):
        if self._frame.mode == Frame.MODE_MOUSE:
            self._hide_frame()

    def _show_frame(self):
        if self._hide_sid != 0:
            gobject.source_remove(self._hide_sid)
        self._frame.show(Frame.MODE_MOUSE)

    def _hide_frame_timeout_cb(self):
        self._frame.hide()
        return False

    def _hide_frame(self):
        if self._hide_sid != 0:
            gobject.source_remove(self._hide_sid)
        self._hide_sid = gobject.timeout_add(
                  _FRAME_HIDING_DELAY, self._hide_frame_timeout_cb)

class _KeyListener(object):
    def __init__(self, frame):
        self._frame = frame

    def key_press(self):
        if self._frame.visible:
            if self._frame.mode == Frame.MODE_KEYBOARD:
                self._frame.hide()
        else:
            self._frame.show(Frame.MODE_KEYBOARD)

class Frame(object):
    MODE_MOUSE    = 0
    MODE_KEYBOARD = 1
    MODE_NON_INTERACTIVE = 2

    def __init__(self, shell):
        self.mode = None

        self._palette_group = palettegroup.get_group('frame')
        self._palette_group.connect('popdown', self._palette_group_popdown_cb)

        self._left_panel = None
        self._right_panel = None
        self._top_panel = None
        self._bottom_panel = None

        self._shell = shell
        self.current_position = 0.0
        self._animator = None

        self._event_area = EventArea()
        self._event_area.connect('enter', self._enter_corner_cb)
        self._event_area.show()

        self._top_panel = self._create_top_panel()
        self._bottom_panel = self._create_bottom_panel()
        self._left_panel = self._create_left_panel()
        self._right_panel = self._create_right_panel()

        screen = gtk.gdk.screen_get_default()
        screen.connect('size-changed', self._size_changed_cb)

        cb_service = clipboardservice.get_instance()
        cb_service.connect_after('object-added', self._clipboard_object_added_cb)

        self._key_listener = _KeyListener(self)
        self._mouse_listener = _MouseListener(self)

        self.move(1.0)

    def is_visible(self):
        return self.current_position != 0.0

    def hide(self):
        if self._animator:
            self._animator.stop()

        self._animator = animator.Animator(0.5)
        self._animator.add(_Animation(self, 0.0))
        self._animator.start()

        self._event_area.show()

        self.mode = None

    def show(self, mode):
        if self.visible:
            return
        if self._animator:
            self._animator.stop()

        self._shell.take_activity_screenshot()

        self.mode = mode

        self._animator = animator.Animator(0.5)
        self._animator.add(_Animation(self, 1.0))
        self._animator.start()

        self._event_area.hide()

    def move(self, pos):
        self.current_position = pos
        self._update_position()

    def _is_hover(self):
        return (self._top_panel.hover or \
                self._bottom_panel.hover or \
                self._left_panel.hover or \
                self._right_panel.hover)

    def _create_top_panel(self):
        panel = self._create_panel(gtk.POS_TOP)

        zoom_tray = ZoomTray(self._shell)
        panel.append(hippo.CanvasWidget(widget=zoom_tray))
        zoom_tray.show()

        activities_tray = ActivitiesTray(self._shell)
        panel.append(hippo.CanvasWidget(widget=activities_tray), hippo.PACK_EXPAND)
        activities_tray.show()

        return panel

    def _create_bottom_panel(self):
        panel = self._create_panel(gtk.POS_BOTTOM)

        """
        activities_tray = activitiestray2.ActivitiesTray(self._shell)
        panel.append(hippo.CanvasWidget(widget=activities_tray), hippo.PACK_EXPAND)
        """

        devices_tray = DevicesTray(self._shell)
        panel.append(hippo.CanvasWidget(widget=devices_tray), hippo.PACK_EXPAND)
        devices_tray.show()

        return panel

    def _create_right_panel(self):
        panel = self._create_panel(gtk.POS_RIGHT)

        tray = FriendsTray(self._shell)
        panel.append(hippo.CanvasWidget(widget=tray), hippo.PACK_EXPAND)
        tray.show()

        return panel

    def _create_left_panel(self):
        panel = ClipboardPanelWindow(self, gtk.POS_LEFT)

        self._connect_to_panel(panel)
        panel.connect('drag-motion', self._drag_motion_cb)
        panel.connect('drag-leave', self._drag_leave_cb)

        return panel

    def _create_panel(self, orientation):
        panel = FrameWindow(orientation)
        self._connect_to_panel(panel)

        return panel

    def _move_panel(self, panel, pos, x1, y1, x2, y2):
        x = (x2 - x1) * pos + x1
        y = (y2 - y1) * pos + y1

        panel.move(int(x), int(y))

        # FIXME we should hide and show as necessary to free memory
        if not panel.props.visible:
            panel.show()

    def _connect_to_panel(self, panel):
        panel.connect('enter-notify-event', self._enter_notify_cb)
        panel.connect('leave-notify-event', self._leave_notify_cb)

    def _update_position(self):
        screen_h = gtk.gdk.screen_height()
        screen_w = gtk.gdk.screen_width()

        self._move_panel(self._top_panel, self.current_position,
                         0, - self._top_panel.size, 0, 0)

        self._move_panel(self._bottom_panel, self.current_position,
                         0, screen_h, 0, screen_h - self._bottom_panel.size)

        self._move_panel(self._left_panel, self.current_position,
                         - self._left_panel.size, 0, 0, 0)

        self._move_panel(self._right_panel, self.current_position,
                         screen_w, 0, screen_w - self._right_panel.size, 0)

    def _size_changed_cb(self, screen):
       self._update_position()

    def _clipboard_object_added_cb(self, cb_service, object_id, name):
        if not self.visible:
            self.show(self.MODE_NON_INTERACTIVE)
            gobject.timeout_add(2000, lambda: self.hide())

    def _enter_notify_cb(self, window, event):
        if event.detail != gtk.gdk.NOTIFY_INFERIOR:
            self._mouse_listener.mouse_enter()

    def _leave_notify_cb(self, window, event):
        if event.detail == gtk.gdk.NOTIFY_INFERIOR:
            return

        if not self._is_hover() and not self._palette_group.is_up():
            self._mouse_listener.mouse_leave()

    def _palette_group_popdown_cb(self, group):
        if not self._is_hover():
            self._mouse_listener.mouse_leave()

    def _drag_motion_cb(self, window, context, x, y, time):
        self._mouse_listener.mouse_enter()
        
    def _drag_leave_cb(self, window, drag_context, timestamp):
        self._mouse_listener.mouse_leave()
            
    def _enter_corner_cb(self, event_area):
        self._mouse_listener.mouse_enter()
        
    def notify_key_press(self):
        self._key_listener.key_press()

    visible = property(is_visible, None)