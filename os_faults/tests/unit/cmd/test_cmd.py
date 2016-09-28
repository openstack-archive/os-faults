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

from os_faults.cmd import cmd
from os_faults.tests.unit import test


class CmdTestCase(test.TestCase):

    def test_main_no_args(self):
        self.assertRaises(SystemExit, cmd.main)

    @mock.patch('os_faults.human_api')
    @mock.patch('os_faults.connect')
    def test_main_verify(self, mock_connect, mock_human_api):
        with mock.patch('sys.argv', ['', '-c', 'my_file', '-v']):
            cmd.main()

            mock_connect.assert_called_once_with(config_filename='my_file')
            mock_connect.return_value.verify.assert_called_once_with()
            mock_human_api.assert_not_called()

    @mock.patch('os_faults.human_api')
    @mock.patch('os_faults.connect')
    def test_main_command(self, mock_connect, mock_human_api):
        with mock.patch('sys.argv', ['', '-c', 'my_file', 'my_command']):
            cmd.main()

            mock_connect.assert_called_once_with(config_filename='my_file')
            mock_connect.return_value.verify.assert_not_called()
            mock_human_api.assert_called_once_with(
                mock_connect.return_value, 'my_command')

    @mock.patch('os_faults.human_api')
    @mock.patch('os_faults.connect')
    def test_main_verify_and_command(self, mock_connect, mock_human_api):
        with mock.patch('sys.argv', ['', '-c', 'my_file', '-v', 'my_command']):
            cmd.main()

            mock_connect.assert_called_once_with(config_filename='my_file')
            mock_connect.return_value.verify.assert_called_once_with()
            mock_human_api.assert_called_once_with(
                mock_connect.return_value, 'my_command')
