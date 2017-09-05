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

from os_faults.api import node_collection
from os_faults.drivers.cloud import universal
from os_faults.tests.unit import fakes
from os_faults.tests.unit import test


@ddt.ddt
class UniversalManagementTestCase(test.TestCase):

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data((
        dict(address='os.local', auth=dict(username='root')),
        dict(remote_user='root', private_key_file=None, password=None,
             become=None, become_password=None, jump_host=None,
             jump_user=None, serial=None),
    ), (
        dict(address='os.local', auth=dict(username='user', become=True,
             become_password='secret'), serial=42),
        dict(remote_user='user', private_key_file=None, password=None,
             become=True, become_password='secret', jump_host=None,
             jump_user=None, serial=42),
    ))
    @ddt.unpack
    def test_init(self, config, expected_runner_call, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value

        cloud = universal.UniversalCloudManagement(config)

        mock_ansible_runner.assert_called_with(**expected_runner_call)
        self.assertIs(cloud.cloud_executor, ansible_runner_inst)

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @mock.patch('os_faults.drivers.cloud.universal.UniversalCloudManagement.'
                'discover_hosts')
    def test_verify(self, mock_discover_hosts, mock_ansible_runner):
        address = '10.0.0.10'
        ansible_result = fakes.FakeAnsibleResult(
            payload=dict(stdout='openstack.local'))
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [ansible_result]
        ]
        hosts = [node_collection.Host(ip=address)]
        mock_discover_hosts.return_value = hosts

        cloud = universal.UniversalCloudManagement(dict(address=address))
        cloud.verify()

        ansible_runner_inst.execute.assert_has_calls([
            mock.call(hosts, {'command': 'hostname'}),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_discover_hosts(self, mock_ansible_runner):
        address = '10.0.0.10'
        hostname = 'openstack.local'

        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [fakes.FakeAnsibleResult(
                payload=dict(stdout=hostname))]
        ]
        expected_hosts = [node_collection.Host(
            ip=address, mac=None, fqdn=hostname)]

        cloud = universal.UniversalCloudManagement(dict(address=address))

        self.assertEqual(expected_hosts, cloud.discover_hosts())

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_discover_hosts_with_iface(self, mock_ansible_runner):
        address = '10.0.0.10'
        hostname = 'openstack.local'
        mac = '0b:fe:fe:13:12:11'

        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [fakes.FakeAnsibleResult(
                payload=dict(stdout=mac))],
            [fakes.FakeAnsibleResult(
                payload=dict(stdout=hostname))],
        ]
        expected_hosts = [node_collection.Host(
            ip=address, mac=mac, fqdn=hostname)]

        cloud = universal.UniversalCloudManagement(
            dict(address=address, iface='eth1'))

        self.assertEqual(expected_hosts, cloud.discover_hosts())
