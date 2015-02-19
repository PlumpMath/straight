# coding=utf-8
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

import straight.networking
import straight.threading

import itertools
import traceback


def test_networking():
    counter = itertools.count()
    errors = []

    class EchoServer(straight.networking.Server):
        def handle(self, connection):
            buffer = connection.readall()
            connection.writeall(buffer)

    class EchoClient(straight.threading.Thread):
        def run():
            thread_id = next(counter)
            try:
                data = ("Hello from thread %d" % thread_id).encode()
                with straight.networking.Connection("localhost", 1234) as c:
                    c.writeall(data)
                    c.shutdown()
                    if data != c.readall():
                        raise Exception("Data mismatch")
            except:
                traceback.print_exc()
                errors.append(thread_id)

    server = EchoServer(1234)  # keep a reference in scope
    assert server
    clients = []
    for _ in range(1):
        clients.append(EchoClient())

    for client in clients:
        client.join()
    assert len(errors) == 0
