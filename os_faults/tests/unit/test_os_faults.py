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
import yaml

import mock

import os_faults
from os_faults.api import error
from os_faults.drivers import devstack
from os_faults.drivers import fuel
from os_faults.drivers import ipmi
from os_faults.drivers import libvirt_driver
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
                }
            }
        }
        destructor = os_faults.connect(cloud_config)
        self.assertIsInstance(destructor, devstack.DevStackManagement)

    def test_connect_fuel_with_libvirt(self):
        destructor = os_faults.connect(self.cloud_config)
        self.assertIsInstance(destructor, fuel.FuelManagement)
        self.assertIsInstance(destructor.power_management,
                              libvirt_driver.LibvirtDriver)

    def test_connect_fuel_with_ipmi(self):
        cloud_config = {
            'cloud_management': {
                'driver': 'fuel',
                'args': {
                    'address': '10.30.00.5',
                    'username': 'root',
                }
            },
            'power_management': {
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
            }
        }
        destructor = os_faults.connect(cloud_config)
        self.assertIsInstance(destructor, fuel.FuelManagement)
        self.assertIsInstance(destructor.power_management, ipmi.IPMIDriver)

    def test_connect_driver_not_found(self):
        cloud_config = {
            'cloud_management': {
                'driver': 'non-existing',
            }
        }
        self.assertRaises(
            error.OSFDriverNotFound, os_faults.connect, cloud_config)

    def test_connect_driver_not_specified(self):
        cloud_config = {'foo': 'bar'}
        self.assertRaises(error.OSFError, os_faults.connect, cloud_config)

    @mock.patch('os.path.exists', return_value=True)
    def test_connect_with_config_file(self, mock_os_path_exists):
        mock_os_faults_open = mock.mock_open(
            read_data=yaml.dump(self.cloud_config))
        with mock.patch('os_faults.open', mock_os_faults_open, create=True):
            destructor = os_faults.connect()
            self.assertIsInstance(destructor, fuel.FuelManagement)
            self.assertIsInstance(destructor.power_management,
                                  libvirt_driver.LibvirtDriver)

    @mock.patch.dict(os.environ, {'OS_FAULTS_CONFIG': '/my/conf.yaml'})
    @mock.patch('os.path.exists', return_value=True)
    def test_connect_with_env_config(self, mock_os_path_exists):
        mock_os_faults_open = mock.mock_open(
            read_data=yaml.dump(self.cloud_config))
        with mock.patch('os_faults.open', mock_os_faults_open, create=True):
            destructor = os_faults.connect()
            self.assertIsInstance(destructor, fuel.FuelManagement)
            self.assertIsInstance(destructor.power_management,
                                  libvirt_driver.LibvirtDriver)
            mock_os_faults_open.assert_called_once_with('/my/conf.yaml')

    @mock.patch('os.path.exists', return_value=False)
    def test_connect_no_config_files(self, mock_os_path_exists):
        self.assertRaises(error.OSFError, os_faults.connect)
