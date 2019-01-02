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

import copy
import ddt
import mock

from os_faults.api import node_collection
from os_faults.drivers.cloud import devstack
from os_faults.tests.unit import fakes
from os_faults.tests.unit import test


class DevStackNodeTestCase(test.TestCase):

    def setUp(self):
        super(DevStackNodeTestCase, self).setUp()
        self.mock_cloud_management = mock.Mock(
            spec=devstack.DevStackCloudManagement)
        self.host = node_collection.Host(
            ip='10.0.0.2', mac='09:7b:74:90:63:c1', fqdn='')

        self.node_collection = devstack.DevStackNodeCollection(
            cloud_management=self.mock_cloud_management,
            hosts=[copy.deepcopy(self.host)])

    def test_connect(self):
        pass

    def test_disconnect(self):
        pass


@ddt.ddt
class DevStackManagementTestCase(test.TestCase):

    def setUp(self):
        super(DevStackManagementTestCase, self).setUp()
        self.conf = {'address': '10.0.0.2', 'auth': {'username': 'root'}}
        self.host = node_collection.Host('10.0.0.2')
        self.discoverd_host = node_collection.Host(ip='10.0.0.2',
                                                   mac='09:7b:74:90:63:c1',
                                                   fqdn='')

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_verify(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [fakes.FakeAnsibleResult(payload={'stdout': '09:7b:74:90:63:c1'},
                                     host='10.0.0.2')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2')],
        ]
        devstack_management = devstack.DevStackCloudManagement(self.conf)
        devstack_management.verify()

        ansible_runner_inst.execute.assert_has_calls([
            mock.call([self.host],
                      {'command': 'cat /sys/class/net/eth0/address'}),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_execute_on_cloud(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [fakes.FakeAnsibleResult(payload={'stdout': '/root'})],
        ]
        devstack_management = devstack.DevStackCloudManagement(self.conf)
        result = devstack_management.execute_on_cloud(
            ['10.0.0.2'], {'command': 'pwd'})

        ansible_runner_inst.execute.assert_called_once_with(
            ['10.0.0.2'], {'command': 'pwd'})
        self.assertEqual(
            [fakes.FakeAnsibleResult(payload={'stdout': '/root'})], result)

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_get_nodes(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [fakes.FakeAnsibleResult(payload={'stdout': '09:7b:74:90:63:c1'},
                                     host='10.0.0.2')],
        ]

        devstack_management = devstack.DevStackCloudManagement(self.conf)
        nodes = devstack_management.get_nodes()
        ansible_runner_inst.execute.assert_called_once_with(
            [self.host], {'command': 'cat /sys/class/net/eth0/address'})

        self.assertIsInstance(nodes, devstack.DevStackNodeCollection)
        self.assertEqual(
            [node_collection.Host(ip='10.0.0.2', mac='09:7b:74:90:63:c1',
                                  fqdn='')],
            nodes.hosts)

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(*devstack.DevStackCloudManagement.SERVICES.keys())
    def test_get_service_nodes(self, service_name, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [fakes.FakeAnsibleResult(payload={'stdout': '09:7b:74:90:63:c1'},
                                     host='10.0.0.2')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''}, host='10.0.0.2')]
        ]

        devstack_management = devstack.DevStackCloudManagement(self.conf)

        service = devstack_management.get_service(service_name)
        nodes = service.get_nodes()

        cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service.grep)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call(
                [self.host], {'command': 'cat /sys/class/net/eth0/address'}),
            mock.call([self.discoverd_host], {'command': cmd}, [])
        ])
        self.assertEqual(
            [node_collection.Host(ip='10.0.0.2', mac='09:7b:74:90:63:c1',
                                  fqdn='')],
            nodes.hosts)

    @mock.patch('os_faults.ansible.executor.AnsibleRunner')
    def test_validate_services(self, _):
        devstack_management = devstack.DevStackCloudManagement(self.conf)
        devstack_management.validate_services()


@ddt.ddt
class DevStackServiceTestCase(test.TestCase):

    def setUp(self):
        super(DevStackServiceTestCase, self).setUp()
        self.conf = {'address': '10.0.0.2', 'auth': {'username': 'stack'}}
        self.host = node_collection.Host('10.0.0.2')
        self.discoverd_host = node_collection.Host(ip='10.0.0.2',
                                                   mac='09:7b:74:90:63:c1',
                                                   fqdn='')

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(*devstack.DevStackCloudManagement.SERVICES.keys())
    def test_restart(self, service_name, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [fakes.FakeAnsibleResult(payload={'stdout': '09:7b:74:90:63:c1'},
                                     host='10.0.0.2')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''}, host='10.0.0.2')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''}, host='10.0.0.2')]
        ]

        devstack_management = devstack.DevStackCloudManagement(
            self.conf)

        service = devstack_management.get_service(service_name)
        service.restart()

        cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service.grep)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call(
                [self.host], {'command': 'cat /sys/class/net/eth0/address'}),
            mock.call([self.discoverd_host], {'command': cmd}, []),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(*devstack.DevStackCloudManagement.SERVICES.keys())
    def test_terminate(self, service_name, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [fakes.FakeAnsibleResult(payload={'stdout': '09:7b:74:90:63:c1'},
                                     host='10.0.0.2')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''}, host='10.0.0.2')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''}, host='10.0.0.2')]
        ]

        devstack_management = devstack.DevStackCloudManagement(
            self.conf)

        service = devstack_management.get_service(service_name)
        service.terminate()

        cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service.grep)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call(
                [self.host], {'command': 'cat /sys/class/net/eth0/address'}),
            mock.call([self.discoverd_host], {'command': cmd}, []),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(*devstack.DevStackCloudManagement.SERVICES.keys())
    def test_start(self, service_name, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [fakes.FakeAnsibleResult(payload={'stdout': '09:7b:74:90:63:c1'},
                                     host='10.0.0.2')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''}, host='10.0.0.2')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''}, host='10.0.0.2')]
        ]

        devstack_management = devstack.DevStackCloudManagement(
            self.conf)

        service = devstack_management.get_service(service_name)
        service.start()

        cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service.grep)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call(
                [self.host], {'command': 'cat /sys/class/net/eth0/address'}),
            mock.call([self.discoverd_host], {'command': cmd}, []),
        ])
