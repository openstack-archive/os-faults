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

from os_faults.drivers import fuel
from os_faults.tests import fake
from os_faults.tests import test


@ddt.ddt
class FuelServiceTestCase(test.TestCase):

    def setUp(self):
        super(FuelServiceTestCase, self).setUp()

        self.fake_ansible_result = fake.FakeAnsibleResult(
            payload={'stdout': '[{"ip": "10.0.0.2", "mac": "02", '
                               '"fqdn": "node2.com"}, '
                               '{"ip": "10.0.0.3", "mac": "03", '
                               '"fqdn": "node3.com"}]'})

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(('keystone', fuel.KeystoneService),
              ('mysql', fuel.MySQLService),
              ('rabbitmq', fuel.RabbitMQService),
              ('nova-api', fuel.NovaAPIService),
              ('glance-api', fuel.GlanceAPIService))
    @ddt.unpack
    def test_kill(self, service_name, service_cls, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.2'),
             fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.3')],
            [fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.2'),
             fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.3')]
        ]

        fuel_managment = fuel.FuelManagement({
            'address': 'fuel.local',
            'username': 'root',
        })

        service = fuel_managment.get_service(service_name)
        self.assertIsInstance(service, service_cls)

        service.kill()
        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['fuel.local'], {'command': 'fuel node --json'}),
            mock.call(['10.0.0.2', '10.0.0.3'],
                      {'command': service_cls.GET_NODES_CMD}, []),
            mock.call(['10.0.0.2', '10.0.0.3'],
                      {'command': service_cls.KILL_CMD}),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(('keystone', fuel.KeystoneService),
              ('mysql', fuel.MySQLService),
              ('rabbitmq', fuel.RabbitMQService),
              ('nova-api', fuel.NovaAPIService),
              ('glance-api', fuel.GlanceAPIService))
    @ddt.unpack
    def test_freeze(self, service_name, service_cls, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.2'),
             fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.3')],
            [fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.2'),
             fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.3')]
        ]

        fuel_managment = fuel.FuelManagement({
            'address': 'fuel.local',
            'username': 'root',
        })

        service = fuel_managment.get_service(service_name)
        self.assertIsInstance(service, service_cls)

        service.freeze()
        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['fuel.local'], {'command': 'fuel node --json'}),
            mock.call(['10.0.0.2', '10.0.0.3'],
                      {'command': service_cls.GET_NODES_CMD}, []),
            mock.call(['10.0.0.2', '10.0.0.3'],
                      {'command': service_cls.FREEZE_CMD}),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(('keystone', fuel.KeystoneService),
              ('mysql', fuel.MySQLService),
              ('rabbitmq', fuel.RabbitMQService),
              ('nova-api', fuel.NovaAPIService),
              ('glance-api', fuel.GlanceAPIService))
    @ddt.unpack
    def test_freeze_sec(self, service_name, service_cls, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.2'),
             fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.3')],
            [fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.2'),
             fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.3')]
        ]

        fuel_managment = fuel.FuelManagement({
            'address': 'fuel.local',
            'username': 'root',
        })

        service = fuel_managment.get_service(service_name)
        self.assertIsInstance(service, service_cls)

        delay_sec = 10
        service.freeze(nodes=None, sec=delay_sec)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['fuel.local'], {'command': 'fuel node --json'}),
            mock.call(['10.0.0.2', '10.0.0.3'],
                      {'command': service_cls.GET_NODES_CMD}, []),
            mock.call(['10.0.0.2', '10.0.0.3'],
                      {'command':
                      service_cls.FREEZE_SEC_CMD.format(delay_sec)}),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(('keystone', fuel.KeystoneService),
              ('mysql', fuel.MySQLService),
              ('rabbitmq', fuel.RabbitMQService),
              ('nova-api', fuel.NovaAPIService),
              ('glance-api', fuel.GlanceAPIService))
    @ddt.unpack
    def test_unfreeze(self, service_name, service_cls, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.2'),
             fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.3')],
            [fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.2'),
             fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.3')]
        ]

        fuel_managment = fuel.FuelManagement({
            'address': 'fuel.local',
            'username': 'root',
        })

        service = fuel_managment.get_service(service_name)
        self.assertIsInstance(service, service_cls)

        service.unfreeze()
        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['fuel.local'], {'command': 'fuel node --json'}),
            mock.call(['10.0.0.2', '10.0.0.3'],
                      {'command': service_cls.GET_NODES_CMD}, []),
            mock.call(['10.0.0.2', '10.0.0.3'],
                      {'command': service_cls.UNFREEZE_CMD}),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(('mysql', fuel.MySQLService))
    @ddt.unpack
    def test_unplug(self, service_name, service_cls, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.2'),
             fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.3')],
            [fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.2'),
             fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.3')]
        ]

        fuel_managment = fuel.FuelManagement({
            'address': 'fuel.local',
            'username': 'root',
        })

        service = fuel_managment.get_service(service_name)
        self.assertIsInstance(service, service_cls)

        service.unplug()
        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['fuel.local'], {'command': 'fuel node --json'}),
            mock.call(['10.0.0.2', '10.0.0.3'],
                      {'command': service_cls.GET_NODES_CMD}, []),
            mock.call(['10.0.0.2', '10.0.0.3'],
                      {'command':
                      service_cls.UNPLUG_CMD.format(service_cls.PORT)}),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(('mysql', fuel.MySQLService))
    @ddt.unpack
    def test_plug(self, service_name, service_cls, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.2'),
             fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.3')],
            [fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.2'),
             fake.FakeAnsibleResult(payload={'stdout': ''},
                                    host='10.0.0.3')]
        ]

        fuel_managment = fuel.FuelManagement({
            'address': 'fuel.local',
            'username': 'root',
        })

        service = fuel_managment.get_service(service_name)
        self.assertIsInstance(service, service_cls)

        service.plug()
        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['fuel.local'], {'command': 'fuel node --json'}),
            mock.call(['10.0.0.2', '10.0.0.3'],
                      {'command': service_cls.GET_NODES_CMD}, []),
            mock.call(['10.0.0.2', '10.0.0.3'],
                      {'command':
                      service_cls.PLUG_CMD.format(service_cls.PORT)}),
        ])
