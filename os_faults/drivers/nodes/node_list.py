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


from os_faults.api import node_collection
from os_faults.api import node_discover
from os_faults import utils


AUTH_SCHEMA = {
    'type': 'object',
    'properties': {
        'username': {'type': 'string'},
        'password': {'type': 'string'},
        'private_key_file': {'type': 'string'},
        'become_password': {'type': 'string'},
        'jump': {
            'type': 'object',
            'properties': {
                'host': {'type': 'string'},
                'username': {'type': 'string'},
                'private_key_file': {'type': 'string'},
            },
            'required': ['host'],
            'additionalProperties': False,
        },
    },
    'additionalProperties': False,
}


class NodeListDiscover(node_discover.NodeDiscover):
    """Node list.

    Allows specifying list of nodes in configuration.

    **Example configuration:**

    .. code-block:: yaml

        node_discover:
          driver: node_list
          args:
          - ip: 10.0.0.51
            mac: aa:bb:cc:dd:ee:01
            fqdn: node1.local
            libvirt_name: node1
          - ip: 192.168.1.50
            mac: aa:bb:cc:dd:ee:02
            fqdn: node2.local
            auth:
              username: user1
              password: secret1
              jump:
                host: 10.0.0.52
                username: ubuntu
                private_key_file: /path/to/file
          - ip: 10.0.0.53
            mac: aa:bb:cc:dd:ee:03
            fqdn: node3.local
            become_password: my_secret_password

    node parameters:

    - **ip** - ip/host of the node
    - **mac** - MAC address of the node (optional).
      MAC address is used for libvirt driver.
    - **fqdn** - FQDN of the node (optional).
      FQDN is used for filtering only.
    - **auth** - SSH related parameters (optional):
        - **username** - SSH username (optional)
        - **password** - SSH password (optional)
        - **private_key_file** - SSH key file (optional)
        - **become_password** - privilege escalation password (optional)
        - **jump** - SSH proxy parameters (optional):
            - **host** - SSH proxy host
            - **username** - SSH proxy user
            - **private_key_file** - SSH proxy key file (optional)

    """

    NAME = 'node_list'
    DESCRIPTION = 'Reads hosts from configuration file'
    CONFIG_SCHEMA = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': {
                'ip': {'type': 'string'},
                'mac': {'type': 'string', 'pattern': utils.MACADDR_REGEXP},
                'fqdn': {'type': 'string'},
                'libvirt_name': {'type': 'string'},
                'auth': AUTH_SCHEMA,
            },
            'required': ['ip'],
            'additionalProperties': False,
        },
        'minItems': 1,
    }

    def __init__(self, conf):
        self.hosts = [node_collection.Host(**host) for host in conf]

    def discover_hosts(self):
        """Discover hosts

        :returns: list of Host instances
        """
        return self.hosts
