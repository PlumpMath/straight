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


class KeepAlive(object):
    """Can be sent instead of the 'timeout' parameter when creating 'Client' or
    'Server' instances. It will activate the TCP Keep-Alive mechanism for that
    connection (or if used on a server connection, it will setup the Keep-Alive
    for incoming client sockets. Note that the Keep-Alive mechanism can only be
    set up when creating the connection, not per operation. Additionally, a
    maximum timeout 'timeout' may be specified, that will set up a global
    operation timeout on the connection (does the same thing as sending a float
    to the 'timeout' parameter, in addition to enabling Keep-Alive frames).
    Note that exceeding the timeout raises a ConnectionTimeout (which derives
    from IOError), but missing sufficient Keep-Alive frames will raise a
    generic socket.error (which also derives from IOError).

    The Keep-Alive mechanism works like this:
    If no data is received on the connection for 'interval' seconds, it will
    send a Keep-Alive frame (similar to a 'ping'). The remote end will then
    reply with a Keep-Alive response (similar to a 'pong'). If a frame has been
    sent but no reply received after 'retry' seconds, another frame will be
    sent, until an answer is received, or 'count' frames have been sent. At
    that point, the connection will be closed and an socket.error will be
    raised in all pending operations (read or write).

    On some operating systems, the Keep-Alive mechanism is not supported, or
    some features are missing. On Windows, the 'count' parameter is fixed to 5
    on 2000/NT/XP and 10 on Vista/7). BSD (and Mac OS X) only support the
    'interval' feature. On Linux 2.4+, all the features are supported.

    Use cases:
    If your application is time critical (you want an answer in 1 second, or
    you should ask another server), then you should use the timeout mechanism.
    However, if your application is not time critical or if long processing
    times are to be expected (such is the case for complex database queries),
    then you should use the Keep-Alive mechanism to only be informed of
    connection errors. You may of course mix the two, to catch errors on the
    remote end (wait for data as long as the connection is up, but never more
    than one hour), or you may set the timeout only for some queries. (by
    default each query waits as long as configured on the connection, but you
    may override the value, or even disable the global timeout by specifying
    None as the timeout value)."""
    def __init__(self, interval, retry, count, timeout=None):
        self.interval = interval
        self.retry = retry
        self.count = count
        self.timeout = timeout
