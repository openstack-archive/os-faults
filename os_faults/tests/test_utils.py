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

from os_faults.api import error
from os_faults.tests import test
from os_faults import utils


class MyException(Exception):
    pass


class UtilsTestCase(test.TestCase):

    def test_run(self):
        target = mock.Mock()
        utils.run(target, ['01', '02'])
        target.assert_has_calls([mock.call(mac_address='01'),
                                mock.call(mac_address='02')])

    def test_run_raise_exception(self):
        target = mock.Mock()
        target.side_effect = MyException()
        self.assertRaises(error.PowerManagementError,
                          utils.run, target, ['01', '02'])

    def test_start_thread(self):
        target = mock.Mock()
        target_params = {'param1': 'val1', 'param2': 'val2'}

        tw = utils.ThreadsWrapper(target)
        tw.start_thread(**target_params)
        tw.join_threads()

        target.assert_has_calls([mock.call(param1='val1', param2='val2')])
        self.assertIsInstance(tw.threads[0], threading.Thread)
        self.assertEqual(len(tw.errors), 0)

    def test_start_thread_raise_exception(self):
        target = mock.Mock()
        target.side_effect = MyException()

        tw = utils.ThreadsWrapper(target)
        tw.start_thread()
        tw.join_threads()

        self.assertEqual(type(tw.errors[0]), MyException)

    def test_join_threads(self):
        target = mock.Mock()
        thread_1 = mock.Mock()
        thread_2 = mock.Mock()

        tw = utils.ThreadsWrapper(target)
        tw.threads = [thread_1, thread_2]
        tw.join_threads()

        thread_1.join.assert_called_once()
        thread_2.join.assert_called_once()
