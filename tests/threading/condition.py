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


def test_notify_one():
    c = straight.threading.Condition()

    def run():
        with c:
            c.wait()

    t1 = straight.threading.Thread(run)
    t2 = straight.threading.Thread(run)

    straight.threading.Thread.sleep(0.5)
    with c:
        c.notify_all()
    straight.threading.Thread.sleep(0.5)
    assert not (t1.is_alive() or t1.is_alive())
    if t1.is_alive():
        t1.stop()
    if t2.is_alive():
        t2.stop()


def test_notify_all():
    c = straight.threading.Condition()

    def run():
        with c:
            c.wait()

    t1 = straight.threading.Thread(run)
    t2 = straight.threading.Thread(run)

    straight.threading.Thread.sleep(0.5)
    with c:
        c.notify_all()
    straight.threading.Thread.sleep(0.5)
    assert not (t1.is_alive() or t2.is_alive())


def test_no_notify():
    c = straight.threading.Condition()

    def run():
        with c:
            c.wait()

    t1 = straight.threading.Thread(run)
    t2 = straight.threading.Thread(run)

    with c:
        c.notify()
    straight.threading.Thread.sleep(0.5)
    assert t1.is_alive() and t2.is_alive()
    t1.stop()
    t2.stop()
