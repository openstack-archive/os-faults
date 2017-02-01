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
from os_faults.drivers import fuel
from os_faults.tests.unit import fakes
from os_faults.tests.unit import test


@ddt.ddt
class FuelManagementTestCase(test.TestCase):

    def setUp(self):
        super(FuelManagementTestCase, self).setUp()

        self.fake_ansible_result = fakes.FakeAnsibleResult(
            payload={
                'stdout': '[{"ip": "10.0.0.2", "mac": "02", "fqdn": "node-2"},'
                          ' {"ip": "10.0.0.3", "mac": "03", "fqdn": "node-3"}]'
            })

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_verify(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [fakes.FakeAnsibleResult(payload={'stdout': ''}),
             fakes.FakeAnsibleResult(payload={'stdout': ''})],
        ]
        fuel_managment = fuel.FuelManagement({
            'address': 'fuel.local',
            'username': 'root',
        })
        fuel_managment.verify()

        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['fuel.local'], {'command': 'fuel node --json'}),
            mock.call(['10.0.0.2', '10.0.0.3'], {'command': 'hostname'}),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_get_nodes(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [[self.fake_ansible_result]]
        fuel_managment = fuel.FuelManagement({
            'address': 'fuel.local',
            'username': 'root',
        })
        nodes = fuel_managment.get_nodes()

        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['fuel.local'], {'command': 'fuel node --json'}),
        ])

        hosts = [
            node_collection.Host(ip='10.0.0.2', mac='02', fqdn='node-2'),
            node_collection.Host(ip='10.0.0.3', mac='03', fqdn='node-3'),
        ]
        self.assertEqual(nodes.hosts, hosts)

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
        fuel_managment = fuel.FuelManagement({
            'address': 'fuel.local',
            'username': 'root',
        })
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
        fuel_managment = fuel.FuelManagement({
            'address': 'fuel.local',
            'username': 'root',
        })
        nodes = fuel_managment.get_nodes()
        result = fuel_managment.execute_on_cloud(
            nodes.get_ips(), {'command': 'mycmd'}, raise_on_error=False)

        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['fuel.local'], {'command': 'fuel node --json'}),
            mock.call(['10.0.0.2', '10.0.0.3'], {'command': 'mycmd'}, []),
        ])

        self.assertEqual(result,
                         [fakes.FakeAnsibleResult(payload={'stdout': ''}),
                          fakes.FakeAnsibleResult(payload={'stdout': ''})])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_get_nodes_fqdns(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [[self.fake_ansible_result]]
        fuel_managment = fuel.FuelManagement({
            'address': 'fuel.local',
            'username': 'root',
        })
        nodes = fuel_managment.get_nodes(fqdns=['node-3'])

        hosts = [
            node_collection.Host(ip='10.0.0.3', mac='03', fqdn='node-3'),
        ]
        self.assertEqual(nodes.hosts, hosts)

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(*fuel.FuelManagement.SERVICE_NAME_TO_CLASS.items())
    @ddt.unpack
    def test_get_service_nodes(self, service_name, service_cls,
                               mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     status=executor.STATUS_FAILED,
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')]
        ]

        fuel_managment = fuel.FuelManagement({
            'address': 'fuel.local',
            'username': 'root',
        })

        service = fuel_managment.get_service(service_name)
        self.assertIsInstance(service, service_cls)

        nodes = service.get_nodes()
        cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service_cls.GREP)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['fuel.local'], {'command': 'fuel node --json'}),
            mock.call(['10.0.0.2', '10.0.0.3'],
                      {'command': cmd}, []),
        ])

        hosts = [
            node_collection.Host(ip='10.0.0.3', mac='03', fqdn='node-3'),
        ]
        self.assertEqual(nodes.hosts, hosts)

    def test_get_unknown_service(self):
        fuel_managment = fuel.FuelManagement({
            'address': 'fuel.local',
            'username': 'root',
        })
        self.assertRaises(error.ServiceError,
                          fuel_managment.get_service, 'unknown')
