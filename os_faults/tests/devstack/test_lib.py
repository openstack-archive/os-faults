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


class TestOSFaultsLibrary(base.BaseTestCase):
    def test_connection(self):
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
