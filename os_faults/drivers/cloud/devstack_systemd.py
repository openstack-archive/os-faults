# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from os_faults.drivers.cloud import devstack

LOG = logging.getLogger(__name__)


class DevStackSystemdManagement(devstack.DevStackManagement):
    """Driver for modern DevStack based on Systemd.

    This driver requires DevStack installed with Systemd (USE_SCREEN=False).
    Supports discovering of node MAC addresses.

    **Example configuration:**

    .. code-block:: yaml

        cloud_management:
          driver: devstack_systemd
          args:
            address: 192.168.1.10
            username: ubuntu
            password: ubuntu_pass
            private_key_file: ~/.ssh/id_rsa_devstack_systemd
            slaves:
            - 192.168.1.11
            - 192.168.1.12
            iface: eth1

    parameters:

    - **address** - ip address of any devstack node
    - **username** - username for all nodes
    - **password** - password for all nodes (optional)
    - **private_key_file** - path to key file (optional)
    - **slaves** - list of ips for additional nodes (optional)
    - **iface** - network interface name to retrieve mac address (optional)
    - **serial** - how many hosts Ansible should manage at a single time.
      (optional) default: 10
    """

    NAME = 'devstack_systemd'
    DESCRIPTION = 'DevStack management driver using Systemd'
    # NODE_CLS = DevStackNode
    SERVICES = {
        'keystone': {
            'driver': 'systemd_service',
            'args': {
                'grep': 'keystone-uwsgi',
                'systemd_service': 'devstack@keystone',
            }
        },
        'mysql': {
            'driver': 'systemd_service',
            'args': {
                'grep': 'mysqld',
                'systemd_service': 'mariadb',
                'port': ['tcp', 3307],
            }
        },
        'rabbitmq': {
            'driver': 'systemd_service',
            'args': {
                'grep': 'rabbitmq_server',
                'systemd_service': 'rabbitmq-server',
            }
        },
        'nova-api': {
            'driver': 'systemd_service',
            'args': {
                'grep': 'nova-api',
                'systemd_service': 'devstack@n-api',
            }
        },
        'glance-api': {
            'driver': 'systemd_service',
            'args': {
                'grep': 'glance-api',
                'systemd_service': 'devstack@g-api',
            }
        },
        'nova-compute': {
            'driver': 'systemd_service',
            'args': {
                'grep': 'nova-compute',
                'systemd_service': 'devstack@n-cpu',
            }
        },
        'nova-scheduler': {
            'driver': 'systemd_service',
            'args': {
                'grep': 'nova-scheduler',
                'systemd_service': 'devstack@n-sch',
            }
        },
    }
    SUPPORTED_NETWORKS = ['all-in-one']
    CONFIG_SCHEMA = {
        'type': 'object',
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'properties': {
            'address': {'type': 'string'},
            'username': {'type': 'string'},
            'password': {'type': 'string'},
            'private_key_file': {'type': 'string'},
            'slaves': {
                'type': 'array',
                'items': {'type': 'string'},
            },
            'iface': {'type': 'string'},
            'serial': {'type': 'integer', 'minimum': 1},
        },
        'required': ['address', 'username'],
        'additionalProperties': False,
    }
