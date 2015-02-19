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

from straight.threading.semaphore import Semaphore


class BoundedSemaphore(Semaphore):
    """A bounded semaphore checks to make sure its current value doesn’t exceed
    its initial value. If it does, ValueError is raised. In most situations
    semaphores are used to guard resources with limited capacity. If the
    semaphore is released too many times it’s a sign of a bug."""
    def __init__(self, value=1):
        Semaphore.__init__(self, value)
        self.__max = value

    def release(self):
        if self.__counter == self.__max:
            raise ValueError
        Semaphore.release(self)

    def __repr__(self):
        return "<straight.threading.BoundedSemaphore " \
               "object at {0}>".format(hex(id(self)))
