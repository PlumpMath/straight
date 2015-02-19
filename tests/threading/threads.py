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

import time


def test_basic():
    messages = []

    def test():
        messages.append("hello world from thread")
    straight.threading.Thread(test).join()
    assert len(messages) != 0


def test_sleep():
    start = time.time()
    straight.threading.Thread.sleep(1)
    assert 0.9 < time.time() - start < 1.1


def test_scheduling():
    test = []

    def run1():
        test.append("1")
        straight.threading.Thread.sleep(0)
        test.append("1")

    class run2(straight.threading.Thread):
        def run(self):
            test.append("2")
            self.sleep(0)
            test.append("2")

    t1 = straight.threading.Thread(run1)
    t2 = run2()

    t1.join()
    t2.join()
    assert "".join(test) == "1212"


def test_stop():
    global finalized
    finalized = False

    def run():
        global finalized
        try:
            straight.threading.Thread.sleep(1000)
        finally:
            finalized = True

    t = straight.threading.Thread(run)
    straight.threading.Thread.sleep(1)
    t.stop()
    t.join()
    assert finalized
