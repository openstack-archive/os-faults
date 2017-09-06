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

import json
import logging

from os_faults.ansible import executor
from os_faults.api import cloud_management
from os_faults.api import node_collection
from os_faults.api import node_discover

LOG = logging.getLogger(__name__)


class FuelNodeCollection(node_collection.NodeCollection):

    def connect(self, network_name):
        LOG.info("Connect network '%s' on nodes: %s", network_name, self)
        task = {'fuel_network_mgmt': {
            'network_name': network_name,
            'operation': 'up',
        }}
        self.cloud_management.execute_on_cloud(self.hosts, task)

    def disconnect(self, network_name):
        LOG.info("Disconnect network '%s' on nodes: %s",
                 network_name, self)
        task = {'fuel_network_mgmt': {
            'network_name': network_name,
            'operation': 'down',
        }}
        self.cloud_management.execute_on_cloud(self.hosts, task)


class FuelManagement(cloud_management.CloudManagement,
                     node_discover.NodeDiscover):
    """Fuel driver.

    Cloud deployed by fuel. Supports discovering of slave nodes.

    **Example configuration:**

    .. code-block:: yaml

        cloud_management:
          driver: fuel
          args:
            address: 192.168.1.10
            username: root
            private_key_file: ~/.ssh/id_rsa_fuel
            slave_direct_ssh: True

    parameters:

    - **address** - ip address of fuel master node
    - **username** - username for fuel master and slave nodes
    - **private_key_file** - path to key file (optional)
    - **slave_direct_ssh** - if *False* then fuel master is used as ssh proxy
      (optional)
    - **serial** - how many hosts Ansible should manage at a single time.
      (optional) default: 10
    """

    NAME = 'fuel'
    DESCRIPTION = 'Fuel 9.x cloud management driver'
    NODE_CLS = FuelNodeCollection
    SERVICES = {
        'keystone': {
            'driver': 'linux_service',
            'args': {
                'grep': 'keystone',
                'linux_service': 'apache2',
            }
        },
        'horizon': {
            'driver': 'linux_service',
            'args': {
                'grep': 'apache2',
                'linux_service': 'apache2',
            }
        },
        'memcached': {
            'driver': 'linux_service',
            'args': {
                'grep': 'memcached',
                'linux_service': 'memcached',
            }
        },
        'mysql': {
            'driver': 'pcs_service',
            'args': {
                'grep': 'mysqld',
                'pcs_service': 'p_mysqld',
                'port': ['tcp', 3307],
            }
        },
        'rabbitmq': {
            'driver': 'pcs_service',
            'args': {
                'grep': 'rabbit tcp_listeners',
                'pcs_service': 'p_rabbitmq-server',
            }
        },
        'glance-api': {
            'driver': 'linux_service',
            'args': {
                'grep': 'glance-api',
                'linux_service': 'glance-api',
            }
        },
        'glance-glare': {
            'driver': 'linux_service',
            'args': {
                'grep': 'glance-glare',
                'linux_service': 'glance-glare',
            }
        },
        'glance-registry': {
            'driver': 'linux_service',
            'args': {
                'grep': 'glance-registry',
                'linux_service': 'glance-registry',
            }
        },
        'nova-api': {
            'driver': 'linux_service',
            'args': {
                'grep': 'nova-api',
                'linux_service': 'nova-api',
            }
        },
        'nova-compute': {
            'driver': 'linux_service',
            'args': {
                'grep': 'nova-compute',
                'linux_service': 'nova-compute',
            }
        },
        'nova-scheduler': {
            'driver': 'linux_service',
            'args': {
                'grep': 'nova-scheduler',
                'linux_service': 'nova-scheduler',
            }
        },
        'nova-cert': {
            'driver': 'linux_service',
            'args': {
                'grep': 'nova-cert',
                'linux_service': 'nova-cert',
            }
        },
        'nova-conductor': {
            'driver': 'linux_service',
            'args': {
                'grep': 'nova-conductor',
                'linux_service': 'nova-conductor',
            }
        },
        'nova-consoleauth': {
            'driver': 'linux_service',
            'args': {
                'grep': 'nova-consoleauth',
                'linux_service': 'nova-consoleauth',
            }
        },
        'nova-novncproxy': {
            'driver': 'linux_service',
            'args': {
                'grep': 'nova-novncproxy',
                'linux_service': 'nova-novncproxy',
            }
        },
        'neutron-server': {
            'driver': 'linux_service',
            'args': {
                'grep': 'neutron-server',
                'linux_service': 'neutron-server',
            }
        },
        'neutron-dhcp-agent': {
            'driver': 'pcs_service',
            'args': {
                'grep': 'neutron-dhcp-agent',
                'pcs_service': 'neutron-dhcp-agent',
            }
        },
        'neutron-metadata-agent': {
            'driver': 'pcs_or_linux_service',
            'args': {
                'grep': 'neutron-metadata-agent',
                'pcs_service': 'neutron-metadata-agent',
                'linux_service': 'neutron-metadata-agent',
            }
        },
        'neutron-openvswitch-agent': {
            'driver': 'pcs_or_linux_service',
            'args': {
                'grep': 'neutron-openvswitch-agent',
                'pcs_service': 'neutron-openvswitch-agent',
                'linux_service': 'neutron-openvswitch-agent',
            }
        },
        'neutron-l3-agent': {
            'driver': 'pcs_or_linux_service',
            'args': {
                'grep': 'neutron-l3-agent',
                'pcs_service': 'neutron-l3-agent',
                'linux_service': 'neutron-l3-agent',
            }
        },
        'heat-api': {
            'driver': 'linux_service',
            'args': {
                'grep': 'heat-api',
                'linux_service': 'heat-api',
            }
        },
        'heat-engine': {
            'driver': 'pcs_service',
            'args': {
                'grep': 'heat-engine',
                'pcs_service': 'p_heat-engine',
            }
        },
        'cinder-api': {
            'driver': 'linux_service',
            'args': {
                'grep': 'cinder-api',
                'linux_service': 'cinder-api',
            }
        },
        'cinder-scheduler': {
            'driver': 'linux_service',
            'args': {
                'grep': 'cinder-scheduler',
                'linux_service': 'cinder-scheduler',
            }
        },
        'cinder-volume': {
            'driver': 'linux_service',
            'args': {
                'grep': 'cinder-volume',
                'linux_service': 'cinder-volume',
            }
        },
        'cinder-backup': {
            'driver': 'linux_service',
            'args': {
                'grep': 'cinder-backup',
                'linux_service': 'cinder-backup',
            }
        },
        'ironic-api': {
            'driver': 'linux_service',
            'args': {
                'grep': 'ironic-api',
                'linux_service': 'ironic-api',
            }
        },
        'ironic-conductor': {
            'driver': 'linux_service',
            'args': {
                'grep': 'ironic-conductor',
                'linux_service': 'ironic-conductor',
            }
        },
        'swift-account': {
            'driver': 'linux_service',
            'args': {
                'grep': 'swift-account',
                'linux_service': 'swift-account',
            }
        },
        'swift-account-auditor': {
            'driver': 'linux_service',
            'args': {
                'grep': 'swift-account-auditor',
                'linux_service': 'swift-account-auditor',
            }
        },
        'swift-account-reaper': {
            'driver': 'linux_service',
            'args': {
                'grep': 'swift-account-reaper',
                'linux_service': 'swift-account-reaper',
            }
        },
        'swift-account-replicator': {
            'driver': 'linux_service',
            'args': {
                'grep': 'swift-account-replicator',
                'linux_service': 'swift-account-replicator',
            }
        },
        'swift-container': {
            'driver': 'linux_service',
            'args': {
                'grep': 'swift-container',
                'linux_service': 'swift-container',
            }
        },
        'swift-container-auditor': {
            'driver': 'linux_service',
            'args': {
                'grep': 'swift-container-auditor',
                'linux_service': 'swift-container-auditor',
            }
        },
        'swift-container-replicator': {
            'driver': 'linux_service',
            'args': {
                'grep': 'swift-container-replicator',
                'linux_service': 'swift-container-replicator',
            }
        },
        'swift-container-sync': {
            'driver': 'linux_service',
            'args': {
                'grep': 'swift-container-sync',
                'linux_service': 'swift-container-sync',
            }
        },
        'swift-container-updater': {
            'driver': 'linux_service',
            'args': {
                'grep': 'swift-container-updater',
                'linux_service': 'swift-container-updater',
            }
        },
        'swift-object': {
            'driver': 'linux_service',
            'args': {
                'grep': 'swift-object',
                'linux_service': 'swift-object',
            }
        },
        'swift-object-auditor': {
            'driver': 'linux_service',
            'args': {
                'grep': 'swift-object-auditor',
                'linux_service': 'swift-object-auditor',
            }
        },
        'swift-object-replicator': {
            'driver': 'linux_service',
            'args': {
                'grep': 'swift-object-replicator',
                'linux_service': 'swift-object-replicator',
            }
        },
        'swift-object-updater': {
            'driver': 'linux_service',
            'args': {
                'grep': 'swift-object-updater',
                'linux_service': 'swift-object-updater',
            }
        },
        'swift-proxy': {
            'driver': 'linux_service',
            'args': {
                'grep': 'swift-proxy',
                'linux_service': 'swift-proxy',
            }
        },
    }
    SUPPORTED_NETWORKS = ['management', 'private', 'public', 'storage']
    CONFIG_SCHEMA = {
        'type': 'object',
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'properties': {
            'address': {'type': 'string'},
            'username': {'type': 'string'},
            'private_key_file': {'type': 'string'},
            'slave_direct_ssh': {'type': 'boolean'},
            'serial': {'type': 'integer', 'minimum': 1},
        },
        'required': ['address', 'username'],
        'additionalProperties': False,
    }

    def __init__(self, cloud_management_params):
        super(FuelManagement, self).__init__()
        self.node_discover = self  # supports discovering

        self.master_node_address = cloud_management_params['address']
        self._master_host = node_collection.Host(ip=self.master_node_address)
        self.username = cloud_management_params['username']
        self.private_key_file = cloud_management_params.get('private_key_file')
        self.slave_direct_ssh = cloud_management_params.get(
            'slave_direct_ssh', False)
        self.serial = cloud_management_params.get('serial')

        self.master_node_executor = executor.AnsibleRunner(
            remote_user=self.username, private_key_file=self.private_key_file)

        jump_host = self.master_node_address
        if self.slave_direct_ssh:
            jump_host = None

        self.cloud_executor = executor.AnsibleRunner(
            remote_user=self.username, private_key_file=self.private_key_file,
            jump_host=jump_host, serial=self.serial)

        self.cached_cloud_hosts = list()

    def verify(self):
        """Verify connection to the cloud."""
        nodes = self.get_nodes()
        LOG.debug('Cloud nodes: %s', nodes)

        task = {'command': 'hostname'}
        task_result = self.execute_on_cloud(nodes.hosts, task)
        LOG.debug('Hostnames of cloud nodes: %s',
                  [r.payload['stdout'] for r in task_result])

        LOG.info('Connected to cloud successfully!')

    def discover_hosts(self):
        if not self.cached_cloud_hosts:
            task = {'command': 'fuel node --json'}
            result = self._execute_on_master_node(task)
            for r in json.loads(result[0].payload['stdout']):
                host = node_collection.Host(ip=r['ip'], mac=r['mac'],
                                            fqdn=r['fqdn'])
                self.cached_cloud_hosts.append(host)

        return self.cached_cloud_hosts

    def _execute_on_master_node(self, task):
        """Execute task on Fuel master node.

        :param task: Ansible task
        :return: Ansible execution result (list of records)
        """
        return self.master_node_executor.execute([self._master_host], task)

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
