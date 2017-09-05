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
from os_faults.api import error
from os_faults.api import node_collection
from os_faults.api import node_discover

LOG = logging.getLogger(__name__)


class UniversalCloudManagement(cloud_management.CloudManagement,
                               node_discover.NodeDiscover):
    """Universal cloud management driver

    This driver is suitable for the most abstract case. It does not have any
    built-in services, all services need to be specified explicitly in
    a config file.

    By default the Universal driver works with only one node. To specify
    more nodes use `node_list` node discovery driver. Authentication
    parameters are then overridden by corresponding parameters from node
    discovery.

    **Example configuration (single node):**

    .. code-block:: yaml

        cloud_management:
          driver: universal
          args:
            address: 192.168.1.10
            username: ubuntu
            password: ubuntu_pass
            private_key_file: ~/.ssh/id_rsa_devstack
            become: true
            become_password: my_secret_password
            iface: eth1
            serial: 10

    **Example configuration (multiple nodes):**

    Note that in this configuration a node discovery driver is required.

    .. code-block:: yaml

        cloud_management:
          driver: universal

        node_discovery:
          driver: node_list
          args:
            - ip: 192.168.5.149
              auth:
                username: developer
                private_key_file: cloud_key
                become: true
                become_password: swordfish

    parameters:

    - **address** - ip address of any devstack node
    - **username** - username for all nodes
    - **password** - password for all nodes (optional)
    - **private_key_file** - path to key file (optional)
    - **become** - True if privilege escalation is used (optional)
    - **become_password** - privilege escalation password (optional)
    - **iface** - network interface name to retrieve mac address (optional)
    - **serial** - how many hosts Ansible should manage at a single time.
      (optional) default: 10
    """

    NAME = 'universal'
    DESCRIPTION = 'Universal cloud management driver'
    CONFIG_SCHEMA = {
        'type': 'object',
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'properties': {
            'address': {'type': 'string'},
            'username': {'type': 'string'},
            'password': {'type': 'string'},
            'private_key_file': {'type': 'string'},
            'become': {'type': 'boolean'},
            'become_password': {'type': 'string'},
            'iface': {'type': 'string'},
            'serial': {'type': 'integer', 'minimum': 1},
        },
        'required': ['address', 'username'],
        'additionalProperties': False,
    }

    def __init__(self, cloud_management_params):
        super(UniversalCloudManagement, self).__init__()
        self.node_discover = self  # can discover itself

        self.address = cloud_management_params.get('address')
        self.username = cloud_management_params.get('username')
        self.private_key_file = cloud_management_params.get('private_key_file')
        self.become = cloud_management_params.get('become')
        self.become_password = cloud_management_params.get('become_password')
        self.slaves = cloud_management_params.get('slaves', [])
        self.iface = cloud_management_params.get('iface')
        self.serial = cloud_management_params.get('serial')
        password = cloud_management_params.get('password')

        self.cloud_executor = executor.AnsibleRunner(
            remote_user=self.username, private_key_file=self.private_key_file,
            password=password, become=self.become,
            become_password=self.become_password, serial=self.serial)

        self.hosts = [node_collection.Host(ip=self.address)]
        self.discovered = False

    def verify(self):
        """Verify connection to the cloud."""
        nodes = self.get_nodes()
        if not nodes:
            raise error.OSFError('Cloud has no nodes')

        task = {'command': 'hostname'}
        task_result = self.execute_on_cloud(nodes.hosts, task)
        LOG.debug('Host names of cloud nodes: %s',
                  ', '.join(r.payload['stdout'] for r in task_result))

        LOG.info('Connected to cloud successfully!')

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
        if not self.discovered:
            # extend hosts with host name and MAC address (if iface provided)
            LOG.debug('Discovering host name and MAC address')

            host2mac = {}
            if self.iface:
                cmd = 'cat /sys/class/net/{}/address'.format(self.iface)
                res = self.execute_on_cloud(self.hosts, {'command': cmd})
                host2mac = dict((r.host, r.payload['stdout']) for r in res)

            res = self.execute_on_cloud(self.hosts, {'command': 'hostname'})
            host2hostname = dict((r.host, r.payload['stdout']) for r in res)

            self.hosts = [node_collection.Host(ip=h,
                                               mac=host2mac.get(h),
                                               fqdn=host2hostname[h])
                          for h in host2hostname.keys()]
            self.discovered = True
        return self.hosts
