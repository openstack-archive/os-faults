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

import logging

from oslotest import base

import os_faults

LOG = logging.getLogger(__name__)


class TestOSFaultsUniversalDriverLibrary(base.BaseTestCase):
    def test_connection_stack_user(self):
        cloud_config = {
            'cloud_management': {
                'driver': 'universal'
            },
            'node_discover': {
                'driver': 'node_list',
                'args': [
                    {
                        'ip': 'localhost',
                        'auth': {
                            'username': 'stack',
                            'private_key_file': '/opt/stack/.ssh/os-faults-key'
                        }
                    }
                ]
            }
        }

        LOG.info('# Create connection to the cloud')
        cloud_management = os_faults.connect(cloud_config)
        self.assertIsNotNone(cloud_management)

        LOG.info('# Verify connection to the cloud')
        cloud_management.verify()


class TestOSFaultsDevstackDriverLibrary(base.BaseTestCase):
    def test_connection_stack_user(self):
        address = 'localhost'
        cloud_config = {
            'cloud_management': {
                'driver': 'devstack',
                'args':
                    {
                        'address': address,
                        'iface': 'lo',
                        'auth': {
                            'username': 'stack',
                            'private_key_file': '/opt/stack/.ssh/os-faults-key'
                        }
                    }
            }
        }

        LOG.info('# Create connection to the cloud')
        cloud_management = os_faults.connect(cloud_config)
        self.assertIsNotNone(cloud_management)

        LOG.info('# Verify connection to the cloud')
        cloud_management.verify()

        nodes = cloud_management.get_nodes()
        self.assertEqual(1, len(nodes))
        self.assertEqual(address, nodes[0].ip)

        service = cloud_management.get_service('etcd')
        self.assertIsNotNone(service)
        nodes = service.get_nodes()
        self.assertEqual(1, len(nodes))
        self.assertEqual(address, nodes[0].ip)

        selection = nodes.pick()
        self.assertIsNotNone(selection)
        self.assertEqual(1, len(selection))
        self.assertEqual(address, selection[0].ip)
