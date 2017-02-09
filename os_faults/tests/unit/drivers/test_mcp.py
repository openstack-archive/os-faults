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

import ddt
import mock

import os_faults
from os_faults.api import node_collection
from os_faults.api import node_discover
from os_faults.drivers import mcp
from os_faults.tests.unit import fakes
from os_faults.tests.unit import test


@ddt.ddt
class MCPManagementTestCase(test.TestCase):

    def setUp(self):
        super(MCPManagementTestCase, self).setUp()

        self.hosts = [
            node_collection.Host(ip='10.0.0.2', mac='09:7b:74:90:63:c1',
                                 fqdn='node1.com'),
            node_collection.Host(ip='10.0.0.3', mac='09:7b:74:90:63:c2',
                                 fqdn='node2.com'),
        ]

        self.mock_node_discover = mock.Mock(spec=node_discover.NodeDiscover)
        self.mock_node_discover.discover_hosts.return_value = self.hosts

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data((
        dict(username='foo'),
        dict(remote_user='foo', password=None, private_key_file=None,
             jump_host=None, jump_user=None, become=False)
    ), (
        dict(username='foo', password='pass', private_key_file='/my/file.key',
             jump_host='host1', jump_user='user1', sudo=True),
        dict(remote_user='foo', password='pass',
             private_key_file='/my/file.key',
             jump_host='host1', jump_user='user1', become=True)
    ))
    @ddt.unpack
    def test_init(self, config, expected_runner_kwargs, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value

        mcp_management = os_faults._init_driver({
            'driver': 'mcp', 'args': config})

        mock_ansible_runner.assert_called_once_with(**expected_runner_kwargs)
        self.assertIs(mcp_management.cloud_executor, ansible_runner_inst)

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_verify(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.return_value = [
            fakes.FakeAnsibleResult(payload={'stdout': ''}),
            fakes.FakeAnsibleResult(payload={'stdout': ''}),
        ]

        mcp_management = mcp.MCPManagement({'username': 'foo_user'})
        mcp_management.set_node_discover(self.mock_node_discover)
        mcp_management.verify()

        ansible_runner_inst.execute.assert_called_once_with(
            ['10.0.0.2', '10.0.0.3'], {'command': 'hostname'})

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_execute_on_cloud(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.return_value = [
            fakes.FakeAnsibleResult(payload={'stdout': ''}),
            fakes.FakeAnsibleResult(payload={'stdout': ''}),
        ]

        mcp_management = mcp.MCPManagement({'username': 'foo_user'})
        mcp_management.set_node_discover(self.mock_node_discover)
        mcp_management.execute_on_cloud(['10.0.0.2'], {'foo': 'bar'},
                                        raise_on_error=False)

        ansible_runner_inst.execute.assert_called_once_with(
            ['10.0.0.2'], {'foo': 'bar'}, [])
