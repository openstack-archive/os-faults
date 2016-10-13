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

from os_faults.api import power_management
from os_faults.drivers import devstack
from os_faults.tests.unit import fakes
from os_faults.tests.unit import test


class DevStackNodeTestCase(test.TestCase):

    def setUp(self):
        super(DevStackNodeTestCase, self).setUp()
        self.mock_cloud_management = mock.Mock(
            spec=devstack.DevStackManagement)
        self.mock_power_management = mock.Mock(
            spec=power_management.PowerManagement)
        self.host = devstack.HostClass(ip='10.0.0.2', mac='09:7b:74:90:63:c1')

        self.node_collection = devstack.DevStackNode(
            cloud_management=self.mock_cloud_management,
            power_management=self.mock_power_management,
            host=copy.deepcopy(self.host))

    def test_len(self):
        self.assertEqual(1, len(self.node_collection))

    def test_pick(self):
        self.assertIs(self.node_collection, self.node_collection.pick())

    def test_run_task(self):
        self.node_collection.run_task({'foo': 'bar'})
        self.mock_cloud_management.execute.assert_called_once_with(
            '10.0.0.2', {'foo': 'bar'})

    def test_reboot(self):
        self.node_collection.reboot()
        self.mock_cloud_management.execute.assert_called_once_with(
            '10.0.0.2', {'command': 'reboot'})

    def test_poweroff(self):
        self.node_collection.poweroff()
        self.mock_power_management.poweroff.assert_called_once_with(
            ['09:7b:74:90:63:c1'])

    def test_poweron(self):
        self.node_collection.poweron()
        self.mock_power_management.poweron.assert_called_once_with(
            ['09:7b:74:90:63:c1'])

    def test_reset(self):
        self.node_collection.reset()
        self.mock_power_management.reset.assert_called_once_with(
            ['09:7b:74:90:63:c1'])


@ddt.ddt
class DevStackManagementTestCase(test.TestCase):

    def setUp(self):
        super(DevStackManagementTestCase, self).setUp()
        self.conf = {'address': '10.0.0.2', 'username': 'root'}

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_verify(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [fakes.FakeAnsibleResult(payload={'stdout': 'node1.com'})],
        ]
        devstack_management = devstack.DevStackManagement(self.conf)
        devstack_management.verify()

        ansible_runner_inst.execute.assert_called_once_with(
            ['10.0.0.2'], {'command': 'hostname'})

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_execute(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [fakes.FakeAnsibleResult(payload={'stdout': '/root'})],
        ]
        devstack_management = devstack.DevStackManagement(self.conf)
        result = devstack_management.execute({'command': 'pwd'})

        ansible_runner_inst.execute.assert_called_once_with(
            ['10.0.0.2'], {'command': 'pwd'})
        self.assertEqual(
            [fakes.FakeAnsibleResult(payload={'stdout': '/root'})], result)

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_get_nodes(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [fakes.FakeAnsibleResult(payload={'stdout': '09:7b:74:90:63:c1'})],
        ]

        devstack_management = devstack.DevStackManagement(self.conf)
        nodes = devstack_management.get_nodes()

        ansible_runner_inst.execute.assert_called_once_with(
            ['10.0.0.2'], {'command': 'cat /sys/class/net/eth0/address'})

        self.assertIsInstance(nodes, devstack.DevStackNode)
        self.assertEqual(
            devstack.HostClass(ip='10.0.0.2', mac='09:7b:74:90:63:c1'),
            nodes.host)

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(('keystone', devstack.KeystoneService))
    @ddt.unpack
    def test_get_service_nodes(self, service_name, service_cls,
                               mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [fakes.FakeAnsibleResult(payload={'stdout': '09:7b:74:90:63:c1'})]
        ]

        devstack_management = devstack.DevStackManagement(self.conf)

        service = devstack_management.get_service(service_name)
        self.assertIsInstance(service, service_cls)

        nodes = service.get_nodes()
        ansible_runner_inst.execute.assert_called_once_with(
            ['10.0.0.2'], {'command': 'cat /sys/class/net/eth0/address'})
        self.assertEqual(
            devstack.HostClass(ip='10.0.0.2', mac='09:7b:74:90:63:c1'),
            nodes.host)


@ddt.ddt
class DevStackServiceTestCase(test.TestCase):

    def setUp(self):
        super(DevStackServiceTestCase, self).setUp()
        self.conf = {'address': '10.0.0.2', 'username': 'root'}

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(('keystone', devstack.KeystoneService))
    @ddt.unpack
    def test_restart(self, service_name, service_cls, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [fakes.FakeAnsibleResult(payload={'stdout': '09:7b:74:90:63:c1'})],
            [fakes.FakeAnsibleResult(payload={'stdout': ''}, host='10.0.0.2')]
        ]

        devstack_management = devstack.DevStackManagement(self.conf)

        service = devstack_management.get_service(service_name)
        self.assertIsInstance(service, service_cls)

        service.restart()
        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['10.0.0.2'],
                      {'command': service_cls.RESTART_CMD}),
        ])
