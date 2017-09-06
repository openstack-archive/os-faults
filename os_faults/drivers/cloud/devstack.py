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
from os_faults.drivers.services import process

LOG = logging.getLogger(__name__)


class DevStackNode(node_collection.NodeCollection):

    def connect(self, network_name):
        raise NotImplementedError

    def disconnect(self, network_name):
        raise NotImplementedError


class ServiceInScreen(process.ServiceAsProcess):
    """Service in Screen

    This driver controls service that is started in a window of
    `screen` tool.

    **Example configuration:**

    .. code-block:: yaml

        services:
          app:
            driver: screen
            args:
              window_name: app
              grep: my_app
              port: ['tcp', 4242]

    parameters:

    - **window_name** - name of a service
    - **grep** - regexp for grep to find process PID
    - **port** - tuple with two values - protocol, port number (optional)

    """
    NAME = 'screen'
    DESCRIPTION = 'Service in screen'
    CONFIG_SCHEMA = {
        'type': 'object',
        'properties': {
            'window_name': {'type': 'string'},
            'grep': {'type': 'string'},
            'port': process.PORT_SCHEMA,
        },
        'required': ['grep', 'window_name'],
        'additionalProperties': False,
    }

    def __init__(self, *args, **kwargs):
        super(ServiceInScreen, self).__init__(*args, **kwargs)
        self.window_name = self.config['window_name']

        # sends ctr+c, arrow up key, enter key
        self.restart_cmd = (
            "screen -S stack -p {window_name} -X "
            "stuff $'\\003'$'\\033[A'$(printf \\\\r)").format(
                window_name=self.window_name)

        # sends ctr+c
        self.terminate_cmd = (
            "screen -S stack -p {window_name} -X "
            "stuff $'\\003'").format(
                window_name=self.window_name)

        # sends arrow up key, enter key
        self.start_cmd = (
            "screen -S stack -p {window_name} -X "
            "stuff $'\\033[A'$(printf \\\\r)").format(
                window_name=self.window_name)


class DevStackManagement(cloud_management.CloudManagement,
                         node_discover.NodeDiscover):
    """Devstack driver.

    This driver requires devstack installed in screen mode (USE_SCREEN=True).
    Supports discovering of node MAC addresses.

    **Example configuration:**

    .. code-block:: yaml

        cloud_management:
          driver: devstack
          args:
            address: 192.168.1.10
            username: ubuntu
            password: ubuntu_pass
            private_key_file: ~/.ssh/id_rsa_devstack
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

    NAME = 'devstack'
    DESCRIPTION = 'DevStack management driver'
    NODE_CLS = DevStackNode
    SERVICES = {
        'keystone': {
            'driver': 'process',
            'args': {
                'grep': 'keystone-',
                'restart_cmd': 'sudo service apache2 restart',
                'terminate_cmd': 'sudo service apache2 stop',
                'start_cmd': 'sudo service apache2 start',
            }
        },
        'mysql': {
            'driver': 'process',
            'args': {
                'grep': 'mysqld',
                'restart_cmd': 'sudo service mysql restart',
                'terminate_cmd': 'sudo service mysql stop',
                'start_cmd': 'sudo service mysql start',
                'port': ['tcp', 3307],
            }
        },
        'rabbitmq': {
            'driver': 'process',
            'args': {
                'grep': 'rabbitmq-server',
                'restart_cmd': 'sudo service rabbitmq-server restart',
                'terminate_cmd': 'sudo service rabbitmq-server stop',
                'start_cmd': 'sudo service rabbitmq-server start',
            }
        },
        'nova-api': {
            'driver': 'screen',
            'args': {
                'grep': 'nova-api',
                'window_name': 'n-api',
            }
        },
        'glance-api': {
            'driver': 'screen',
            'args': {
                'grep': 'glance-api',
                'window_name': 'g-api',
            }
        },
        'nova-compute': {
            'driver': 'screen',
            'args': {
                'grep': 'nova-compute',
                'window_name': 'n-cpu',
            }
        },
        'nova-scheduler': {
            'driver': 'screen',
            'args': {
                'grep': 'nova-scheduler',
                'window_name': 'n-sch',
            }
        },
        'ironic-api': {
            'driver': 'screen',
            'args': {
                'grep': 'ironic-api',
                'window_name': 'ir-api',
            }
        },
        'ironic-conductor': {
            'driver': 'screen',
            'args': {
                'grep': 'ironic-conductor',
                'window_name': 'ir-cond',
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
        super(DevStackManagement, self).__init__()
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
            become=False, serial=self.serial)

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

            # TODO(astudenov): support fqdn
            self.nodes = [node_collection.Host(ip=r.host,
                                               mac=r.payload['stdout'],
                                               fqdn='')
                          for r in results]

        return self.nodes
