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

import mock
import unittest

from os_faults.cmd import cmd
from os_faults.tests import test


class CmdTestCase(test.TestCase):

    def test_empty_args(self):
        self.assertRaises(SystemExit, cmd.main)

    @mock.patch('os_faults.human_api')
    @mock.patch('os_faults.connect')
    def test_destructor_created(self, mock_connect, mock_human):
        with mock.patch('sys.argv', ['', '-c', 'my_file', 'my_command']):
            cmd.main()
            mock_connect.assert_called_once()
            mock_connect.accert_has_calls(mock.call(config_filename='my_file'))

    @mock.patch('os_faults.human_api')
    @mock.patch('os_faults.connect')
    def test_human_api_called(self, mock_connect, mock_human):
        with mock.patch('sys.argv', ['', '-c', 'my_file', 'my_command']):
            cmd.main()
            mock_human.assert_called_once()
            mock_human.accert_has_calls(mock.call(
                mock.MagicMock(name='connect()'), 'my_command'))

    @mock.patch('os_faults.human_api')
    @mock.patch('os_faults.connect')
    def test_human_verify(self, mock_connect, mock_human):
        with mock.patch('sys.argv', ['', '-c', 'my_file', '-v']):
            cmd.main()
            mock_connect.accert_has_calls(mock.call(mock.call().verify()))


if __name__ == '__main__':
    unittest.main()
