# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import jsonschema
import mock

import os_faults
from os_faults.ansible import executor
from os_faults.api import cloud_management
from os_faults.api import error
from os_faults.api import node_collection
from os_faults.api import service
from os_faults.drivers.cloud import devstack
from os_faults.drivers.power import libvirt
from os_faults.tests.unit import test


class OSFaultsTestCase(test.TestCase):

    def setUp(self):
        super(OSFaultsTestCase, self).setUp()
        self.cloud_config = {
            'cloud_management': {
                'driver': 'devstack',
                'args': {
                    'address': '10.30.00.5',
                    'auth': {
                        'username': 'root',
                        'private_key_file': '/my/path/pk.key',
                    },
                }
            },
            'power_managements': [{
                'driver': 'libvirt',
                'args': {
                    'connection_uri': "qemu+ssh://user@10.30.20.21/system"
                }
            }]
        }

    @mock.patch('os_faults.ansible.executor.AnsibleRunner')
    def test_connect_devstack(self, _):
        cloud_config = {
            'cloud_management': {
                'driver': 'devstack',
                'args': {
                    'address': 'devstack.local',
                    'auth': {
                        'username': 'developer',
                        'private_key_file': '/my/path/pk.key',
                    },
                }
            }
        }
        destructor = os_faults.connect(cloud_config)
        self.assertIsInstance(destructor, devstack.DevStackCloudManagement)

    @mock.patch('os_faults.ansible.executor.AnsibleRunner')
    def test_config_with_services(self, _):
        self.cloud_config['services'] = {
            'app': {
                'driver': 'process',
                'args': {'grep': 'myapp'}
            }
        }
        destructor = os_faults.connect(self.cloud_config)
        app = destructor.get_service('app')
        self.assertIsNotNone(app)

    @mock.patch('os_faults.ansible.executor.AnsibleRunner')
    def test_config_with_services_and_hosts(self, _):
        self.cloud_config['node_discover'] = {
            'driver': 'node_list',
            'args': [
                {
                    'ip': '10.0.0.11',
                    'mac': '01:ab:cd:01:ab:cd',
                    'fqdn': 'node-1'
                }, {
                    'ip': '10.0.0.12',
                    'mac': '02:ab:cd:02:ab:cd',
                    'fqdn': 'node-2'
                },
            ]
        }
        self.cloud_config['services'] = {
            'app': {
                'driver': 'process',
                'args': {'grep': 'myapp'},
                'hosts': ['10.0.0.11', '10.0.0.12']
            }
        }
        destructor = os_faults.connect(self.cloud_config)
        app = destructor.get_service('app')
        self.assertIsNotNone(app)
        nodes = app.get_nodes()
        self.assertEqual(['10.0.0.11', '10.0.0.12'], nodes.get_ips())
        self.assertEqual(['node-1', 'node-2'], nodes.get_fqdns())
        self.assertEqual(['01:ab:cd:01:ab:cd', '02:ab:cd:02:ab:cd'],
                         nodes.get_macs())

    @mock.patch('os_faults.ansible.executor.AnsibleRunner')
    def test_connect_with_libvirt(self, _):
        destructor = os_faults.connect(self.cloud_config)
        self.assertIsInstance(destructor, devstack.DevStackCloudManagement)
        self.assertEqual(1, len(destructor.power_manager.power_drivers))
        self.assertIsInstance(destructor.power_manager.power_drivers[0],
                              libvirt.LibvirtDriver)

    def test_connect_driver_not_found(self):
        cloud_config = {
            'cloud_management': {
                'driver': 'non-existing',
                'args': {},
            }
        }
        self.assertRaises(
            error.OSFDriverNotFound, os_faults.connect, cloud_config)

    def test_connect_driver_not_specified(self):
        cloud_config = {'foo': 'bar'}
        self.assertRaises(
            jsonschema.ValidationError, os_faults.connect, cloud_config)

    @mock.patch('os.path.exists', return_value=False)
    def test_connect_no_config_files(self, mock_os_path_exists):
        self.assertRaises(error.OSFError, os_faults.connect)

    @mock.patch('os.path.exists', side_effect=lambda x: 'bad' not in x)
    @mock.patch('os.walk', side_effect=lambda x: ([x, [], []],
                                                  [x + 'subdir', [], []]))
    @mock.patch.object(executor, 'MODULE_PATHS', set())
    def test_register_ansible_modules(self, mock_os_walk, mock_os_path_exists):
        os_faults.register_ansible_modules(['/my/path/', '/other/path/'])
        self.assertEqual(executor.get_module_paths(),
                         {'/my/path/', '/my/path/subdir',
                          '/other/path/', '/other/path/subdir'})

        self.assertRaises(error.OSFError, os_faults.register_ansible_modules,
                          ['/my/bad/path/'])

    @mock.patch('os_faults.connect')
    def test_discover(self, mock_connect):
        cloud_config = {
            'cloud_management': {
                'driver': 'devstack',
                'args': {
                    'address': 'devstack.local',
                    'username': 'developer',
                    'private_key_file': '/my/path/pk.key',
                }
            }
        }
        cloud_management_mock = mock.create_autospec(
            cloud_management.CloudManagement)
        mock_connect.return_value = cloud_management_mock
        cloud_management_mock.get_nodes.return_value.hosts = [
            node_collection.Host(
                ip='10.0.0.2', mac='09:7b:74:90:63:c1', fqdn='node1.local'),
            node_collection.Host(
                ip='10.0.0.3', mac='09:7b:74:90:63:c2', fqdn='node2.local')]
        cloud_management_mock.list_supported_services.return_value = [
            'srv1', 'srv2']

        def mock_service(name, config, ips):
            m = mock.create_autospec(service.Service)
            m.NAME = name
            m.config = config
            m.get_nodes.return_value.get_ips.return_value = ips
            return m

        srv1 = mock_service('process', {'grep': 'srv1'}, [])
        srv2 = mock_service('linux_service',
                            {'grep': 'srv2', 'linux_service': 'srv2'},
                            ['10.0.0.2'])
        services = {'srv1': srv1, 'srv2': srv2}
        cloud_management_mock.get_service.side_effect = services.get

        discovered_config = os_faults.discover(cloud_config)
        self.assertEqual({
            'cloud_management': {
                'driver': 'devstack',
                'args': {
                    'address': 'devstack.local',
                    'private_key_file': '/my/path/pk.key',
                    'username': 'developer'
                }
            },
            'node_discover': {
                'driver': 'node_list',
                'args': [
                    {
                        'fqdn': 'node1.local',
                        'ip': '10.0.0.2',
                        'mac': '09:7b:74:90:63:c1'
                    }, {
                        'fqdn': 'node2.local',
                        'ip': '10.0.0.3',
                        'mac': '09:7b:74:90:63:c2'
                    }
                ]
            },
            'services': {
                'srv1': {
                    'driver': 'process',
                    'args': {'grep': 'srv1'},
                },
                'srv2': {
                    'driver': 'linux_service',
                    'args': {'grep': 'srv2', 'linux_service': 'srv2'},
                    'hosts': ['10.0.0.2']
                }
            }
        }, discovered_config)
