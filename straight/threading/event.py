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

from straight.threading import WaitTimeout
from straight import ioloop

import greenlet
import pyuv


class Event(object):
    """This is one of the simplest mechanisms for communication between
    threads: one thread signals an event and other threads wait for it.

    An event object manages an internal flag that can be set to true with the
    `set()` method and reset to false with the `clear()` method. The `wait()`
    method blocks until the flag is true."""

    def __init__(self):
        """The internal flag is initially false."""
        self.__set = False
        self.__waiters = {}

    def isSet(self):
        """Return true if and only if the internal flag is true."""
        return self.__set
    is_set = isSet

    def set(self):
        """Set the internal flag to true. All threads waiting for it to become
        true are awakened. Threads that call `wait()` once the flag is true
        will not block at all."""
        # operation is atomic (no pauses)
        self.__set = True
        for thread in self.__waiters:
            timer = self.__waiters[thread]
            if timer:
                timer.stop()
            ioloop.resume(thread)
        self.__waiters.clear()

    def clear(self):
        """Reset the internal flag to false. Subsequently, threads calling
        `wait()` will block until `set()` is called to set the internal flag to
        true again."""
        self.__set = False

    def set_once(self):
        """Wakes up a single thread waiting for the event to become available.
        The chosen thread (if any) will resume as if the event was set, but all
        the others (if any) will keep waiting until such a time when their
        timeout expires, or another `set` or `setAndClear` call is made. This
        event will remain unset at the end of this call. Mostly used by
        `Condition` objects, but it may be used whenever the `Lock` overhead
        associated with a condition is not needed. If the event is already set
        when this method is called, it will do nothing."""
        try:
            thread, timer = self.__waiters.popitem()
            if timer:
                timer.stop()
            ioloop.resume(thread)
        except KeyError:
            """No threads waiting for this event, or the event is already set.
            Do nothing."""
    setOnce = set_once

    def wait(self, timeout=None):
        """Block until the internal flag is true. If the internal flag is true
        on entry, return immediately. Otherwise, block until another thread
        calls `set()` to set the flag to true, or until the optional timeout
        occurs.

        When the timeout argument is present and not None, it should be a
        floating point number specifying a timeout for the operation in seconds
        (or fractions thereof).

        This method returns once the event was triggered. If the operation
        times out, a WaitTimeout will be raised instead."""
        if self.__set:
            return

        current = greenlet.getcurrent()

        if timeout:
            def wakeup(timer):
                del self.__waiters[timer.thread]
                ioloop.resume(timer.thread, WaitTimeout)

            timer = pyuv.Timer(ioloop.default)
            timer.thread = current
            timer.start(wakeup, timeout)
        else:
            timer = None

        self.__waiters[current] = timer
        ioloop.pause(current)

    def __repr__(self):
        return "<straight.threading.Event object at {0}>".format(hex(id(self)))
