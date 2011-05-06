#! /usr/bin/env python
# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.

HTTPSERVER_HOST = '127.0.0.1'
HTTPSERVER_PORT = 8081
HTTPSERVER_BASE_URL = 'http://{host}:{port}'.format(host=HTTPSERVER_HOST,
                                                    port=HTTPSERVER_PORT)

# Timestep for moving actions:
MOVE_TIMESTEP = 30

# Orientation of containers:
ORIENTATION_HORIZONTAL = 0
ORIENTATION_VERTICAL = 1

# Mouse buttons (compatible to GTK+):
MOUSE_BUTTON_LEFT = 1
MOUSE_BUTTON_MIDDLE = 2
MOUSE_BUTTON_RIGHT = 3

# General mode of Melange:
MODE_NORMAL = 0
MODE_EDIT = 1

# States a widget or container be in:
STATE_NONE = 0
STATE_VISIBLE = 1
STATE_HIDDEN = 2
STATE_MOVE = 3
STATE_MOVING = 4

OVERLAY_FADE_DURATION = 350
