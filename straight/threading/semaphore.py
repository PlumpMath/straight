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


class Semaphore(object):
    """This is one of the oldest synchronization primitives in the history of
    computer science, invented by the early Dutch computer scientist Edsger W.
    Dijkstra (he used `P()` and `V()` instead of `acquire()` and `release()`).

    A semaphore manages an internal counter which is decremented by each
    `acquire()` call and incremented by each `release()` call. The counter can
    never go below zero; when `acquire()` finds that it is zero, it blocks,
    waiting until some other thread calls `release()`."""

    def __init__(self, value=1):
        """The optional argument gives the initial value for the internal
        counter; it defaults to 1. If the value given is less than 0,
        `ValueError` is raised."""
        if value < 0:
            raise ValueError
        self.__counter = value
        self.__event = Event()

    def acquire(self, timeout=None):
        """Acquire a semaphore.

        When invoked without arguments: if the internal counter is larger than
        zero on entry, decrement it by one and return immediately. If it is
        zero on entry, block, waiting until some other thread has called
        `release()` to make it larger than zero. This is done with proper
        interlocking so that if multiple `acquire()` calls are blocked,
        `release()` will wake exactly one of them up. The implementation may
        pick one at random, so the order in which blocked threads are awakened
        should not be relied on.

        The optional argument `timeout` specifies the maximum number of seconds
        the calling thread is willing to wait for the semaphore to become
        available. If the timeout is reached, a WaitError is raised in the
        calling thread. The default is `None`, meaning no timeout."""
        if self.__counter == 0:
            self.__event.wait(timeout)

        self.__counter -= 1

    def release(self):
        """Release a semaphore, incrementing the internal counter by one. When
        it was zero on entry and another thread is waiting for it to become
        larger than zero again, wake up that thread."""
        if self.__counter == 0:
            self.__event.set_once()
        self.__counter += 1

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()

    def __repr__(self):
        return "<straight.threading.Semaphore " \
               "object at {0}>".format(hex(id(self)))
