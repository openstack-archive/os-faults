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

import os

from click import testing
import mock

from os_faults.api import cloud_management
from os_faults.api import node_collection
from os_faults.cmd import main
from os_faults.tests.unit import test


class MainTestCase(test.TestCase):

    def setUp(self):
        super(MainTestCase, self).setUp()
        self.runner = testing.CliRunner()

    def test_version(self):
        result = self.runner.invoke(main.main, ['--version'])
        self.assertEqual(0, result.exit_code)
        self.assertIn('Version', result.output)

    @mock.patch('os_faults.connect')
    def test_verify(self, mock_connect):
        with self.runner.isolated_filesystem():
            with open('my.yaml', 'w') as f:
                f.write('foo')
            result = self.runner.invoke(main.main, ['verify'],
                                        env={'OS_FAULTS_CONFIG': 'my.yaml'})
        self.assertEqual(0, result.exit_code)
        mock_connect.assert_called_once_with(config_filename='my.yaml')
        destructor = mock_connect.return_value
        destructor.verify.assert_called_once_with()

    @mock.patch('os_faults.connect')
    def test_verify_with_config(self, mock_connect):
        with self.runner.isolated_filesystem():
            with open('my.yaml', 'w') as f:
                f.write('foo')
            myconf = os.path.abspath(f.name)
            result = self.runner.invoke(main.main, ['verify', '-c', myconf])
        self.assertEqual(0, result.exit_code)
        mock_connect.assert_called_once_with(config_filename=myconf)
        destructor = mock_connect.return_value
        destructor.verify.assert_called_once_with()

    @mock.patch('os_faults.discover')
    def test_discover(self, mock_discover):
        mock_discover.return_value = {'foo': 'bar'}
        with self.runner.isolated_filesystem():
            with open('my.yaml', 'w') as f:
                f.write('foo')
            myconf = os.path.abspath(f.name)
            result = self.runner.invoke(main.main, ['discover', '-c', myconf,
                                                    'my-new.yaml'])
            self.assertEqual(0, result.exit_code)
            mock_discover.assert_called_once_with('foo')

            with open('my-new.yaml') as f:
                self.assertEqual('foo: bar\n', f.read())

    @mock.patch('os_faults.connect')
    def test_nodes(self, mock_connect):
        cloud_management_mock = mock.create_autospec(
            cloud_management.CloudManagement)
        mock_connect.return_value = cloud_management_mock
        cloud_management_mock.get_nodes.return_value.hosts = [
            node_collection.Host(
                ip='10.0.0.2', mac='09:7b:74:90:63:c1', fqdn='node1.local'),
            node_collection.Host(
                ip='10.0.0.3', mac='09:7b:74:90:63:c2', fqdn='node2.local')]

        with self.runner.isolated_filesystem():
            with open('my.yaml', 'w') as f:
                f.write('foo')
            myconf = os.path.abspath(f.name)
            result = self.runner.invoke(main.main, ['nodes', '-c', myconf])
        self.assertEqual(0, result.exit_code)
        self.assertEqual(
            '- fqdn: node1.local\n'
            '  ip: 10.0.0.2\n'
            '  mac: 09:7b:74:90:63:c1\n'
            '- fqdn: node2.local\n'
            '  ip: 10.0.0.3\n'
            '  mac: 09:7b:74:90:63:c2\n', result.output)

    @mock.patch('os_faults.registry.get_drivers')
    def test_drivers(self, mock_get_drivers):
        mock_get_drivers.return_value = {'foo': 1, 'bar': 2}

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(main.main, ['drivers'])
        self.assertEqual(0, result.exit_code)
        self.assertEqual(
            '- bar\n'
            '- foo\n', result.output)
