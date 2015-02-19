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
from straight import ioloop

import greenlet
import logging


class Thread(object):
    """This class represents an activity that is run in a separate thread of
    control. There are two ways to specify the activity: by passing a callable
    object to the constructor, or by overriding the `run()` method in a
    subclass. No other methods (except for the constructor) should be
    overridden in a subclass. In other words, only override the `__init__()`
    and `run()` methods of this class.

    Once a thread object is created, its activity must be started by calling
    the thread’s `start()` method. This invokes the `run()` method in a
    separate thread of control.

    Once the thread’s activity is started, the thread is considered ‘alive’. It
    stops being alive when its `run()` method terminates – either normally, or
    by raising an unhandled exception. The `alive` attribute tests whether the
    thread is alive.

    Other threads can call a thread’s `join()` method. This blocks the calling
    thread until the thread whose `join()` method is called is terminated.

    A thread has a name. The name can be passed to the constructor, and read or
    changed through the `name` attribute. It should be a string or unicode.

    Other threads may also stop a thread by calling it's `stop()` method. This
    raises an GreenletExit exception in the target thread and the default
    action is to terminate it as soon as possible. However, user code may catch
    the exception and delay termination, or ignore it completely."""
    __threads = set()  # all active Thread instances; we need to keep explicit
                       # references to all running threads to prevent garbage
                       # collection and to allow for `Thread.enumerate()`

    def __init__(self, target=None, name=None, args=(), kwargs={}):
        # compat with threading.Thread
        if name:
            self.name = name
        else:
            self.name = "Unnamed thread"

        self.__target = target
        self.__args = args
        self.__kwargs = kwargs

        self.__greenlet = None
        self.__finished = False

    def start(self):
        if self.__greenlet:
            raise RuntimeError("Thread '{0}' was already "
                               "started".format(self.name))

        self.__greenlet = greenlet.greenlet(self.__safe_run)
        ioloop.resume(self.__greenlet)

    def __safe_run(self):
        """Calls the 'run' method, making sure to trigger the attached event
        once it returns."""
        try:
            Thread.__threads.add(self)
            self.run()
        except:
            logging.exception("Unhandled exception in "
                              "thread '{0}'".format(self.name))
        finally:
            Thread.__threads.remove(self)
            # for performance reasons, the 'finished' event bound to a thread
            # is only created the first time another thread waits on this it
            if isinstance(self.__finished, Event):
                self.__finished.set()
            self.__finished = True

    def run(self):
        """This method will be called in a new thread."""
        if self.__target:
            self.__target(*self.__args, **self.__kwargs)

    def stop(self):
        """"Stops the thread, if active. The thread's 'run' method will receive
        a GreenletExit exception."""
        ioloop.resume(self.__greenlet, greenlet.GreenletExit)

    def join(self, timeout=None):
        """Wait until the thread terminates. This blocks the calling thread
        until the thread whose `join()` method is called terminates – either
        normally or through an unhandled exception – or until the optional
        timeout occurs. If the operation times out, a WaitTimeout will be
        raised instead.

        When the timeout argument is present and not None, it should be a
        floating point number specifying a timeout for the operation in seconds
        (or fractions thereof).

        When the timeout argument is not present or None, the operation will
        block until the thread terminates.

        A thread can be `join()`ed many times."""
        if self.__finished is False:
            self.__finished = Event()
        elif self.__finished is True:
            return
        self.__finished.wait(timeout)

    def __repr__(self):
        return "<straight.threading.Thread({0}) object at {1}>".format(
            self.name, hex(id(self)))

    @property
    def alive(self):
        """Return whether the thread is alive.

        This method returns True just before the `run()` method starts until
        just after the `run()` method terminates."""
        return self.__greenlet is not None

    @classmethod
    def enumerate(self):
        """Return a list of all Thread objects currently alive. The list does
        not include the main thread, any external (non straight) threads or any
        threads that have been terminated or have yet to be started.
        """
        return list(self.__threads)
