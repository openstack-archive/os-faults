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
    cloud_config = {
        'cloud_management': {
            'driver': 'universal',
        },
        'node_discover': {
            'driver': 'node_list',
            'args': [
                {
                    'ip': '192.168.5.127',
                    'auth': {
                        'username': 'root',
                        'private_key_file': 'openstack_key',
                    }
                },
                {
                    'ip': '192.168.5.128',
                    'auth': {
                        'username': 'root',
                        'private_key_file': 'openstack_key',
                    }
                }
            ]
        },
        'services': {
            'memcached': {
                'driver': 'system_service',
                'args': {
                    'service_name': 'memcached',
                    'grep': 'memcached',
                }
            }
        },
        'power_managements': [
            {
                'driver': 'libvirt',
                'args': {
                    'connection_uri': 'qemu+unix:///system',
                }
            },
        ]
    }

    logging.info('# Create connection to the cloud')
    cloud_management = os_faults.connect(cloud_config)

    logging.info('# Verify connection to the cloud')
    cloud_management.verify()

    logging.info('# Kill Memcached service on all nodes')
    service = cloud_management.get_service(name='memcached')
    service.kill()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.INFO)
    main()
