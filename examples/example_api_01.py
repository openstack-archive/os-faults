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
            'driver': 'fuel',
            'args': {
                'address': 'fuel.local',
                'username': 'root',
                'private_key_file': '~/.ssh/os_faults',
            }
        },
        'power_managements': [
            {
                'driver': 'libvirt',
                'args': {
                    'connection_uri': 'qemu+ssh://ubuntu@host.local/system'
                }
            }
        ]
    }

    logging.info('# Create connection to the cloud')
    cloud_management = os_faults.connect(cloud_config)

    logging.info('# Verify connection to the cloud')
    cloud_management.verify()

    # os_faults library operate with 2 types of objects:
    # service - is software that runs in the cloud, e.g. keystone, mysql,
    #           rabbitmq, nova-api, glance-api
    # nodes   - nodes that host the cloud, e.g. hardware server with hostname

    logging.info('# Get nodes where Keystone service is running')
    service = cloud_management.get_service(name='keystone')
    nodes = service.get_nodes()
    logging.info('Nodes: %s', nodes)

    logging.info('# Restart Keystone service on all nodes')
    service.restart()

    logging.info('# Pick and reset one of Keystone service nodes')
    one = nodes.pick()
    one.reset()

    logging.info('# Get all nodes in the cloud')
    nodes = cloud_management.get_nodes()
    logging.info('All cloud nodes: %s', nodes)

    logging.info('# Reset all these nodes')
    nodes.reset()

    logging.info('# Get node by FQDN: node-2.domain.tld')
    nodes = cloud_management.get_nodes(fqdns=['node-2.domain.tld'])
    logging.info('Node node-2.domain.tld: %s', nodes)

    logging.info('# Disable public network on node-2.domain.tld')
    nodes.disconnect(network_name='public')

    logging.info('# Enable public network on node-2.domain.tld')
    nodes.connect(network_name='public')

    logging.info('# Kill Glance API service on a single node')
    service = cloud_management.get_service(name='glance-api')
    nodes = service.get_nodes().pick()
    service.kill(nodes)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.INFO)
    main()
