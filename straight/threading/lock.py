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

from straight.threading.event import Event


class Lock(object):
    """A primitive lock is a synchronization primitive that is not owned by a
    particular thread when locked.

    A primitive lock is in one of two states, “locked” or “unlocked”. It is
    created in the unlocked state. It has two basic methods, acquire() and
    release(). When the state is unlocked, acquire() changes the state to
    locked and returns immediately. When the state is locked, acquire() blocks
    until a call to release() in another thread changes it to unlocked, then
    the acquire() call resets it to locked and returns. The release() method
    should only be called in the locked state; it changes the state to unlocked
    and returns immediately.

    When more than one thread is blocked in acquire() waiting for the state to
    turn to unlocked, only one thread proceeds when a release() call resets the
    state to unlocked; which one of the waiting threads proceeds is not
    defined, and may vary across implementations.

    All methods are executed atomically."""
    def __init__(self):
        self.__unlocked = Event()

    def acquire(self, timeout=None):
        """Blocks until the thread owning the current lock releases it, or
        `timeout` seconds have passed. If `timeout` is None, it will
        potentially wait forever. If the lock is not acquired by the current
        thread at the end of the call, a `WaitTimeout` is raised."""
        self.__unlocked.wait(timeout)

    def release(self):
        """When the lock is locked, reset it to unlocked, and return. If any
        other threads are blocked waiting for the lock to become unlocked,
        allow exactly one of them to proceed.

        There is no return value."""
        self.__unlocked.set_once()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()

    def __repr__(self):
        return "<straight.threading.Lock object at {0}>".format(hex(id(self)))
