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
            'systemd_service': {'type': 'string'},
            'grep': {'type': 'string'},
            'port': service.PORT_SCHEMA,
        },
        'required': ['grep', 'systemd_service'],
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
        'keystone': {  # get_nodes() could get nodes with it, ok
            'driver': 'systemd_service',
            'args': {
                'grep': 'apache2',
                'systemd_service': 'keystone.service',
                # can restart, terminate and start
            }
        },
        'mysql': {  # get_nodes() could get nodes with it, ok
            'driver': 'systemd_service',
            'args': {
                'grep': 'mysqld',
                'systemd_service': 'mysql.service',
                'restart_cmd': 'systemctl restart mysql',  # Execution failed
                'terminate_cmd': 'systemctl stop mysql',  # Execution failed
                'start_cmd': 'systemctl start mysql',  # Execution failed
                'port': ['tcp', 3307],
            }
        },
        'rabbitmq': {  # get_nodes() could get nodes with it, ok
            'driver': 'systemd_service',
            'args': {
                'grep': 'rabbitmq-server',
                'systemd_service': 'rabbit.service',  # Execution failed
                'restart_cmd': 'systemctl restart rabbitmq-server',
                'terminate_cmd': 'systemctl stop rabbitmq-server',
                'start_cmd': 'systemctl start rabbitmq-server',
            }
        },
        'nova-api': {  # get_nodes() could get nodes with it, ok
            'driver': 'systemd_service',  # can restart, terminate, start
            'args': {
                'grep': 'nova-api',
                'systemd_service': 'n-api.service',
            }
        },
        'glance-api': {  # get_nodes() could get nodes with it, ok
            'driver': 'systemd_service',  # can restart, terminate, start
            'args': {
                'grep': 'glance-api',
                'systemd_service': 'g-api.service',
            }
        },
        'nova-compute': {
            'driver': 'systemd_service',  # can not get_nodes() with n-cpu
            'args': {
                'grep': 'n-cpu',
                'systemd_service': 'n-cpu.service',
            }
        },
        'nova-scheduler': {    # can not get_nodes() with n-sch
            'driver': 'systemd_service',
            'args': {
                'grep': 'n-sch',
                'systemd_service': 'n-sch.service',
            }
        },
        'ironic-api': {  # can not get_nodes() with ir-api
            'driver': 'systemd_service',
            'args': {
                'grep': 'ir-api',
                'systemd_service': 'ir-api.service',
            }
        },
        'ironic-conductor': {    # can not get_nodes() with ir-api
            'driver': 'systemd_service',
            'args': {
                'grep': 'ir-cond',
                'systemd_service': 'ir-cond.service',
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
