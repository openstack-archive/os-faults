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
from os_faults.drivers import shared_schemas

LOG = logging.getLogger(__name__)


class UniversalCloudManagement(cloud_management.CloudManagement,
                               node_discover.NodeDiscover):
    """Universal cloud management driver

    This driver is suitable for the most abstract (and thus universal) case.
    The driver does not have any built-in services, all services need
    to be listed explicitly in a config file.

    By default the Universal driver works with only one node. To specify
    more nodes use `node_list` node discovery driver. Authentication
    parameters can be shared or overridden by corresponding parameters
    from node discovery.

    **Example single node configuration:**

    .. code-block:: yaml

        cloud_management:
          driver: universal
          args:
            address: 192.168.1.10
            auth:
              username: ubuntu
              private_key_file: devstack_key
              become: true
              become_password: my_secret_password
            iface: eth1
            serial: 10

    **Example multi-node configuration:**

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
                become_password: my_secret_password

    parameters:

    - **address** - address of the node (optional, but if not set
      a node discovery driver is mandatory)
    - **auth** - SSH related parameters (optional):
        - **username** - SSH username (optional)
        - **password** - SSH password (optional)
        - **private_key_file** - SSH key file (optional)
        - **become** - True if privilege escalation is used (optional)
        - **become_password** - privilege escalation password (optional)
        - **jump** - SSH proxy parameters (optional):
            - **host** - SSH proxy host
            - **username** - SSH proxy user
            - **private_key_file** - SSH proxy key file (optional)
    - **iface** - network interface name to retrieve mac address (optional)
    - **serial** - how many hosts Ansible should manage at a single time
      (optional) default: 10
    """

    NAME = 'universal'
    DESCRIPTION = 'Universal cloud management driver'
    CONFIG_SCHEMA = {
        'type': 'object',
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'properties': {
            'address': {'type': 'string'},
            'auth': shared_schemas.AUTH_SCHEMA,
            'iface': {'type': 'string'},
            'serial': {'type': 'integer', 'minimum': 1},
        },
        'additionalProperties': False,
    }

    def __init__(self, cloud_management_params):
        super(UniversalCloudManagement, self).__init__()
        self.node_discover = self  # by default can discover itself

        self.address = cloud_management_params.get('address')
        self.iface = cloud_management_params.get('iface')
        serial = cloud_management_params.get('serial')

        auth = cloud_management_params.get('auth') or {}
        jump = auth.get('jump') or {}

        self.cloud_executor = executor.AnsibleRunner(
            remote_user=auth.get('username'),
            password=auth.get('password'),
            private_key_file=auth.get('private_key_file'),
            become=auth.get('become'),
            become_password=auth.get('become_password'),
            jump_host=jump.get('host'),
            jump_user=jump.get('user'),
            serial=serial,
        )

        self.cached_hosts = None  # cache for node discovery

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
        # this function is called when no node-discovery driver is specified;
        # discover the default host set in config for this driver

        if not self.address:
            raise error.OSFError('Cloud has no nodes. Specify address in '
                                 'cloud management driver or add node '
                                 'discovery driver')

        if not self.cached_hosts:
            LOG.info('Discovering host name and MAC address for %s',
                     self.address)
            host = node_collection.Host(ip=self.address)

            mac = None
            if self.iface:
                cmd = 'cat /sys/class/net/{}/address'.format(self.iface)
                res = self.execute_on_cloud([host], {'command': cmd})
                mac = res[0].payload['stdout']

            res = self.execute_on_cloud([host], {'command': 'hostname'})
            hostname = res[0].payload['stdout']

            # update my hosts
            self.cached_hosts = [node_collection.Host(
                ip=self.address, mac=mac, fqdn=hostname)]

        return self.cached_hosts
