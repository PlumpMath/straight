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


class Undefined(object):
    """Used as a default value for uninstantiated values"""


class BaseConnection(object):
    """Maintains a connection to a remote end-point. Automatically closes the
    connection when its destructor is called."""
    __eagain = socket.error(errno.EAGAIN, "Handled internally")

    def __init__(self, address, descriptor, timeout):
        """Must never be called directly. Use the 'Client' or 'Server'
        classes."""

        object.__setattr__(self, "status", 0)
        object.__setattr__(self, "address", address)
        self.__socket = descriptor
        self.__buffer = None

        descriptor.setblocking(False)
        # configure KeepAlive or timeout
        if isinstance(timeout, straight.networking.keepalive.KeepAlive):
            descriptor.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            try:
                # Linux 2.4+
                descriptor.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE,
                                      timeout.interval)
                descriptor.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL,
                                      timeout.retry)
                descriptor.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT,
                                      timeout.count)
            except Exception:
                # BSD and Mac OS X
                try:
                    descriptor.setsockopt(socket.IPPROTO_TCP,
                                          socket.TCP_KEEPIDLE,
                                          timeout.interval)
                except Exception:
                    try:
                        # Windows expects the values in milliseconds
                        descriptor.ioctl(socket.SIO_KEEPALIVE_VALS, (
                            True,
                            int(1000 * timeout.interval),
                            int(1000 * timeout.retry))
                        )
                    except Exception:
                        log.warning("Keep-Alive frames (requested for " +
                                    descriptor +") are not supported by the "
                                    "operating system.")

            self.timeout = timeout.timeout
        else:
            self.timeout = timeout

        self.__id = descriptor.fileno()
        self.__reading = self.__writing = False

    def __setattr__(self, key, value):
        if key in ("address", "closed"):
            raise AttributeError("The '%s' attribute is read only" % key)
        object.__setattr__(self, key, value)

    def __delattr__(self, key):
        if key in ("address", "closed"):
            raise AttributeError("The '%s' attribute is read only" % key)
        object.__delattr__(self, key)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, value, traceback):
        self.close()

    def __del__(self):
        """Closes the connection, if not closed already."""
        if hasattr(self, "status") and self.status != 2:
            self.close()

    def shutdown(self):
        """Half closes the connection, notifying the other end that this
        endpoint has sent all the data it's ever going to. The socket may still
        be used for reading. Any current or future write calls will fail with a
        socket.error."""
        if self.status != 0:
            raise socket.error(errno.ESHUTDOWN, "Connection is already half "
                                                "closed")

        IOLoop.unregister(self.__id, False)
        self.__socket.shutdown(socket.SHUT_WR)
        object.__setattr__(self, "status", 1)

    def close(self):
        """Closes the connection. Any active or future read / write calls will
        fail with a socket.error."""
        if self.status == 2:
            raise socket.error(errno.ENOTCONN, "Connection is already closed")

        IOLoop.unregister(self.__id)
        self.__socket.close()
        self.__socket = None
        object.__setattr__(self, "status", 2)

    def __read(self, count, timeout):
        self.__reading = True
        try:
            if self.__buffer is not None:
                if self.__buffer.tell() < len(self.__buffer.getvalue()):
                    # there's still some data available in buffer
                    return self.buffer.read(count)
                else:
                    # buffer is depleted; dispose and read from network
                    self.__buffer = None
            return self.__socket.recv(count)
        except socket.error as e:
            if e.args[0] not in (errno.EINPROGRESS, errno.EWOULDBLOCK,
                                 errno.EAGAIN):
                self.__status = 2
                raise
            IOLoop.thread.switch(IOLoop.READ_REQUEST, self.__id, timeout)
            try:
                return self.__socket.recv(count)
            except socket.error:
                self.__status = 2
                raise
        finally:
            self.__reading = False

    def __can_read(self, timeout):
        if self.status == 2:
            raise socket.error(errno.ENOTCONN, "Connection is closed.")
        if self.__reading:
            raise ConnectionInUse("Another thread is currently reading from "
                                  "this connection")

        if timeout is Undefined:
            return self.timeout
        return timeout

    def read(self, count, timeout=Undefined):
        """Reads a chunk of data from the remote end-point. Returns a string of
        at most 'count' bytes. If the connection is broken, or if no data is
        received after the specified timeout, it will raise a socket.error.
        This method returns an empty string if the connection has been closed
        by the other end, and no further data will ever be received on this
        connection. If 'timeout' is specified, it will be used; otherwise the
        timeout configured with this connection if any, will be used. If a
        timeout is configured with this connection, but this request should
        wait until the connection is dropped, set timeout to None to wait as
        long as the connection is alive (only predictable when using
        Keep-Alive). Returns the read data."""
        timeout = self.__can_read(timeout)
        if not count:
            return
        return self.__read(count, timeout)

    def __write(self, data, timeout):
        self.__writing = True
        try:
            count = self.__socket.send(data)
            if count:
                return count
            raise self.__eagain
        except socket.error as e:
            if e.args[0] not in (errno.EINPROGRESS, errno.EWOULDBLOCK,
                                 errno.EAGAIN):
                self.status = 1
                raise
            IOLoop.thread.switch(IOLoop.WRITE_REQUEST, self.__id, timeout)
            try:
                count = self.__socket.send(data)
                if count == 0:
                    raise socket.error(errno.ECONNRESET, "Connection closed")
                return count
            except socket.error:
                self.status = 1
                raise
        finally:
            self.__writing = False

    def __can_write(self, timeout):
        if self.status != 0:
            raise socket.error(errno.ESHUTDOWN, "Connection is closed.")
        if self.__writing:
            raise ConnectionInUse("Another thread is currently writing to this "
                                  "connection")

        if timeout is Undefined:
            return self.timeout
        return timeout

    def write(self, data, timeout=Undefined):
        """Writes a chunk of data to a remote end-point. If the connection is
        broken, or no data could be sent after the specified timeout, it will
        raise an socket.error. Returns the number of bytes written, which will
        always be different from 0. If 'timeout' is specified, it will be used;
        otherwise the timeout configured with this connection if any, will be
        used. If a timeout is configured with this connection, but this request
        should wait until the connection is dropped, set timeout to None to
        wait as long as the connection is alive (only predictable when using
        Keep-Alive). Note that success only means that the data has been sent,
        not necessarily received by the remote end-point. If you want to
        confirm data reception, design your protocol to reply with a 'OK'
        message which you would then read."""
        timeout = self.__can_write(timeout)
        if not data:
            return
        return self.__write(data, timeout)

    def readall(self, count=None, timeout=Undefined):
        """Reads from the remote end-point, until 'count' bytes have been read,
        the connection is closed by the other end-point or a socket.error
        occurred. If 'count' is None reads until the connection is closed.
        Otherwise, will wither return exactly 'count' bytes, or raise a
        socket.error (connection reset by peer). If 'timeout' is specified, it
        will be used; otherwise the timeout configured with this connection if
        any, will be used. If a timeout is configured with this connection, but
        this request should wait until the connection is dropped, set timeout
        to None to wait as long as the connection is alive (only predictable
        when using Keep-Alive). Returns the read data."""
        timeout = self.__can_read(timeout)
        if timeout is not None:
            timeout += time.time()

        data = io.BytesIO()
        while count != 0:
            c, t = count, timeout
            if not c:
                c = 4096
            if t is not None:
                t -= time.time()

            buff = self.__read(c, t)
            if not buff:
                # end of stream
                if count:
                    # closed before the entire message was read
                    raise socket.error(
                        errno.ECONNRESET,
                        "Connection closed prematurely (" + count + " bytes "
                        "left to read)."
                    )
                break

            # write to output buffer and update byte count
            data.write(buff)
            if count:
                count -= len(buff)
        return data.getvalue()
    read_all = readAll = readFully = readall

    def writeall(self, data, timeout=Undefined):
        """Writes 'data' to the remote end-point, until completely written, the
        connection has been closed by the other end-point or a socket.error
        occurred. If 'timeout' is specified, it will be used; otherwise the
        timeout configured with this connection if any, will be used. If a
        timeout is configured with this connection, but this request should
        wait until the connection is dropped, set timeout to None to wait as
        long as the connection is alive (only predictable when using
        Keep-Alive). As with 'write', there's no way to determine how many
        bytes have been successfully received by the remote end-point; success
        only means that the data was sent. If you want to confirm data
        reception, design your protocol to reply with a 'OK' message which you
        would then read."""
        timeout = self.__can_write(timeout)
        if not data:
            return
        if timeout is not None:
            timeout += time.time()

        count = len(data)
        offset = 0
        try:
            # python 2.7+
            view = memoryview(data)
            while offset < count:
                t = timeout
                if t is not None:
                    t -= time.time()
                offset += self.__write(view[offset:], t)
        except NameError:
            # python 2.6
            while offset < count:
                t = timeout
                if t is not None:
                    t -= time.time()
                offset += self.__write(buffer(data, offset), t)
        return count
    write_all = writeAll = writeFully = writeall

    def readuntil(self, pattern, timeout=Undefined):
        """Reads from the remote end-point until the string 'pattern' is
        encountered, the connection has been closed by the other end-point or a
        socket.error occurred. If 'timeout' is specified, it will be used;
        otherwise the timeout configured with this connection if any, will be
        used. If a timeout is configured with this connection, but this request
        should wait until the connection is dropped, set timeout to None to
        wait as long as the connection is alive (only predictable when using
        Keep-Alive). Returns the read data, which will always end in 'pattern'.
        If the connection is closed before the requested pattern is received, a
        socket.error (connection reset by peer) is raised."""
        timeout = self.__can_read(timeout)
        if timeout is not None:
            timeout += time.time()

        if self.__buffer:
            #buffer exists; store current position and seek to the end of it
            offset = self.__buffer.tell()
            self.__buffer.seek(0, 2)
        else:
            self.__buffer = io.BytesIO()
            offset = 0

        try:
            while True:
                # read next packet into the buffer
                t = timeout
                if t is not None:
                    t -= time.time()
                buff = self.__read(4096, t)
                if not buff:
                    raise socket.error(errno.ECONNRESET,
                                       "Connection closed prematurely ("
                                       "requested pattern not found).")
                self.__buffer.write(buff)

                try:
                    # the buffer has the requested pattern; seek to the first
                    # unread position, read and return it
                    index = self.__buffer.getvalue().index(pattern, offset)
                    self.__buffer.seek(offset)
                    return self.__buffer.read(index + len(pattern) - offset)
                except ValueError:
                    """Pattern not found. Try again on the next pass."""
        except ConnectionTimeout:
            self.__buffer.seek(offset)
            raise

    read_until = readUntil = readuntil
