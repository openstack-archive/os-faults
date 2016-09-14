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
from os_faults.drivers import fuel
from os_faults.tests import fake
from os_faults.tests import test


@ddt.ddt
class FuelManagementTestCase(test.TestCase):

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_verify(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [fake.FakeAsnibleResult(payload={
                'stdout': '[{"ip": "10.0.0.2"}, {"ip": "10.0.0.3"}]',
            })],
            [fake.FakeAsnibleResult(payload={'stdout': ''}),
             fake.FakeAsnibleResult(payload={'stdout': ''})],
        ]
        fuel_managment = fuel.FuelManagement({
            'address': 'fuel.local',
            'username': 'root',
        })
        fuel_managment.verify()

        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['fuel.local'], {'command': 'fuel2 node list -f json'}),
            mock.call(['10.0.0.2', '10.0.0.3'], {'command': 'hostname'}),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_get_nodes(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [fake.FakeAsnibleResult(payload={
                'stdout': '[{"ip": "10.0.0.2"}, {"ip": "10.0.0.3"}]',
            })],
        ]
        fuel_managment = fuel.FuelManagement({
            'address': 'fuel.local',
            'username': 'root',
        })
        nodes = fuel_managment.get_nodes()

        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['fuel.local'], {'command': 'fuel2 node list -f json'}),
        ])

        self.assertEqual(nodes.hosts, [{'ip': '10.0.0.2'},
                                       {'ip': '10.0.0.3'}])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_execute_on_cloud(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [fake.FakeAsnibleResult(payload={
                'stdout': '[{"ip": "10.0.0.2"}, {"ip": "10.0.0.3"}]',
            })],
            [fake.FakeAsnibleResult(payload={'stdout': ''}),
             fake.FakeAsnibleResult(payload={'stdout': ''})]
        ]
        fuel_managment = fuel.FuelManagement({
            'address': 'fuel.local',
            'username': 'root',
        })
        nodes = fuel_managment.get_nodes()
        result = fuel_managment.execute_on_cloud(
            nodes.get_ips(), {'command': 'mycmd'}, raise_on_error=False)

        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['fuel.local'], {'command': 'fuel2 node list -f json'}),
            mock.call(['10.0.0.2', '10.0.0.3'], {'command': 'mycmd'}, []),
        ])

        self.assertEqual(
            result,
            [fake.FakeAsnibleResult(payload={'stdout': ''}),
             fake.FakeAsnibleResult(payload={'stdout': ''})])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_get_nodes_fqdns(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [fake.FakeAsnibleResult(payload={
                'stdout': ('[{"ip": "10.0.0.2", "id": 1}, '
                           '{"ip": "10.0.0.3", "id": 2}]'),
            })],
            [fake.FakeAsnibleResult(payload={
                'stdout': '{"fqdn": "node1.com", "ip": "10.0.0.2"}',
            })],
            [fake.FakeAsnibleResult(payload={
                'stdout': '{"fqdn": "node2.com", "ip": "10.0.0.3"}',
            })],
        ]
        fuel_managment = fuel.FuelManagement({
            'address': 'fuel.local',
            'username': 'root',
        })
        nodes = fuel_managment.get_nodes(fqdns=['node2.com'])

        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['fuel.local'],
                      {'command': 'fuel2 node list -f json'}),
            mock.call(['fuel.local'],
                      {'command': 'fuel2 node show 1 -f json'}),
            mock.call(['fuel.local'],
                      {'command': 'fuel2 node show 2 -f json'}),
        ])

        self.assertEqual(nodes.hosts, [{'ip': '10.0.0.3', 'id': 2}])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(('keystone', fuel.KeystoneService),
              ('mysql', fuel.MySQLService),
              ('rabbitmq', fuel.RabbitMQService),
              ('nova-api', fuel.NovaAPIService),
              ('glance-api', fuel.GlanceAPIService),
              ('memcached', fuel.MemcachedService))
    @ddt.unpack
    def test_get_service_nodes(self, service_name, service_cls,
                               mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [fake.FakeAsnibleResult(payload={
                'stdout': '[{"ip": "10.0.0.2"}, {"ip": "10.0.0.3"}]',
            })],
            [fake.FakeAsnibleResult(payload={'stdout': ''},
                                    status=executor.STATUS_FAILED,
                                    host='10.0.0.2'),
             fake.FakeAsnibleResult(payload={'stdout': ''},
                                    host='10.0.0.3')]
        ]

        fuel_managment = fuel.FuelManagement({
            'address': 'fuel.local',
            'username': 'root',
        })

        service = fuel_managment.get_service(service_name)
        self.assertIsInstance(service, service_cls)

        nodes = service.get_nodes()
        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['fuel.local'], {'command': 'fuel2 node list -f json'}),
            mock.call(['10.0.0.2', '10.0.0.3'],
                      {'command': service_cls.GET_NODES_CMD}, []),
        ])
        self.assertEqual(nodes.hosts, [{'ip': '10.0.0.3'}])
