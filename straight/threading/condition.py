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

from straight.threading.event import Event
from straight.threading.rlock import RLock


class Condition(object):
    """A condition variable is always associated with some kind of lock; this
    can be passed in or one will be created by default. (Passing one in is
    useful when several condition variables must share the same lock.)

    A condition variable has `acquire()` and `release()` methods that call the
    corresponding methods of the associated lock. It also has a `wait()`
    method, and `notify()` and `notifyAll()` methods. These three must only be
    called when the calling thread has acquired the lock, otherwise a
    RuntimeError is raised.

    The wait() method releases the lock, and then blocks until it is awakened
    by a `notify()` or notifyAll() call for the same condition variable in
    another thread. Once awakened, it re-acquires the lock and returns. It is
    also possible to specify a timeout.

    The `notify()` method wakes up one of the threads waiting for the condition
    variable, if any are waiting. The `notifyAll()` method wakes up all threads
    waiting for the condition variable.

    Note: the `notify()` and `notifyAll()` methods don’t release the lock; this
    means that the thread or threads awakened will not return from their
    `wait()` call immediately, but only when the thread that called `notify()`
    or `notifyAll()` finally relinquishes ownership of the lock.

    Tip: the typical programming style using condition variables uses the lock
    to synchronize access to some shared state; threads that are interested in
    a particular change of state call `wait()` repeatedly until they see the
    desired state, while threads that modify the state call `notify()` or
    `notifyAll()` when they change the state in such a way that it could
    possibly be a desired state for one of the waiters."""

    def __init__(self, lock=None):
        """If the lock argument is given and not None, it must be a RLock
        object, and it will be used as the underlying lock. Otherwise, a new
        RLock object is created and used as the underlying lock."""
        if lock is None:
            lock = RLock()
        assert isinstance(lock, RLock), "Conditions require a re-entrant lock"
        self.__lock = lock
        self.__event = Event()

    def acquire(self, timeout):
        """Blocks until the thread owning the underlying lock releases it, or
        'timeout' seconds have passed. If 'timeout' is None, it will
        potentially wait forever. If the lock is not acquired by the current
        thread at the end of the call, a 'WaitTimeout' is raised. If the
        current thread already owns the lock, it will return immediately and
        update its lock count. The number of calls 'acquire' must match the
        number of calls to 'release' before the lock is actually released."""
        self.__lock.acquire(timeout)

    def release(self, *args, **kwargs):
        """Releases the underlying lock if the current thread owns it.
        Otherwise, raises an AssertionError."""
        self.__lock.release()

    def wait(self, timeout=None):
        """Wait until notified or until a timeout occurs. If the calling
        thread has not acquired the lock when this method is called, an
        AssertionError is raised.

        This method releases the underlying lock, and then blocks until it is
        awakened by a `notify()` or `notifyAll()` call for the same condition
        variable in another thread, or until the optional timeout occurs. Once
        awakened or timed out, it re-acquires the lock and returns.

        When the timeout argument is present and not None, it should be a
        floating point number specifying a timeout for the operation in seconds
        (or fractions thereof).

        Since the underlying lock is re-entrant, it is released multiple times
        until its `owned` property is False. Prior to returning, this method
        will always re-acquire the underlying lock the same number of times it
        was previously released. Note that there is no way to set a timeout for
        the re-acquire operation. It will block until the lock was restored to
        the initial state, or a GreenletExit exception is raised in the calling
        thread. For this reason, always use conditions either within `with`
        blocks or call `release()` in the `finally` section of the `try` block
        that called `acquire()`."""
        # release the lock
        count = 0
        while self.__lock.owned:
            self.__lock.release()
            count += 1

        assert count, "Attempted to wait for {0} without owning the " \
                      "underlying lock.".format(repr(self))

        try:
            self.__event.wait()
        finally:
            # reacquire the lock
            while count:
                self.acquire()
                count -= 1

    def notify(self, n=1):
        """By default, wake up one thread waiting on this condition, if any. If
        the calling thread has not acquired the lock when this method is
        called, an AssertionError is raised.

        This method wakes up at most `n` of the threads waiting for the
        condition variable; it is a no-op if no threads are waiting.

        The current implementation wakes up exactly `n` threads, if at least
        `n` threads are waiting. However, it’s not safe to rely on this
        behavior. A future, optimized implementation may occasionally wake up
        more than `n` threads.

        Note: an awakened thread does not actually return from its `wait()`
        call until it can reacquire the lock. Since `notify()` does not release
        the lock, its caller should."""
        assert self.__lock.owned, "Attempted to notify {0} without owning " \
                                  "the underlying lock".format(repr(self))
        self.__event.set_once()

    def notify_all(self):
        """Wake up all threads waiting on this condition. This method acts like
        `notify()`, but wakes up all waiting threads instead of one (or n). If
        the calling thread has not acquired the lock when this method is
        called, an AssertionError is raised."""
        assert self.__lock.owned, "Attempted to notify {0} without owning " \
                                  "the underlying lock".format(repr(self))

        self.__event.set()  # wake up all waiting threads
        self.__event.clear()  # restore the internal event state
    notifyAll = notify_all

    def __enter__(self):
        self.__lock.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__lock.release()

    def __repr__(self):
        return "<straight.threading.Condition " \
               "object at {0}>".format(hex(id(self)))
