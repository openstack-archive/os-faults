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
import sys

import mock

from os_faults.api import base_driver
from os_faults.api import error
from os_faults import drivers
from os_faults import registry
from os_faults.tests.unit import test


class TestDriver(base_driver.BaseDriver):
    NAME = 'test'


class RegistryTestCase(test.TestCase):

    def setUp(self):
        super(RegistryTestCase, self).setUp()
        registry.DRIVERS.clear()  # reset global drivers list

    def tearDown(self):
        super(RegistryTestCase, self).tearDown()
        registry.DRIVERS.clear()  # reset global drivers list

    @mock.patch('oslo_utils.importutils.import_module')
    @mock.patch('os.walk')
    def test_get_drivers(self, mock_os_walk, mock_import_module):
        drivers_folder = os.path.dirname(drivers.__file__)
        mock_os_walk.return_value = [(drivers_folder, [], ['driver.py'])]
        mock_import_module.return_value = sys.modules[__name__]

        self.assertEqual({'test': TestDriver}, registry.get_drivers())

    @mock.patch('os_faults.registry._list_drivers')
    def test_name_collision(self, mock_list_drivers):
        class TestDriver1(base_driver.BaseDriver):
            NAME = 'test'

        class TestDriver2(base_driver.BaseDriver):
            NAME = 'test'

        mock_list_drivers.return_value = [TestDriver1, TestDriver2]
        self.assertRaises(error.OSFDriverWithSuchNameExists,
                          registry.get_drivers)
