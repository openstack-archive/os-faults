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

from os_faults.ansible import executor
from os_faults.api import error
from os_faults.api import node_collection
from os_faults.drivers.cloud import fuel
from os_faults.tests.unit import fakes
from os_faults.tests.unit import test


@ddt.ddt
class FuelManagementTestCase(test.TestCase):

    def setUp(self):
        super(FuelManagementTestCase, self).setUp()
        self.conf = {
            'address': 'fuel.local',
            'username': 'root',
        }

        self.fake_ansible_result = fakes.FakeAnsibleResult(
            payload={
                'stdout': '[{"ip": "10.0.0.2", "mac": "02", "fqdn": "node-2"},'
                          ' {"ip": "10.0.0.3", "mac": "03", "fqdn": "node-3"}]'
            })

        self.master_host = node_collection.Host('fuel.local')
        self.hosts = [
            node_collection.Host(ip='10.0.0.2', mac='02', fqdn='node-2'),
            node_collection.Host(ip='10.0.0.3', mac='03', fqdn='node-3'),
        ]

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data((
        dict(address='fuel.local', username='root'),
        (mock.call(private_key_file=None, remote_user='root'),
         mock.call(private_key_file=None, remote_user='root',
                   jump_host='fuel.local', serial=None))
    ), (
        dict(address='fuel.local', username='root', slave_direct_ssh=True,
             serial=42),
        (mock.call(private_key_file=None, remote_user='root'),
         mock.call(private_key_file=None, remote_user='root',
                   jump_host=None, serial=42))
    ))
    @ddt.unpack
    def test_init(self, config, expected_runner_calls, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value

        fuel_managment = fuel.FuelManagement(config)

        mock_ansible_runner.assert_has_calls(expected_runner_calls)
        self.assertIs(fuel_managment.master_node_executor, ansible_runner_inst)
        self.assertIs(fuel_managment.cloud_executor, ansible_runner_inst)

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_verify(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [fakes.FakeAnsibleResult(payload={'stdout': ''}),
             fakes.FakeAnsibleResult(payload={'stdout': ''})],
        ]
        fuel_managment = fuel.FuelManagement(self.conf)
        fuel_managment.verify()

        ansible_runner_inst.execute.assert_has_calls([
            mock.call([self.master_host], {'command': 'fuel node --json'}),
            mock.call(self.hosts, {'command': 'hostname'}),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_get_nodes(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [[self.fake_ansible_result]]
        fuel_managment = fuel.FuelManagement(self.conf)
        nodes = fuel_managment.get_nodes()

        ansible_runner_inst.execute.assert_has_calls([
            mock.call([self.master_host], {'command': 'fuel node --json'}),
        ])

        self.assertEqual(nodes.hosts, self.hosts)

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_get_nodes_from_discover_driver(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        hosts = [
            node_collection.Host(ip='10.0.2.2', mac='09:7b:74:90:63:c2',
                                 fqdn='mynode1.local'),
            node_collection.Host(ip='10.0.2.3', mac='09:7b:74:90:63:c3',
                                 fqdn='mynode2.local'),
        ]
        node_discover_driver = mock.Mock()
        node_discover_driver.discover_hosts.return_value = hosts
        fuel_managment = fuel.FuelManagement(self.conf)
        fuel_managment.set_node_discover(node_discover_driver)
        nodes = fuel_managment.get_nodes()

        self.assertFalse(ansible_runner_inst.execute.called)
        self.assertEqual(hosts, nodes.hosts)

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_execute_on_cloud(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [fakes.FakeAnsibleResult(payload={'stdout': ''}),
             fakes.FakeAnsibleResult(payload={'stdout': ''})]
        ]
        fuel_managment = fuel.FuelManagement(self.conf)
        nodes = fuel_managment.get_nodes()
        result = fuel_managment.execute_on_cloud(
            nodes.hosts, {'command': 'mycmd'}, raise_on_error=False)

        ansible_runner_inst.execute.assert_has_calls([
            mock.call([self.master_host], {'command': 'fuel node --json'}),
            mock.call(self.hosts, {'command': 'mycmd'}, []),
        ])

        self.assertEqual(result,
                         [fakes.FakeAnsibleResult(payload={'stdout': ''}),
                          fakes.FakeAnsibleResult(payload={'stdout': ''})])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_get_nodes_fqdns(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [[self.fake_ansible_result]]
        fuel_managment = fuel.FuelManagement(self.conf)
        nodes = fuel_managment.get_nodes(fqdns=['node-3'])

        hosts = [
            node_collection.Host(ip='10.0.0.3', mac='03', fqdn='node-3'),
        ]
        self.assertEqual(nodes.hosts, hosts)

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(*fuel.FuelManagement.SERVICES.keys())
    def test_get_service_nodes(self, service_name, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     status=executor.STATUS_FAILED,
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')]
        ]

        fuel_managment = fuel.FuelManagement(self.conf)

        service = fuel_managment.get_service(service_name)

        nodes = service.get_nodes()
        cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service.grep)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call([self.master_host], {'command': 'fuel node --json'}),
            mock.call(self.hosts, {'command': cmd}, []),
        ])

        self.assertEqual(nodes.hosts, [self.hosts[1]])

    def test_get_unknown_service(self):
        fuel_managment = fuel.FuelManagement(self.conf)
        self.assertRaises(error.ServiceError,
                          fuel_managment.get_service, 'unknown')

    def test_validate_services(self):
        fuel_managment = fuel.FuelManagement(self.conf)
        fuel_managment.validate_services()
