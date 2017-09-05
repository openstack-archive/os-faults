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

import mock

from os_faults.api import node_collection
from os_faults.drivers.cloud import fuel
from os_faults.tests.unit import test


class FuelNodeCollectionTestCase(test.TestCase):

    def setUp(self):
        super(FuelNodeCollectionTestCase, self).setUp()
        self.mock_cloud_management = mock.Mock(spec=fuel.FuelManagement)
        self.hosts = [
            node_collection.Host(ip='10.0.0.2', mac='09:7b:74:90:63:c1',
                                 fqdn='node1.com'),
            node_collection.Host(ip='10.0.0.3', mac='09:7b:74:90:63:c2',
                                 fqdn='node2.com'),
            node_collection.Host(ip='10.0.0.4', mac='09:7b:74:90:63:c3',
                                 fqdn='node3.com'),
            node_collection.Host(ip='10.0.0.5', mac='09:7b:74:90:63:c4',
                                 fqdn='node4.com'),
        ]

        self.node_collection = fuel.FuelNodeCollection(
            cloud_management=self.mock_cloud_management,
            hosts=copy.deepcopy(self.hosts))

    def test_connect(self):
        self.node_collection.connect(network_name='storage')
        self.mock_cloud_management.execute_on_cloud.assert_called_once_with(
            self.hosts, {'fuel_network_mgmt': {'operation': 'up',
                                               'network_name': 'storage'}})

    def test_disconnect(self):
        self.node_collection.disconnect(network_name='storage')
        self.mock_cloud_management.execute_on_cloud.assert_called_once_with(
            self.hosts, {'fuel_network_mgmt': {'operation': 'down',
                                               'network_name': 'storage'}})
