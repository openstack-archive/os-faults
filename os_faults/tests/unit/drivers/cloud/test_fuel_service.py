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
class FuelServiceTestCase(test.TestCase):

    def setUp(self):
        super(FuelServiceTestCase, self).setUp()
        self.conf = {'address': 'fuel.local', 'username': 'root'}
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
    @ddt.data(*fuel.FuelManagement.SERVICES.keys())
    def test_kill(self, service_name, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')]
        ]

        fuel_managment = fuel.FuelManagement(self.conf)

        service = fuel_managment.get_service(service_name)
        service.kill()

        get_nodes_cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service.grep)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call([self.master_host], {'command': 'fuel node --json'}),
            mock.call(self.hosts, {'command': get_nodes_cmd}, []),
            mock.call(self.hosts, {'kill': {'grep': service.grep, 'sig': 9}}),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(*fuel.FuelManagement.SERVICES.keys())
    def test_freeze(self, service_name, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')]
        ]

        fuel_managment = fuel.FuelManagement(self.conf)

        service = fuel_managment.get_service(service_name)
        service.freeze()

        get_nodes_cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service.grep)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call([self.master_host], {'command': 'fuel node --json'}),
            mock.call(self.hosts, {'command': get_nodes_cmd}, []),
            mock.call(self.hosts, {'kill': {'grep': service.grep, 'sig': 19}}),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(*fuel.FuelManagement.SERVICES.keys())
    def test_freeze_sec(self, service_name, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')]
        ]

        fuel_managment = fuel.FuelManagement(self.conf)

        service = fuel_managment.get_service(service_name)
        delay_sec = 10
        service.freeze(nodes=None, sec=delay_sec)

        get_nodes_cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service.grep)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call([self.master_host], {'command': 'fuel node --json'}),
            mock.call(self.hosts, {'command': get_nodes_cmd}, []),
            mock.call(self.hosts, {'freeze': {'grep': service.grep,
                                              'sec': delay_sec}}),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(*fuel.FuelManagement.SERVICES.keys())
    def test_unfreeze(self, service_name, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')]
        ]

        fuel_managment = fuel.FuelManagement(self.conf)

        service = fuel_managment.get_service(service_name)
        service.unfreeze()

        get_nodes_cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service.grep)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call([self.master_host], {'command': 'fuel node --json'}),
            mock.call(self.hosts, {'command': get_nodes_cmd}, []),
            mock.call(self.hosts, {'kill': {'grep': service.grep, 'sig': 18}}),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data('mysql')
    def test_unplug(self, service_name, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')]
        ]

        fuel_managment = fuel.FuelManagement(self.conf)

        service = fuel_managment.get_service(service_name)
        service.unplug()

        get_nodes_cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service.grep)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call([self.master_host], {'command': 'fuel node --json'}),
            mock.call(self.hosts, {'command': get_nodes_cmd}, []),
            mock.call(self.hosts,
                      {'iptables': {'protocol': service.port[0],
                                    'port': service.port[1],
                                    'action': 'block',
                                    'service': service.service_name}}),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data('mysql')
    def test_plug(self, service_name, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')]
        ]

        fuel_managment = fuel.FuelManagement(self.conf)

        service = fuel_managment.get_service(service_name)
        service.plug()

        get_nodes_cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service.grep)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call([self.master_host], {'command': 'fuel node --json'}),
            mock.call(self.hosts, {'command': get_nodes_cmd}, []),
            mock.call(self.hosts,
                      {'iptables': {'protocol': service.port[0],
                                    'port': service.port[1],
                                    'action': 'unblock',
                                    'service': service.service_name}}),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(*fuel.FuelManagement.SERVICES.keys())
    def test_restart(self, service_name, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')]
        ]

        fuel_managment = fuel.FuelManagement(self.conf)

        service = fuel_managment.get_service(service_name)
        service.restart()

        get_nodes_cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service.grep)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call([self.master_host], {'command': 'fuel node --json'}),
            mock.call(self.hosts, {'command': get_nodes_cmd}, []),
            mock.call(self.hosts, {'shell': service.restart_cmd}),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(*fuel.FuelManagement.SERVICES.keys())
    def test_terminate(self, service_name, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')]
        ]

        fuel_managment = fuel.FuelManagement(self.conf)

        service = fuel_managment.get_service(service_name)
        service.terminate()

        get_nodes_cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service.grep)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call([self.master_host], {'command': 'fuel node --json'}),
            mock.call(self.hosts, {'command': get_nodes_cmd}, []),
            mock.call(self.hosts, {'shell': service.terminate_cmd}),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(*fuel.FuelManagement.SERVICES.keys())
    def test_start(self, service_name, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')]
        ]

        fuel_managment = fuel.FuelManagement(self.conf)

        service = fuel_managment.get_service(service_name)
        service.start()

        get_nodes_cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service.grep)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call([self.master_host], {'command': 'fuel node --json'}),
            mock.call(self.hosts, {'command': get_nodes_cmd}, []),
            mock.call(self.hosts, {'shell': service.start_cmd}),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_run_node_collection_empty(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2',
                                     status=executor.STATUS_FAILED),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3',
                                     status=executor.STATUS_FAILED)],
        ]

        fuel_managment = fuel.FuelManagement(self.conf)

        service = fuel_managment.get_service('keystone')
        exception = self.assertRaises(error.ServiceError, service.restart)
        self.assertEqual('Service keystone is not found on any nodes',
                         str(exception))

        get_nodes_cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service.grep)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call([self.master_host], {'command': 'fuel node --json'}),
            mock.call(self.hosts, {'command': get_nodes_cmd}, []),
        ])
