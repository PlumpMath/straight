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

from straight.threading.lock import Lock

import greenlet


class RLock(Lock):
    """A reentrant lock is a synchronization primitive that may be acquired
    multiple times by the same thread. Internally, it uses the concepts of
    “owning thread” and “recursion level” in addition to the locked/unlocked
    state used by primitive locks. In the locked state, some thread owns the
    lock; in the unlocked state, no thread owns it.

    To lock the lock, a thread calls its `acquire()` method; this returns once
    the thread owns the lock. To unlock the lock, a thread calls its
    `release()` method. acquire()/release() call pairs may be nested; only the
    final release() (the release() of the outermost pair) resets the lock to
    unlocked and allows another thread blocked in acquire() to proceed."""
    def __init__(self):
        Lock.__init__(self)
        self.__owner = None
        self.__level = 0

    def acquire(self, timeout=None):
        """Blocks until the thread owning the current lock releases it, or
        `timeout` seconds have passed. If `timeout` is None, it will
        potentially wait forever. If the lock is not acquired by the current
        thread at the end of the call, a WaitTimeout is raised. If the current
        thread already owns the lock, it will return immediately and increase
        its recursion level. The number of calls 'acquire' must match the
        number of calls to 'release' before the lock is actually released."""
        current = greenlet.getcurrent()
        if self.__owner is not current:
            if self.__owner is not None:
                # wait for the owner to yield this lock
                Lock.acquire(self, timeout)
            # lock is no longer owned; claim ownership
            self.__owner = current
        # lock is owned; increase recursion level
        self.__level += 1

    def release(self):
        """Decrements the recursion level of a lock if the current thread owns
        it. Otherwise, raises an AssertionError. If the recursion level reaches
        0, then the lock is released."""
        assert self.owned, "Attempted to release {0} without " \
                           "owning it".format(repr(self))
        # decrement recursion level (since the lock is owned, the recursion
        # level is strictly positive)
        self.__level -= 1
        if self.__level == 0:
            # lock is no longer owned; yield ownership and allow other threads
            # to claim it
            self.__owner = None
            Lock.release(self)

    @property
    def owned(self):
        """Returns True if and only if the current thread owns the lock."""
        return self.__owner is greenlet.getcurrent()

    def __repr__(self):
        return "<straight.threading.RLock object at {0}>".format(hex(id(self)))
