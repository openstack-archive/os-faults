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
from os_faults import utils

LOG = logging.getLogger(__name__)


class DevStackNode(node_collection.NodeCollection):

    def connect(self, network_name):
        raise NotImplementedError

    def disconnect(self, network_name):
        raise NotImplementedError


class ServiceInScreen(service.ServiceAsProcess):

    @utils.require_variables('WINDOW_NAME')
    def __init__(self, *args, **kwargs):
        super(ServiceInScreen, self).__init__(*args, **kwargs)

        # sends ctr+c, arrow up key, enter key
        self.RESTART_CMD = (
            "screen -S stack -p {window_name} -X "
            "stuff $'\\003'$'\\033[A'$(printf \\\\r)").format(
                window_name=self.WINDOW_NAME)

        # sends ctr+c
        self.TERMINATE_CMD = (
            "screen -S stack -p {window_name} -X "
            "stuff $'\\003'").format(
                window_name=self.WINDOW_NAME)

        # sends arrow up key, enter key
        self.START_CMD = (
            "screen -S stack -p {window_name} -X "
            "stuff $'\\033[A'$(printf \\\\r)").format(
                window_name=self.WINDOW_NAME)


class KeystoneService(service.ServiceAsProcess):
    SERVICE_NAME = 'keystone'
    GREP = 'keystone-'
    RESTART_CMD = 'sudo service apache2 restart'
    TERMINATE_CMD = 'sudo service apache2 stop'
    START_CMD = 'sudo service apache2 start'


class MySQLService(service.ServiceAsProcess):
    SERVICE_NAME = 'mysql'
    GREP = 'mysqld'
    RESTART_CMD = 'sudo service mysql restart'
    TERMINATE_CMD = 'sudo service mysql stop'
    START_CMD = 'sudo service mysql start'
    PORT = ('tcp', 3307)


class RabbitMQService(service.ServiceAsProcess):
    SERVICE_NAME = 'rabbitmq'
    GREP = 'rabbitmq-server'
    RESTART_CMD = 'sudo service rabbitmq-server restart'
    TERMINATE_CMD = 'sudo service rabbitmq-server stop'
    START_CMD = 'sudo service rabbitmq-server start'


class NovaAPIService(ServiceInScreen):
    SERVICE_NAME = 'nova-api'
    GREP = 'nova-api'
    WINDOW_NAME = 'n-api'


class GlanceAPIService(ServiceInScreen):
    SERVICE_NAME = 'glance-api'
    GREP = 'glance-api'
    WINDOW_NAME = 'g-api'


class NovaComputeService(ServiceInScreen):
    SERVICE_NAME = 'nova-compute'
    GREP = 'nova-compute'
    WINDOW_NAME = 'n-cpu'


class NovaSchedulerService(ServiceInScreen):
    SERVICE_NAME = 'nova-scheduler'
    GREP = 'nova-scheduler'
    WINDOW_NAME = 'n-sch'


class IronicApiService(ServiceInScreen):
    SERVICE_NAME = 'ironic-api'
    GREP = 'ironic-api'
    WINDOW_NAME = 'ir-api'


class IronicConductorService(ServiceInScreen):
    SERVICE_NAME = 'ironic-conductor'
    GREP = 'ironic-conductor'
    WINDOW_NAME = 'ir-cond'


class DevStackManagement(cloud_management.CloudManagement,
                         node_discover.NodeDiscover):
    """Devstack driver.

    This driver requires devstack installed in screen mode (USE_SCREEN=True).
    Supports discovering of node MAC addreses.

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
    - **iface** - network interface name to retrive mac address (optional)
    """

    NAME = 'devstack'
    DESCRIPTION = 'DevStack management driver'
    NODE_CLS = DevStackNode
    SERVICE_NAME_TO_CLASS = {
        'keystone': KeystoneService,
        'mysql': MySQLService,
        'rabbitmq': RabbitMQService,
        'nova-api': NovaAPIService,
        'glance-api': GlanceAPIService,
        'nova-compute': NovaComputeService,
        'nova-scheduler': NovaSchedulerService,
        'ironic-api': IronicApiService,
        'ironic-conductor': IronicConductorService,
    }
    SUPPORTED_SERVICES = list(SERVICE_NAME_TO_CLASS.keys())
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

        self.cloud_executor = executor.AnsibleRunner(
            remote_user=self.username, private_key_file=self.private_key_file,
            password=cloud_management_params.get('password'),
            become=False)

        self.hosts = [self.address]
        if self.slaves:
            self.hosts.extend(self.slaves)
        self.nodes = None

    def verify(self):
        """Verify connection to the cloud."""
        nodes = self.get_nodes()
        task = {'shell': 'screen -ls | grep -P "\\d+\\.stack"'}
        results = self.execute_on_cloud(nodes.get_ips(), task)
        hostnames = [result.host for result in results]
        LOG.debug('DevStack hostnames: %s', hostnames)
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
