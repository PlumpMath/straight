# coding utf-8
"""This file is part of Straight.

Straight is free software: you can redistribute it and/or modify it under the
terms of the GNU Lesser General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

Straight is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along
with Straight. If not, see <http://www.gnu.org/licenses/>."""
from __future__ import absolute_import, division, unicode_literals

from straight import ioloop

import pycares
import pyuv


_channel = pycares.Channel(sock_state_cb=_sock_state_cb)
loop = ioloop.default
_timer = pyuv.Timer(loop)
_fd_map = {}


def _sock_state_cb(fd, readable, writable):
    if readable or writable:
        if fd not in _fd_map:
            # New socket
            handle = pyuv.Poll(self.loop, fd)
            handle.fd = fd
            _fd_map[fd] = handle
        else:
            handle = _fd_map[fd]
        if not _timer.active:
            _timer.start(_timer_cb, 1.0, 1.0)
        flags = 0
        if readable:
            flags |= pyuv.UV_READABLE
        if writable:
            flags |= pyuv.UV_WRITABLE
        handle.start(flags, _poll_cb)
    else:
        # Socket is now closed
        handle = _fd_map.pop(fd)
        handle.close()
        if not _fd_map:
            _timer.stop()


def _timer_cb(self, timer):
        _channel.process_fd(pycares.ARES_SOCKET_BAD, pycares.ARES_SOCKET_BAD)


def _poll_cb(self, handle, events, error):
    read_fd = handle.fd
    write_fd = handle.fd
    if error is not None:
        # There was an error, pretend the socket is ready
        _channel.process_fd(read_fd, write_fd)
        return
    if not events & pyuv.UV_READABLE:
        read_fd = pycares.ARES_SOCKET_BAD
    if not events & pyuv.UV_WRITABLE:
        write_fd = pycares.ARES_SOCKET_BAD
    _channel.process_fd(read_fd, write_fd)


 def _query(self, query_type, name, cb):
        _channel.query(query_type, name, cb)


def gethostbyname