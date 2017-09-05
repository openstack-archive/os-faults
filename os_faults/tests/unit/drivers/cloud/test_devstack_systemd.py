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
from os_faults.drivers.cloud import devstack_systemd
from os_faults.tests.unit.drivers.cloud import test_devstack
from os_faults.tests.unit import fakes
from os_faults.tests.unit import test


@ddt.ddt
class DevStackSystemdManagementTestCase(
        test_devstack.DevStackManagementTestCase):

    def setUp(self):
        super(DevStackSystemdManagementTestCase, self).setUp()


@ddt.ddt
class DevStackSystemdServiceTestCase(test.TestCase):

    def setUp(self):
        super(DevStackSystemdServiceTestCase, self).setUp()
        self.conf = {'address': '10.0.0.2', 'username': 'root'}
        self.host = node_collection.Host('10.0.0.2')
        self.discoverd_host = node_collection.Host(ip='10.0.0.2',
                                                   mac='09:7b:74:90:63:c1',
                                                   fqdn='')

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(*devstack_systemd.DevStackSystemdManagement.SERVICES.keys())
    def test_restart(self, service_name, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [fakes.FakeAnsibleResult(payload={'stdout': '09:7b:74:90:63:c1'},
                                     host='10.0.0.2')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''}, host='10.0.0.2')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''}, host='10.0.0.2')]
        ]

        devstack_management = devstack_systemd.DevStackSystemdManagement(
            self.conf)

        service = devstack_management.get_service(service_name)
        service.restart()

        cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service.grep)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call(
                [self.host], {'command': 'cat /sys/class/net/eth0/address'}),
            mock.call([self.discoverd_host], {'command': cmd}, []),
            mock.call([self.discoverd_host], {'shell': service.restart_cmd})
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(*devstack_systemd.DevStackSystemdManagement.SERVICES.keys())
    def test_terminate(self, service_name, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [fakes.FakeAnsibleResult(payload={'stdout': '09:7b:74:90:63:c1'},
                                     host='10.0.0.2')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''}, host='10.0.0.2')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''}, host='10.0.0.2')]
        ]

        devstack_management = devstack_systemd.DevStackSystemdManagement(
            self.conf)

        service = devstack_management.get_service(service_name)
        service.terminate()

        cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service.grep)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call(
                [self.host], {'command': 'cat /sys/class/net/eth0/address'}),
            mock.call([self.discoverd_host], {'command': cmd}, []),
            mock.call([self.discoverd_host], {'shell': service.terminate_cmd})
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(*devstack_systemd.DevStackSystemdManagement.SERVICES.keys())
    def test_start(self, service_name, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [fakes.FakeAnsibleResult(payload={'stdout': '09:7b:74:90:63:c1'},
                                     host='10.0.0.2')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''}, host='10.0.0.2')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''}, host='10.0.0.2')]
        ]

        devstack_management = devstack_systemd.DevStackSystemdManagement(
            self.conf)

        service = devstack_management.get_service(service_name)
        service.start()

        cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service.grep)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call(
                [self.host], {'command': 'cat /sys/class/net/eth0/address'}),
            mock.call([self.discoverd_host], {'command': cmd}, []),
            mock.call([self.discoverd_host], {'shell': service.start_cmd})
        ])
