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

from straight.networking.keepalive import KeepAlive

import pyuv


class Connection(object):
    def __init__(self, hostname, port, timeout=None):
        """Connects to 'hostname' on the 'port' port. If the connection is not
        established after timeout seconds, an socket.error is raised. If no
        timeout is given, the connection will never time out. Any read or write
        calls will raise a WaitTimeout after 'timeout' seconds."""
        # TODO: add support for ipv6 and async getaddrinfo
        hosts = socket.getaddrinfo(
            hostname, port, socket.AF_INET, socket.SOCK_STREAM
        )
        family, sock_type, proto, _, address = hosts[0]

        descriptor = self.__socket = socket.socket(family, sock_type, proto)
        straight.networking.connection.BaseConnection.__init__(
            self, address, descriptor, timeout
        )
        try:
            descriptor.connect(address)
        except socket.error as e:
            # An error is always raised so wait for the 'write' event which
            # triggers when the connection is established
            if e.args[0] not in (
                errno.EINPROGRESS,
                errno.EWOULDBLOCK,
                errno.EAGAIN
            ):
                raise
            self.write()
        log.debug("Socket %d is connected to %s:%d" % (
            descriptor.fileno(), hostname, port)
        )
