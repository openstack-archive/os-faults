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

import os_faults


def main():
    # cloud config schema is an extension to os-client-config
    cloud_config = {
        'cloud_management': {
            'driver': 'devstack',
            'args': {
                'address': 'devstack.local',
                'username': 'stack',
            }
        }
    }

    logging.info('# Create connection to the cloud')
    cloud_management = os_faults.connect(cloud_config)

    logging.info('# Verify connection to the cloud')
    cloud_management.verify()

    logging.info('# Restart Keystone service on all nodes')
    service = cloud_management.get_service(name='keystone')
    service.restart()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.INFO)
    main()
