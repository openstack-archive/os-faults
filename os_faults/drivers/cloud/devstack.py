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

from os_faults.ansible import executor
from os_faults.api import cloud_management
from os_faults.api import node_collection
from os_faults.api import node_discover
from os_faults.drivers import shared_schemas

LOG = logging.getLogger(__name__)


class DevStackNodeCollection(node_collection.NodeCollection):
    def connect(self, network_name):
        raise NotImplementedError

    def disconnect(self, network_name):
        raise NotImplementedError


class DevStackCloudManagement(cloud_management.CloudManagement,
                              node_discover.NodeDiscover):
    """Driver for DevStack.

    This driver requires DevStack installed with Systemd (USE_SCREEN=False).
    Supports discovering of node MAC addresses.

    **Example configuration:**

    .. code-block:: yaml

        cloud_management:
          driver: devstack
          args:
            address: 192.168.1.10
            auth:
              username: ubuntu
              password: ubuntu_pass
              private_key_file: ~/.ssh/id_rsa_devstack
            iface: eth1

    parameters:

    - **address** - ip address of any devstack node
    - **username** - username for all nodes
    - **password** - password for all nodes (optional)
    - **private_key_file** - path to key file (optional)
    - **iface** - network interface name to retrieve mac address (optional)
    """

    NAME = 'devstack'
    DESCRIPTION = 'DevStack driver'
    NODE_CLS = DevStackNodeCollection
    SERVICES = {
        'cinder-api': {
            'driver': 'system_service',
            'args': {
                'grep': 'cinder-api',
                'service_name': 'devstack@c-api',
            }
        },
        'cinder-scheduler': {
            'driver': 'system_service',
            'args': {
                'grep': 'cinder-schedule',
                'service_name': 'devstack@c-sch',
            }
        },
        'cinder-volume': {
            'driver': 'system_service',
            'args': {
                'grep': 'cinder-volume',
                'service_name': 'devstack@c-vol',
            }
        },
        'etcd': {
            'driver': 'system_service',
            'args': {
                'grep': 'etcd',
                'service_name': 'devstack@etcd',
            }
        },
        'glance-api': {
            'driver': 'system_service',
            'args': {
                'grep': 'glance-api',
                'service_name': 'devstack@g-api',
            }
        },
        'heat-api': {
            'driver': 'system_service',
            'args': {
                'grep': 'heat-api',
                'service_name': 'devstack@h-api',
            }
        },
        'heat-engine': {
            'driver': 'system_service',
            'args': {
                'grep': 'heat-engine',
                'service_name': 'devstack@h-eng',
            }
        },
        'keystone': {
            'driver': 'system_service',
            'args': {
                'grep': 'keystone',
                'service_name': 'devstack@keystone',
            }
        },
        'memcached': {
            'driver': 'system_service',
            'args': {
                'grep': 'memcached',
                'service_name': 'memcached',
            }
        },
        'mysql': {
            'driver': 'system_service',
            'args': {
                'grep': 'mysqld',
                'service_name': 'mariadb',
                'port': ['tcp', 3307],
            }
        },
        'neutron-dhcp-agent': {
            'driver': 'system_service',
            'args': {
                'grep': 'neutron-dhcp-agent',
                'service_name': 'devstack@q-dhcp',
            }
        },
        'neutron-l3-agent': {
            'driver': 'system_service',
            'args': {
                'grep': 'neutron-l3-agent',
                'service_name': 'devstack@q-l3',
            }
        },
        'neutron-meta-agent': {
            'driver': 'system_service',
            'args': {
                'grep': 'neutron-meta-agent',
                'service_name': 'devstack@q-meta',
            }
        },
        'neutron-openvswitch-agent': {
            'driver': 'system_service',
            'args': {
                'grep': 'neutron-openvswitch-agent',
                'service_name': 'devstack@q-agt',
            }
        },
        'neutron-server': {
            'driver': 'system_service',
            'args': {
                'grep': 'neutron-server',
                'service_name': 'devstack@q-svc',
            }
        },
        'nova-api': {
            'driver': 'system_service',
            'args': {
                'grep': 'nova-api',
                'service_name': 'devstack@n-api',
            }
        },
        'nova-compute': {
            'driver': 'system_service',
            'args': {
                'grep': 'nova-compute',
                'service_name': 'devstack@n-cpu',
            }
        },
        'nova-scheduler': {
            'driver': 'system_service',
            'args': {
                'grep': 'nova-scheduler',
                'service_name': 'devstack@n-sch',
            }
        },
        'placement-api': {
            'driver': 'system_service',
            'args': {
                'grep': 'placement',
                'service_name': 'devstack@placement-api',
            }
        },
        'rabbitmq': {
            'driver': 'system_service',
            'args': {
                'grep': 'rabbitmq_server',
                'service_name': 'rabbitmq-server',
            }
        },
    }
    SUPPORTED_NETWORKS = ['all-in-one']
    CONFIG_SCHEMA = {
        'type': 'object',
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'properties': {
            'address': {'type': 'string'},
            'auth': shared_schemas.AUTH_SCHEMA,
            'iface': {'type': 'string'},
        },
        'required': ['address', 'auth'],
        'additionalProperties': False,
    }

    def __init__(self, cloud_management_params):
        super(DevStackCloudManagement, self).__init__()
        self.node_discover = self  # supports discovering

        address = cloud_management_params['address']
        auth = cloud_management_params['auth']
        self.iface = cloud_management_params.get('iface', 'eth0')

        self.cloud_executor = executor.AnsibleRunner(auth=auth)

        self.hosts = [node_collection.Host(ip=address)]
        self.nodes = None

    def verify(self):
        """Verify connection to the cloud."""
        nodes = self.get_nodes()
        if nodes:
            LOG.debug('DevStack nodes: %s', nodes)
            LOG.info('Connected to cloud successfully')

    def execute_on_cloud(self, hosts, task, raise_on_error=True):
        """Execute task on specified hosts within the cloud.

        :param hosts: List of host FQDNs
        :param task: Ansible task
        :param raise_on_error: throw exception in case of error
        :return: Ansible execution result (list of records)
        """
        if raise_on_error:
            return self.cloud_executor.execute(hosts, task)
        else:
            return self.cloud_executor.execute(hosts, task, [])

    def discover_hosts(self):
        if self.nodes is None:
            get_mac_cmd = 'cat /sys/class/net/{}/address'.format(self.iface)
            task = {'command': get_mac_cmd}
            results = self.execute_on_cloud(self.hosts, task)

            # TODO(astudenov): support fqdn
            self.nodes = [node_collection.Host(ip=r.host,
                                               mac=r.payload['stdout'],
                                               fqdn='')
                          for r in results]

        return self.nodes
