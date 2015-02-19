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

import logging
import sys
import os

current = os.path.dirname(__file__)
package = os.path.abspath(os.path.join(current, os.pardir))
sys.path.append(package)

import straight.threading
import straight
logging.basicConfig()


def pytest_runtest_call(item):
    errors = []
    runtest = item.runtest

    def run_test():
        try:
            runtest()
        except:
            errors.append(sys.exc_type)
            errors.append(sys.exc_value)
            errors.append(sys.exc_traceback)
        finally:
            straight.shutdown()

    def run_straight():
        straight.threading.Thread(run_test)
        straight.run(1)
        if errors:
            raise errors[0], errors[1], errors[2]

    item.runtest = run_straight


def pytest_collect_file(path, parent):
    if \
            path.ext == ".py" and \
            "networking" not in str(path):
        return parent.Module(path, parent)
