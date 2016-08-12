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

    # connect
    distractor = os_failures.connect(cloud_config)

    # verify connection to the cloud
    distractor.verify()

    # os_failures library operate with 2 types of instances:
    # service - is software that runs in the cloud, e.g. keystone
    # nodes - nodes that host the cloud, e.g. hardware server with hostname

    # get a particular service in the cloud
    service = distractor.get_service(name='keystone-api')
    logging.info('Keystone API Service: %s', service)

    # restart the service
    service.restart()

    # use case #2: get nodes where the service runs
    nodes = service.get_nodes()
    logging.info('Nodes: %s', nodes)

    # reboot these nodes
    nodes.reboot()

    # pick one one out of collection of nodes
    one = nodes.pick()

    # switch the node off
    one.poweroff()

    # get all nodes in the cloud
    nodes = distractor.get_nodes()
    logging.info('All cloud nodes: %s', nodes)

    # reset all these nodes
    nodes.reset()

    # get nodes by their FQDNs
    nodes = distractor.get_nodes(fqdns=['node-1.domain.tld'])
    logging.info('Node with specific FQDN: %s', nodes)

    # disable public network on these nodes
    nodes.disable_network(network_name='public')

    # enable public network on these nodes
    nodes.enable_network(network_name='public')


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.INFO)
    main()
