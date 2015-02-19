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
from __future__ import absolute_import

from straight.threading import Thread
from straight.errors import StraightError
from straight.ioloop import IOLoop
from .connection import BaseConnection

import multiprocessing
import logging
import socket
log = logging.getLogger("straight.network")

class Server(Thread):
    def __init__(self, port, timeout=None, interface="0.0.0.0"):
        """Creates a server listening for connections on the specified port.
        Whenever a connection is established, the 'handle' method will be
        called with a single argument, the client Socket of the newly created
        connection. If specified, 'timeout' will set the default socket timeout
        for all incoming client connections (either float, or KeepAlive). By
        default, the server will listen on all interfaces, but that may be
        changed by specifying the 'interface'
        parameter. If a server is registered before the 'straight.run' method
        is called and Straight is configured to run with multiple workers, then
        the individual processes will receive connections in a round-robin
        fashion. If the server is registered after the run() method, it will be
        local to the current worker; all connections will be handled by this
        instance."""
        Thread.__init__(self)
        self.__timeout = timeout
        self.__lock = multiprocessing.Lock()

        # TODO: add support for ipv6 and async getaddrinfo
        # setup socket and options
        address = (interface, port)
        descriptor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        descriptor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        descriptor.bind(address)
        descriptor.listen(socket.SOMAXCONN)
        descriptor.setblocking(False)

        # register the socket with the Straight IOLoop
        self.__connection = BaseConnection(address, descriptor, None)
        log.debug("Socket " + descriptor.fileno() + " is listening on " +
                  interface + ":" + port)

    def handle(self, connection):
        raise StraightError("You must rewrite the 'handle' method to accept "
                            "connections")

    def __handle(self, connection):
        """Calls ``handle``, but cleans the client connection upon termination.
        """
        with connection:
            self.handle(connection)

    def run(self):
        """Runs the server, listening for connections on its assigned socket.
        """
        with self.__connection:
            while True:
                try:
                    # a new connection is available when the server socket is
                    # ready for reading
                    IOLoop.thread.switch(IOLoop.READ_REQUEST,
                                         self.__connection._BaseConnection__id,
                                         self.__timeout)

                    if self.__lock.acquire(False):
                        # load balance: only this worker will accept this
                        # connection
                        client, address = self.__connection._BaseConnection__socket.accept()
                        Thread(self.__handle, BaseConnection(address, client, self.__timeout))
                        self.__lock.release()
                except Exception:
                    # TODO: check what happens to the server socket when the
                    # network is shut down
                    log.exception("Exception occurred while processing server "
                                  "connection")

    def stop(self):
        """Stops the server from listening for connections. Existing
        connections (and the threads handling them) are not closed, but no
        further calls to 'handle' will be made."""
        Thread.stop(self)
