# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# import ddt
import mock

from os_faults.api import error
from os_faults.tests import test
from os_faults import utils


class UtilsTestCase(test.TestCase):

    def setUp(self):
        super(UtilsTestCase, self).setUp()
        self.macs_list = ['52:54:00:f9:b8:f9', '52:54:00:ab:64:42']

    def simple_func(self, **kwargs):
        pass

    def test_call_count(self):
        someobj = mock.Mock(side_effect=self.simple_func())
        utils.run(someobj, self.macs_list)
        self.assertEqual(someobj.call_count, 2)

    def simple_exception(self, mac_address):
        raise Exception()

    @mock.patch('os_faults.utils.ThreadsWrapper')
    def test_exception(self, mock_threads_wrapper):
        self.assertRaises(error.PowerManagementError, utils.run,
                          self.simple_exception, self.macs_list)
