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
            'driver': 'fuel',
            'address': 'fuel.local',
            'username': 'root',
        },
        'power_management': {
            'driver': 'libvirt',
            'connection_uri': "qemu+ssh://ubuntu@host.local/system"
        }
    }

    logging.info('Create connection to the cluster')
    destructor = os_failures.connect(cloud_config)

    logging.info('Verify connection to the cluster')
    destructor.verify()

    logging.info('Get all cluster nodes')
    nodes = destructor.get_nodes()
    logging.info('All cluster nodes: %s', nodes)

    logging.info('Pick and power off one of cluster nodes')
    one = nodes.pick()
    one.poweroff()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.INFO)
    main()
