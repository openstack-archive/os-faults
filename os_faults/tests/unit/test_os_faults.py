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

import os

import jsonschema
import mock
import yaml

import os_faults
from os_faults.ansible import executor
from os_faults.api import error
from os_faults.drivers import devstack
from os_faults.drivers import fuel
from os_faults.drivers import ipmi
from os_faults.drivers import libvirt_driver
from os_faults.drivers import node_list
from os_faults.tests.unit import test


class OSFaultsTestCase(test.TestCase):

    def setUp(self):
        super(OSFaultsTestCase, self).setUp()
        self.cloud_config = {
            'cloud_management': {
                'driver': 'fuel',
                'args': {
                    'address': '10.30.00.5',
                    'username': 'root',
                    'private_key_file': '/my/path/pk.key',
                }
            },
            'power_management': {
                'driver': 'libvirt',
                'args': {
                    'connection_uri': "qemu+ssh://user@10.30.20.21/system"
                }
            }
        }

    def test_connect_devstack(self):
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
        destructor = os_faults.connect(cloud_config)
        self.assertIsInstance(destructor, devstack.DevStackManagement)

    def test_connect_fuel_with_libvirt(self):
        destructor = os_faults.connect(self.cloud_config)
        self.assertIsInstance(destructor, fuel.FuelManagement)
        self.assertIsInstance(destructor.node_discover, fuel.FuelManagement)
        self.assertEqual(1, len(destructor.power_manager.power_drivers))
        self.assertIsInstance(destructor.power_manager.power_drivers[0],
                              libvirt_driver.LibvirtDriver)

    def test_connect_fuel_with_ipmi_libvirt_and_node_list(self):
        cloud_config = {
            'node_discover': {
                'driver': 'node_list',
                'args': [
                    {
                        'ip': '10.0.0.11',
                        'mac': '01:ab:cd:01:ab:cd',
                        'fqdn': 'node-1'
                    }, {
                        'ip': '10.0.0.12',
                        'mac': '02:ab:cd:02:ab:cd',
                        'fqdn': 'node-2'},
                ]
            },
            'cloud_management': {
                'driver': 'fuel',
                'args': {
                    'address': '10.30.00.5',
                    'username': 'root',
                },
            },
            'power_managements': [
                {
                    'driver': 'ipmi',
                    'args': {
                        'mac_to_bmc': {
                            '00:00:00:00:00:00': {
                                'address': '55.55.55.55',
                                'username': 'foo',
                                'password': 'bar',
                            }
                        }
                    }
                }, {
                    'driver': 'libvirt',
                    'args': {
                        'connection_uri': "qemu+ssh://user@10.30.20.21/system"
                    }
                }
            ]
        }
        destructor = os_faults.connect(cloud_config)
        self.assertIsInstance(destructor, fuel.FuelManagement)
        self.assertIsInstance(destructor.node_discover,
                              node_list.NodeListDiscover)
        self.assertEqual(2, len(destructor.power_manager.power_drivers))
        self.assertIsInstance(destructor.power_manager.power_drivers[0],
                              ipmi.IPMIDriver)
        self.assertIsInstance(destructor.power_manager.power_drivers[1],
                              libvirt_driver.LibvirtDriver)

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

    @mock.patch('os.path.exists', return_value=True)
    def test_connect_with_config_file(self, mock_os_path_exists):
        mock_os_faults_open = mock.mock_open(
            read_data=yaml.dump(self.cloud_config))
        with mock.patch('os_faults.open', mock_os_faults_open, create=True):
            destructor = os_faults.connect()
            self.assertIsInstance(destructor, fuel.FuelManagement)
            self.assertEqual(1, len(destructor.power_manager.power_drivers))
            self.assertIsInstance(destructor.power_manager.power_drivers[0],
                                  libvirt_driver.LibvirtDriver)

    @mock.patch.dict(os.environ, {'OS_FAULTS_CONFIG': '/my/conf.yaml'})
    @mock.patch('os.path.exists', return_value=True)
    def test_connect_with_env_config(self, mock_os_path_exists):
        mock_os_faults_open = mock.mock_open(
            read_data=yaml.dump(self.cloud_config))
        with mock.patch('os_faults.open', mock_os_faults_open, create=True):
            destructor = os_faults.connect()
            self.assertIsInstance(destructor, fuel.FuelManagement)
            self.assertEqual(1, len(destructor.power_manager.power_drivers))
            self.assertIsInstance(destructor.power_manager.power_drivers[0],
                                  libvirt_driver.LibvirtDriver)
            mock_os_faults_open.assert_called_once_with('/my/conf.yaml')

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
