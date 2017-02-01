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
from os_faults.api import node_collection
from os_faults.drivers import tcpcloud
from os_faults.tests.unit import fakes
from os_faults.tests.unit import test


@ddt.ddt
class TCPCloudManagementTestCase(test.TestCase):

    def setUp(self):
        super(TCPCloudManagementTestCase, self).setUp()
        self.fake_ansible_result = fakes.FakeAnsibleResult(
            payload={
                'stdout': 'cmp01.mk20.local:\n'
                          '  eth1:\n'
                          '    hwaddr: 09:7b:74:90:63:c2\n'
                          '    inet:\n'
                          '    - address: 10.0.0.2\n'
                          '  eth2:\n'
                          '    hwaddr: 00:00:00:00:00:02\n'
                          '    inet:\n'
                          '    - address: 192.168.1.2\n'
                          'cmp02.mk20.local:\n'
                          '  eth1:\n'
                          '    hwaddr: 00:00:00:00:00:03\n'
                          '    inet:\n'
                          '    - address: 192.168.1.3\n'
                          '  eth2:\n'
                          '    hwaddr: 09:7b:74:90:63:c3\n'
                          '    inet:\n'
                          '    - address: 10.0.0.3\n'
            })
        self.fake_node_ip_result = fakes.FakeAnsibleResult(
            payload={
                'stdout': 'cmp01.mk20.local:\n'
                          '  10.0.0.2\n'
                          'cmp02.mk20.local:\n'
                          '  10.0.0.3\n'
            })

        self.tcp_conf = {
            'address': 'tcp.local',
            'username': 'root',
        }
        self.get_nodes_cmd = (
            "salt -E '^(?!cfg|mon)' network.interfaces --out=yaml")
        self.get_ips_cmd = ("salt -E '^(?!cfg|mon)' "
                            "pillar.get _param:single_address --out=yaml")

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data((
        dict(address='tcp.local', username='root'),
        (mock.call(become=None, private_key_file=None, remote_user='root',
                   password=None),
         mock.call(become=None, jump_host='tcp.local', jump_user='root',
                   private_key_file=None, remote_user='root',
                   password=None))
    ), (
        dict(address='tcp.local', username='ubuntu',
             slave_username='root', master_sudo=True,
             private_key_file='/path/id_rsa'),
        (mock.call(become=True, private_key_file='/path/id_rsa',
                   remote_user='ubuntu', password=None),
         mock.call(become=None, jump_host='tcp.local', jump_user='ubuntu',
                   private_key_file='/path/id_rsa', remote_user='root',
                   password=None))
    ), (
        dict(address='tcp.local', username='ubuntu',
             slave_username='root', slave_sudo=True,
             private_key_file='/path/id_rsa'),
        (mock.call(become=None, private_key_file='/path/id_rsa',
                   remote_user='ubuntu', password=None),
         mock.call(become=True, jump_host='tcp.local', jump_user='ubuntu',
                   private_key_file='/path/id_rsa', remote_user='root',
                   password=None))
    ), (
        dict(address='tcp.local', username='ubuntu',
             slave_username='root', slave_sudo=True,
             private_key_file='/path/id_rsa',
             slave_direct_ssh=True),
        (mock.call(become=None, private_key_file='/path/id_rsa',
                   remote_user='ubuntu', password=None),
         mock.call(become=True, jump_host=None, jump_user=None,
                   private_key_file='/path/id_rsa', remote_user='root',
                   password=None))
    ), (
        dict(address='tcp.local', username='root', password='root_pass'),
        (mock.call(become=None, private_key_file=None, remote_user='root',
                   password='root_pass'),
         mock.call(become=None, jump_host='tcp.local', jump_user='root',
                   private_key_file=None, remote_user='root',
                   password='root_pass'))
    ), (
        dict(address='tcp.local', username='root',
             slave_password='slave_pass'),
        (mock.call(become=None, private_key_file=None, remote_user='root',
                   password=None),
         mock.call(become=None, jump_host='tcp.local', jump_user='root',
                   private_key_file=None, remote_user='root',
                   password='slave_pass'))
    ))
    @ddt.unpack
    def test_init(self, config, expected_runner_calls, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value

        tcp_managment = tcpcloud.TCPCloudManagement(config)

        mock_ansible_runner.assert_has_calls(expected_runner_calls)
        self.assertIs(tcp_managment.master_node_executor, ansible_runner_inst)
        self.assertIs(tcp_managment.cloud_executor, ansible_runner_inst)

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_verify(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [self.fake_node_ip_result],
            [fakes.FakeAnsibleResult(payload={'stdout': ''}),
             fakes.FakeAnsibleResult(payload={'stdout': ''})],
        ]
        self.tcp_conf['slave_name_regexp'] = '(ctl*|cmp*)'
        tcp_managment = tcpcloud.TCPCloudManagement(self.tcp_conf)
        tcp_managment.verify()

        get_nodes_cmd = "salt -E '(ctl*|cmp*)' network.interfaces --out=yaml"
        get_ips_cmd = ("salt -E '(ctl*|cmp*)' "
                       "pillar.get _param:single_address --out=yaml")
        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['tcp.local'], {'command': get_nodes_cmd}),
            mock.call(['tcp.local'], {'command': get_ips_cmd}),
            mock.call(['10.0.0.2', '10.0.0.3'], {'command': 'hostname'}),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_get_nodes(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [self.fake_node_ip_result],
        ]
        tcp_managment = tcpcloud.TCPCloudManagement(self.tcp_conf)
        nodes = tcp_managment.get_nodes()

        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['tcp.local'], {'command': self.get_nodes_cmd}),
            mock.call(['tcp.local'], {'command': self.get_ips_cmd}),
        ])

        hosts = [
            node_collection.Host(ip='10.0.0.2', mac='09:7b:74:90:63:c2',
                                 fqdn='cmp01.mk20.local'),
            node_collection.Host(ip='10.0.0.3', mac='09:7b:74:90:63:c3',
                                 fqdn='cmp02.mk20.local'),
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
        tcp_managment = tcpcloud.TCPCloudManagement(self.tcp_conf)
        tcp_managment.set_node_discover(node_discover_driver)
        nodes = tcp_managment.get_nodes()

        self.assertFalse(ansible_runner_inst.execute.called)
        self.assertEqual(hosts, nodes.hosts)

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_execute_on_cloud(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [self.fake_node_ip_result],
            [fakes.FakeAnsibleResult(payload={'stdout': ''}),
             fakes.FakeAnsibleResult(payload={'stdout': ''})]
        ]
        tcp_managment = tcpcloud.TCPCloudManagement(self.tcp_conf)
        nodes = tcp_managment.get_nodes()
        result = tcp_managment.execute_on_cloud(
            nodes.get_ips(), {'command': 'mycmd'}, raise_on_error=False)

        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['tcp.local'], {'command': self.get_nodes_cmd}),
            mock.call(['tcp.local'], {'command': self.get_ips_cmd}),
            mock.call(['10.0.0.2', '10.0.0.3'], {'command': 'mycmd'}, []),
        ])

        self.assertEqual(result,
                         [fakes.FakeAnsibleResult(payload={'stdout': ''}),
                          fakes.FakeAnsibleResult(payload={'stdout': ''})])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    def test_get_nodes_fqdns(self, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [self.fake_node_ip_result],
        ]
        tcp_managment = tcpcloud.TCPCloudManagement(self.tcp_conf)
        nodes = tcp_managment.get_nodes(fqdns=['cmp02.mk20.local'])

        hosts = [
            node_collection.Host(ip='10.0.0.3', mac='09:7b:74:90:63:c3',
                                 fqdn='cmp02.mk20.local'),
        ]
        self.assertEqual(nodes.hosts, hosts)

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(*tcpcloud.TCPCloudManagement.SERVICE_NAME_TO_CLASS.items())
    @ddt.unpack
    def test_get_service_nodes(self, service_name, service_cls,
                               mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [self.fake_node_ip_result],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     status=executor.STATUS_FAILED,
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')]
        ]

        tcp_managment = tcpcloud.TCPCloudManagement(self.tcp_conf)

        service = tcp_managment.get_service(service_name)
        self.assertIsInstance(service, service_cls)

        nodes = service.get_nodes()
        cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service_cls.GREP)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['tcp.local'], {'command': self.get_nodes_cmd}),
            mock.call(['tcp.local'], {'command': self.get_ips_cmd}),
            mock.call(['10.0.0.2', '10.0.0.3'],
                      {'command': cmd}, []),
        ])

        hosts = [
            node_collection.Host(ip='10.0.0.3', mac='09:7b:74:90:63:c3',
                                 fqdn='cmp02.mk20.local'),
        ]
        self.assertEqual(nodes.hosts, hosts)


@ddt.ddt
class TcpServiceTestCase(test.TestCase):

    def setUp(self):
        super(TcpServiceTestCase, self).setUp()
        self.fake_ansible_result = fakes.FakeAnsibleResult(
            payload={
                'stdout': 'cmp01.mk20.local:\n'
                          '  eth0:\n'
                          '    hwaddr: 09:7b:74:90:63:c2\n'
                          '    inet:\n'
                          '    - address: 10.0.0.2\n'
                          'cmp02.mk20.local:\n'
                          '  eth0:\n'
                          '    hwaddr: 09:7b:74:90:63:c3\n'
                          '    inet:\n'
                          '    - address: 10.0.0.3\n'
            })
        self.fake_node_ip_result = fakes.FakeAnsibleResult(
            payload={
                'stdout': 'cmp01.mk20.local:\n'
                          '  10.0.0.2\n'
                          'cmp02.mk20.local:\n'
                          '  10.0.0.3\n'
            })

        self.tcp_conf = {
            'address': 'tcp.local',
            'username': 'root',
        }
        self.get_nodes_cmd = (
            "salt -E '^(?!cfg|mon)' network.interfaces --out=yaml")
        self.get_ips_cmd = ("salt -E '^(?!cfg|mon)' "
                            "pillar.get _param:single_address --out=yaml")

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(*tcpcloud.TCPCloudManagement.SERVICE_NAME_TO_CLASS.items())
    @ddt.unpack
    def test_restart(self, service_name, service_cls, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [self.fake_node_ip_result],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     status=executor.STATUS_FAILED,
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')]
        ]

        tcp_managment = tcpcloud.TCPCloudManagement(self.tcp_conf)

        service = tcp_managment.get_service(service_name)
        self.assertIsInstance(service, service_cls)

        service.restart()

        cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service_cls.GREP)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['tcp.local'], {'command': self.get_nodes_cmd}),
            mock.call(['tcp.local'], {'command': self.get_ips_cmd}),
            mock.call(['10.0.0.2', '10.0.0.3'],
                      {'command': cmd}, []),
            mock.call(['10.0.0.3'], {'shell': service.RESTART_CMD}),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(*tcpcloud.TCPCloudManagement.SERVICE_NAME_TO_CLASS.items())
    @ddt.unpack
    def test_terminate(self, service_name, service_cls, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [self.fake_node_ip_result],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     status=executor.STATUS_FAILED,
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')]
        ]

        tcp_managment = tcpcloud.TCPCloudManagement(self.tcp_conf)

        service = tcp_managment.get_service(service_name)
        self.assertIsInstance(service, service_cls)

        service.terminate()

        cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service_cls.GREP)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['tcp.local'], {'command': self.get_nodes_cmd}),
            mock.call(['tcp.local'], {'command': self.get_ips_cmd}),
            mock.call(['10.0.0.2', '10.0.0.3'],
                      {'command': cmd}, []),
            mock.call(['10.0.0.3'], {'shell': service.TERMINATE_CMD}),
        ])

    @mock.patch('os_faults.ansible.executor.AnsibleRunner', autospec=True)
    @ddt.data(*tcpcloud.TCPCloudManagement.SERVICE_NAME_TO_CLASS.items())
    @ddt.unpack
    def test_start(self, service_name, service_cls, mock_ansible_runner):
        ansible_runner_inst = mock_ansible_runner.return_value
        ansible_runner_inst.execute.side_effect = [
            [self.fake_ansible_result],
            [self.fake_node_ip_result],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     status=executor.STATUS_FAILED,
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')],
            [fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.2'),
             fakes.FakeAnsibleResult(payload={'stdout': ''},
                                     host='10.0.0.3')]
        ]

        tcp_managment = tcpcloud.TCPCloudManagement(self.tcp_conf)

        service = tcp_managment.get_service(service_name)
        self.assertIsInstance(service, service_cls)

        service.start()

        cmd = 'bash -c "ps ax | grep -v grep | grep \'{}\'"'.format(
            service_cls.GREP)
        ansible_runner_inst.execute.assert_has_calls([
            mock.call(['tcp.local'], {'command': self.get_nodes_cmd}),
            mock.call(['tcp.local'], {'command': self.get_ips_cmd}),
            mock.call(['10.0.0.2', '10.0.0.3'],
                      {'command': cmd}, []),
            mock.call(['10.0.0.3'], {'shell': service.START_CMD}),
        ])
