# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import threading

import mock

from os_faults.tests.unit import test
from os_faults import utils


class MyException(Exception):
    pass


class UtilsTestCase(test.TestCase):

    def test_start_thread(self):
        target = mock.Mock()
        target_params = {'param1': 'val1', 'param2': 'val2'}

        tw = utils.ThreadsWrapper()
        tw.start_thread(target, **target_params)
        tw.join_threads()

        target.assert_has_calls([mock.call(param1='val1', param2='val2')])
        self.assertIsInstance(tw.threads[0], threading.Thread)
        self.assertEqual(len(tw.errors), 0)

    def test_start_thread_raise_exception(self):
        target = mock.Mock()
        target.side_effect = MyException()

        tw = utils.ThreadsWrapper()
        tw.start_thread(target)
        tw.join_threads()

        self.assertEqual(type(tw.errors[0]), MyException)

    def test_join_threads(self):
        thread_1 = mock.Mock()
        thread_2 = mock.Mock()

        tw = utils.ThreadsWrapper()
        tw.threads = [thread_1, thread_2]
        tw.join_threads()

        thread_1.join.assert_called_once()
        thread_2.join.assert_called_once()


class MyClass(object):
    FOO = 10

    def __init__(self):
        self.BAR = None

    @utils.require_variables('FOO')
    def method(self, a, b):
        return self.FOO + a + b

    @utils.require_variables('BAR', 'BAZ')
    def method_that_miss_variables(self):
        return self.BAR, self.BAZ


class RequiredVariablesTestCase(test.TestCase):

    def test_require_variables(self):
        inst = MyClass()
        self.assertEqual(inst.method(1, b=2), 13)

    def test_require_variables_not_implemented(self):
        inst = MyClass()
        err = self.assertRaises(NotImplementedError,
                                inst.method_that_miss_variables)
        msg = 'BAR, BAZ required for MyClass.method_that_miss_variables'
        self.assertEqual(str(err), msg)


class MyPoint(utils.ComparableMixin):
    ATTRS = ('a', 'b')

    def __init__(self, a, b):
        self.a = a
        self.b = b


class ComparableMixinTestCase(test.TestCase):

    def test_operations(self):
        p1 = MyPoint(1, 'a')
        p2 = MyPoint(1, 'b')
        p3 = MyPoint(2, 'c')
        p4 = MyPoint(2, 'c')

        self.assertTrue(p1 < p2)
        self.assertTrue(p1 <= p2)
        self.assertFalse(p1 == p2)
        self.assertFalse(p1 >= p2)
        self.assertFalse(p1 > p2)
        self.assertTrue(p1 != p2)
        self.assertTrue(hash(p1) != hash(p2))

        self.assertTrue(p2 < p3)
        self.assertTrue(p2 <= p3)
        self.assertFalse(p2 == p3)
        self.assertFalse(p2 >= p3)
        self.assertFalse(p2 > p3)
        self.assertTrue(p2 != p3)
        self.assertTrue(hash(p2) != hash(p3))

        self.assertFalse(p3 < p4)
        self.assertTrue(p3 <= p4)
        self.assertTrue(p3 == p4)
        self.assertTrue(p3 >= p4)
        self.assertFalse(p3 > p4)
        self.assertFalse(p3 != p4)
        self.assertEqual(hash(p3), hash(p4))


class MyRepr(utils.ReprMixin):
    REPR_ATTRS = ('a', 'b', 'c')

    def __init__(self):
        self.a = 'foo'
        self.b = {'foo': 'bar'}
        self.c = 42


class ReprMixinTestCase(test.TestCase):

    def test_repr(self):
        r = MyRepr()
        self.assertEqual("MyRepr(a='foo', b={'foo': 'bar'}, c=42)", repr(r))
