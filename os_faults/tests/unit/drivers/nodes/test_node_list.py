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

from os_faults.api import node_collection
from os_faults.drivers.nodes import node_list
from os_faults.tests.unit import test


class NodeListDiscoverTestCase(test.TestCase):

    def test_discover_hosts(self):
        conf = [
            {'ip': '10.0.0.11', 'mac': '01', 'fqdn': 'node-1'},
            {'ip': '10.0.0.12', 'mac': '02', 'fqdn': 'node-2'},
        ]
        expected_hosts = [
            node_collection.Host(ip='10.0.0.11', mac='01', fqdn='node-1'),
            node_collection.Host(ip='10.0.0.12', mac='02', fqdn='node-2'),
        ]

        node_list_discover = node_list.NodeListDiscover(conf)
        hosts = node_list_discover.discover_hosts()
        self.assertEqual(expected_hosts, hosts)
