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
import straight.util.base_pool
import random


class Resource(object):
    def __init__(self, *args, **kwargs):
        self.args = []
        self.kwargs = {}
        self.args.extend(args)
        self.kwargs.update(kwargs)


def test_constructor_args():
    args = []
    for _ in range(10):
        args.append(str(random.randint(0, 1000)))

    kwargs = {}
    for _ in range(10):
        kwargs[str(random.randint(0, 1000))] = random.random()

    pool = straight.util.base_pool.BasePool(Resource, *args, **kwargs)
    resource = pool.acquire()

    assert args == resource.args
    assert kwargs == resource.kwargs

    # cleanup
    pool.release(resource)


def test_reuse():
    pool = straight.util.base_pool.BasePool(Resource)
    pool.growth = 1
    first = pool.acquire()
    pool.release(first)
    second = pool.acquire()
    assert first is second

    # cleanup
    pool.release(second)


def test_shrink():
    pool = straight.util.base_pool.BasePool(Resource)
    resources = [pool.acquire() for i in xrange(100)]
    peak = pool.size()
    for resource in resources:
        pool.release(resource)
    assert pool.size() < peak
