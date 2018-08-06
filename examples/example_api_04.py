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
    # The cloud config details could be defined within the script or a
    # separate os-faults.yml file and then loaded to the script.
    # Ex. cloud_management = os_faults.connect(config_filename='os-faults.yml')
    cloud_config = {
        'cloud_management': {
            'driver': 'universal'
        },
        'node_discover': {
            'driver': 'node_list',
            'args': [
                {
                    'ip': '192.0.10.6',
                    'auth': {
                        'username': 'heat-admin',
                        'private_key_file': '/home/stack/.ssh/id_rsa',
                        'become': True
                    }
                },
                {
                    'ip': '192.0.10.8',
                    'auth': {
                        'username': 'heat-admin',
                        'private_key_file': '/home/stack/.ssh/id_rsa',
                        'become': True
                    }
                },
                {
                    'ip': '192.0.10.7',
                    'auth': {
                        'username': 'heat-admin',
                        'private_key_file': '/home/stack/.ssh/id_rsa',
                        'become': True
                    }
                }
            ]
        },
        'services': {
            'openvswitch': {
                'driver': 'system_service',
                'args': {
                    'service_name': 'openvswitch',
                    'grep': 'openvswitch'
                }
            }
        },
        'containers': {
            'neutron_ovs_agent': {
                'driver': 'docker_container',
                'args': {
                    'container_name': 'neutron_ovs_agent'
                }
            },
            'neutron_api': {
                'driver': 'docker_container',
                'args': {
                    'container_name': 'neutron_api'
                }
            }
        }
    }

    logging.info('# Create connection to the cloud')
    cloud_management = os_faults.connect(cloud_config)
    logging.info('Verify connection to the cloud')
    cloud_management.verify()

    logging.info('Get nodes where openvswitch service is running')
    service = cloud_management.get_service(name='openvswitch')
    service_nodes = service.get_nodes()
    logging.info('Nodes: {}'.format(service_nodes))

    logging.info('Stop openvswitch service on random node')
    random_node = service.get_nodes().pick()
    service.terminate(random_node)

    logging.info('Get nodes where neutron_ovs_agent container is running')
    container = cloud_management.get_container(name='neutron_ovs_agent')
    container_nodes = container.get_nodes()
    logging.info('Nodes: {}'.format(container_nodes))

    logging.info('Restart neutron_ovs_agent container on the '
                 'following nodes: {}'.format(container_nodes))
    container.restart(container_nodes)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.INFO)
    main()
