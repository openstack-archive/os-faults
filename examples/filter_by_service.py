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
            'driver': 'kvm',
            'address': 'kvm.local',
            'username': 'root',
        }
    }

    logging.info('# Create connection')
    distractor = os_failures.connect(cloud_config)

    logging.info('# Verify connection to the cloud')
    distractor.verify()

    logging.info('# Get all nodes in the cloud')
    nodes = distractor.get_nodes()
    logging.info('All cloud nodes: %s', nodes)

    mysql_nodes = nodes.filter_by_service('mysql')
    logging.info('# MySQL nodes: %s', mysql_nodes)

    rabbitmq_nodes = nodes.filter_by_service('rabbitmq')
    logging.info('# RabbitMQ nodes: %s', rabbitmq_nodes)

    keystone_nodes = nodes.filter_by_service('keystone')
    logging.info('# Keystone nodes: %s', keystone_nodes)

    nova_api_nodes = nodes.filter_by_service('nova-api')
    logging.info('# nova-api nodes: %s', nova_api_nodes)

    glance_api_nodes = nodes.filter_by_service('glance-api')
    logging.info('# glance-api nodes: %s', glance_api_nodes)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                        level=logging.INFO)
    main()