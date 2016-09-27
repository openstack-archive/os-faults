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

import ddt
import mock

from os_faults.api import error
from os_faults.api import human
from os_faults.api import node_collection
from os_faults.api import service as service_api
from os_faults.tests.unit import test


@ddt.ddt
class TestHumanAPI(test.TestCase):
    def setUp(self):
        super(TestHumanAPI, self).setUp()
        self.destructor = mock.MagicMock()
        self.service = mock.MagicMock(service_api.Service)

        self.destructor.get_service = mock.MagicMock(return_value=self.service)

    @ddt.data(('restart', 'keystone'), ('kill', 'nova-api'))
    @ddt.unpack
    def test_service_action(self, action, service_name):

        command = '%s %s service' % (action, service_name)
        human.execute(self.destructor, command)

        self.destructor.get_service.assert_called_once_with(name=service_name)
        getattr(self.service, action).assert_called_once_with()

    @ddt.data(('restart', 'keystone', 'random'), ('kill', 'nova-api', 'one'))
    @ddt.unpack
    def test_service_action_on_random_node(self, action, service_name, node):

        nodes = mock.MagicMock(node_collection.NodeCollection)
        self.service.get_nodes = mock.MagicMock(return_value=nodes)

        one_node = mock.MagicMock(node_collection.NodeCollection)
        nodes.pick = mock.MagicMock(return_value=one_node)

        command = '%s %s service on %s node' % (action, service_name, node)
        human.execute(self.destructor, command)

        self.destructor.get_service.assert_called_once_with(name=service_name)
        getattr(self.service, action).assert_called_once_with(nodes=one_node)

        nodes.pick.assert_called_once()

    @ddt.data(('freeze', 'keystone', 5))
    @ddt.unpack
    def test_service_action_with_duration(self, action, service_name, t):

        command = '%s %s service for %d seconds' % (action, service_name, t)
        human.execute(self.destructor, command)

        self.destructor.get_service.assert_called_once_with(name=service_name)
        getattr(self.service, action).assert_called_once_with(sec=t)

    @ddt.data(('restart', 'keystone', 'node'), ('kill', 'nova-api', 'node'))
    @ddt.unpack
    def test_service_action_on_fqdn_node(self, action, service_name, node):

        nodes = mock.MagicMock(node_collection.NodeCollection)
        self.destructor.get_nodes.return_value = nodes

        command = '%s %s service on %s node' % (action, service_name, node)
        human.execute(self.destructor, command)

        self.destructor.get_service.assert_called_once_with(name=service_name)
        self.destructor.get_nodes.assert_called_once_with(fqdns=[node])
        getattr(self.service, action).assert_called_once_with(nodes=nodes)

    @ddt.data(('reboot', 'keystone'), ('reset', 'nova-api'))
    @ddt.unpack
    def test_node_action_on_all_nodes(self, action, service_name):

        nodes = mock.MagicMock(node_collection.NodeCollection)

        self.service.get_nodes = mock.MagicMock(return_value=nodes)

        command = '%s node with %s' % (action, service_name)
        human.execute(self.destructor, command)

        self.destructor.get_service.assert_called_once_with(name=service_name)
        getattr(nodes, action).assert_called_once_with()

    @ddt.data(('reboot', 'keystone'), ('reset', 'nova-api'))
    @ddt.unpack
    def test_node_action_on_random_node(self, action, service_name):

        nodes = mock.MagicMock(node_collection.NodeCollection)
        nodes2 = mock.MagicMock(node_collection.NodeCollection)

        self.service.get_nodes = mock.MagicMock(return_value=nodes)
        nodes.pick = mock.MagicMock(return_value=nodes2)

        command = '%s one node with %s' % (action, service_name)
        human.execute(self.destructor, command)

        self.destructor.get_service.assert_called_once_with(name=service_name)
        nodes.pick.assert_called_once()
        getattr(nodes2, action).assert_called_once_with()

    @ddt.data('reboot', 'poweroff', 'poweron')
    def test_node_action_by_fqdn(self, action):
        destructor = mock.MagicMock()
        nodes = mock.MagicMock(node_collection.NodeCollection)
        destructor.get_nodes = mock.MagicMock(return_value=nodes)

        command = '%s node-2.local node' % action.capitalize()
        human.execute(destructor, command)

        destructor.get_nodes.assert_called_once_with(fqdns=['node-2.local'])
        getattr(nodes, action).assert_called_once()

    @ddt.data(('Disable network', 'disable_network'),
              ('Enable network', 'enable_network'))
    @ddt.unpack
    def test_disable_network_node_by_fqdn(self, user_action, action):
        destructor = mock.MagicMock()
        nodes = mock.MagicMock(node_collection.NodeCollection)
        destructor.get_nodes = mock.MagicMock(return_value=nodes)

        command = '%s storage on node-2.local node' % user_action
        human.execute(destructor, command)

        destructor.get_nodes.assert_called_once_with(fqdns=['node-2.local'])
        getattr(nodes, action).assert_called_once_with(network_name='storage')

    def test_malformed_query(self):
        destructor = mock.MagicMock()

        command = 'inject some fault'
        self.assertRaises(error.OSFException, human.execute, destructor,
                          command)
