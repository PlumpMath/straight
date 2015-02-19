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

import straight.threading

import random
import pytest


def test_basic():
    lock = straight.threading.Lock()
    errors = []

    def run1():
        with lock:
            straight.threading.Thread.sleep(1.0)

    def run2():
        straight.threading.Thread.sleep(0.5)
        with pytest.raises(straight.errors.WaitTimeout):
            lock.acquire(0)
            errors.append("Double lock")  # must never be executed
        straight.threading.Thread.sleep(1.0)
        try:
            lock.acquire(0)
        except straight.WaitTimeout:
            errors.append("Not unlocked")

    t1 = straight.threading.Thread(run1)
    t2 = straight.threading.Thread(run2)

    t1.join()
    t2.join()

    for message in errors:
        raise Exception(message)


def test_stress():
    global owner
    owner = None
    threads = []
    errors = []
    lock = straight.threading.Lock()

    for i in range(1000):
        def run():
            global owner
            with lock:
                if owner is not None:
                    errors.append(i)
                owner = i
                straight.threading.Thread.sleep(random.random() / 100)
                owner = None

        threads.append(straight.threading.Thread(run))

    for thread in threads:
        thread.join()
    assert len(errors) == 0
