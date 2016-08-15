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

import os_failures


def main():
    # cloud config schema is an extension to os-client-config
    cloud_config = {
        'auth': {
            'username': 'admin',
            'password': 'admin',
            'project_name': 'admin',
        },
        'region_name': 'RegionOne',
        'cloud_management': {
            'driver': 'devstack',
            'address': '172.18.76.77',
            'username': 'developer',
        }
    }

    logging.info('# Create connection')
    distractor = os_failures.connect(cloud_config)

    logging.info('# Verify connection to the cloud')
    distractor.verify()

    logging.info('# Get a particular service in the cloud')
    service = distractor.get_service(name='keystone-api')
    logging.info('Keystone API Service: %s', service)

    logging.info('# Restart the service')
    service.restart()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.INFO)
    main()
