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
            'address': '172.18.171.149',
            'username': 'root',
        },
        'power_management': {
            'driver': 'kvm',
            'address': '172.18.171.5',
            'username': 'root',
        }
    }

    logging.info('# Create connection')
    distractor = os_failures.connect(cloud_config)

    logging.info('# Verify connection to the cloud')
    distractor.verify()

    # os_failures library operate with 2 types of objects:
    # service - is software that runs in the cloud, e.g. keystone
    # nodes - nodes that host the cloud, e.g. hardware server with hostname

    logging.info('# Get a particular service in the cloud')
    service = distractor.get_service(name='keystone-api')
    logging.info('Keystone API Service: %s', service)

    logging.info('# Restart the service')
    service.restart()

    logging.info('# Get nodes where the service runs')
    nodes = service.get_nodes()
    logging.info('Nodes: %s', nodes)

    logging.info('# Reboot these nodes')
    nodes.reboot()

    logging.info('# Pick one one out of collection of nodes')
    one = nodes.pick()

    logging.info('# Switch the node off')
    one.poweroff()

    logging.info('# Get all nodes in the cloud')
    nodes = distractor.get_nodes()
    logging.info('All cloud nodes: %s', nodes)

    logging.info('# Reset all these nodes')
    nodes.reset()

    logging.info('# Get nodes by their FQDNs')
    nodes = distractor.get_nodes(fqdns=['node-2.domain.tld'])
    logging.info('Node with specific FQDN: %s', nodes)

    logging.info('# Disable public network on these nodes')
    nodes.disable_network(network_name='public')

    logging.info('# Enable public network on these nodes')
    nodes.enable_network(network_name='public')

    logging.info('# Restart service on a single node')
    service = distractor.get_service(name='keystone-api')
    nodes = service.get_nodes().pick()
    service.restart(nodes)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.INFO)
    main()
