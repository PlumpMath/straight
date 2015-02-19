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

__all__ = ["WaitTimeout", "Thread", "Event", "Lock", "RLock", "Condition",
           "Semaphore", "BoundedSemaphore"]


class WaitTimeout(Exception):
    pass


from straight.threading.thread import Thread
from straight.threading.event import Event
from straight.threading.lock import Lock
from straight.threading.rlock import RLock
from straight.threading.condition import Condition
from straight.threading.semaphore import Semaphore
from straight.threading.bounded_semaphore import BoundedSemaphore
