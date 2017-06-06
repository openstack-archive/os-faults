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
from os_faults.common import service

LOG = logging.getLogger(__name__)


class DevStackNode(node_collection.NodeCollection):

    def connect(self, network_name):
        raise NotImplementedError

    def disconnect(self, network_name):
        raise NotImplementedError


class ServiceInSystemdUnit(service.ServiceAsProcess):
    """Service in Systemd unit.

    This driver controls serviced that is started as Systemd unit.

    **Example configuration:**

    .. code-block:: yaml

        services:
          app:
            driver: systemd
            args:
              unit_name: app
              grep: my_app
              port: ['tcp', 4242]

    parameters:

    - **unit_name** - name of a service
    - **grep** - regexp for grep to find process PID
    - **port** - tuple with two values - protocol, port number (optional)

    """
    NAME = 'systemd'
    DESCRIPTION = 'Service as Systemd unit'
    CONFIG_SCHEMA = {
        'type': 'object',
        'properties': {
            'unit_name': {'type': 'string'},
            'grep': {'type': 'string'},
            'port': service.PORT_SCHEMA,
        },
        'required': ['grep', 'unit_name'],
        'additionalProperties': False,
    }

    def __init__(self, *args, **kwargs):
        super(ServiceInSystemdUnit, self).__init__(*args, **kwargs)
        self.unit_name = self.config['unit_name']

        # restart systemd unit
        self.restart_cmd = ("systemctl restart "
                            "devstack@{}.service".format(self.unit_name))

        # stop systemd unit
        self.terminate_cmd = ("systemctl stop "
                              "devstack@{}.service".format(self.unit_name))

        # start systemd unit
        self.start_cmd = ("systemctl start "
                          "devstack@{}.service".format(self.unit_name))


class DevStackSystemdManagement(cloud_management.CloudManagement,
                                node_discover.NodeDiscover):
    """Devstack Systemd driver.

    This driver requires Devstack installed with Systemd (USE_SCREEN=False).
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
    NODE_CLS = DevStackNode
    SERVICES = {
        'keystone': {
            'driver': 'systemd_service',
            'args': {
                'grep': 'apache2',
                'systemd_service': 'keystone.service',
                'restart_cmd': 'systemctl restart apache2',
                'terminate_cmd': 'systemctl stop apache2 ',
                'start_cmd': 'systemctl start apache2',
            }
        },
        'mysql': {
            'driver': 'systemd_service',
            'args': {
                'grep': 'mysqld',
                'systemd_service': 'mysql.service',
                'restart_cmd': 'systemctl restart mysql',
                'terminate_cmd': 'systemctl stop mysql',
                'start_cmd': 'systemctl start mysql',
                'port': ['tcp', 3307],
            }
        },
        'rabbitmq': {
            'driver': 'systemd_service',
            'args': {
                'grep': 'rabbit.service',
                'systemd_service': 'rabbit.service',
                'restart_cmd': 'systemctl restart rabbitmq-server',
                'terminate_cmd': 'systemctl stop rabbitmq-server',
                'start_cmd': 'systemctl start rabbitmq-server',
            }
        },
        'nova-api': {
            'driver': 'systemd_service',
            'args': {
                'grep': 'n-api',
                'unit_name': 'n-api.service',
            }
        },
        'glance-api': {
            'driver': 'systemd_service',
            'args': {
                'grep': 'glance-api',
                'unit_name': 'g-api.service',
            }
        },
        'nova-compute': {
            'driver': 'systemd_service',
            'args': {
                'grep': 'n-cpu',
                'unit_name': 'n-cpu.service',
            }
        },
        'nova-scheduler': {
            'driver': 'systemd_service',
            'args': {
                'grep': 'n-sch',
                'unit_name': 'n-sch.service',
            }
        },
        'ironic-api': {
            'driver': 'systemd_service',
            'args': {
                'grep': 'ir-api',
                'unit_name': 'ir-api.service',
            }
        },
        'ironic-conductor': {
            'driver': 'systemd_service',
            'args': {
                'grep': 'ir-cond',
                'unit_name': 'ir-cond.service',
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

    def __init__(self, cloud_management_params):
        super(DevStackSystemdManagement, self).__init__()
        self.node_discover = self  # supports discovering

        self.address = cloud_management_params['address']
        self.username = cloud_management_params['username']
        self.private_key_file = cloud_management_params.get('private_key_file')
        self.slaves = cloud_management_params.get('slaves', [])
        self.iface = cloud_management_params.get('iface', 'eth0')
        self.serial = cloud_management_params.get('serial')

        self.cloud_executor = executor.AnsibleRunner(
            remote_user=self.username, private_key_file=self.private_key_file,
            password=cloud_management_params.get('password'),
            become=True, serial=self.serial)

        self.hosts = [node_collection.Host(ip=self.address)]
        if self.slaves:
            self.hosts.extend([node_collection.Host(ip=h)
                               for h in self.slaves])
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

            self.nodes = [node_collection.Host(ip=r.host,
                                               mac=r.payload['stdout'],
                                               fqdn='')
                          for r in results]

        return self.nodes
