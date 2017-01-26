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
          - ip: 10.0.0.52
            mac: aa:bb:cc:dd:ee:02
            fqdn: node2.local
          - ip: 10.0.0.53
            mac: aa:bb:cc:dd:ee:03
            fqdn: node3.local
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
                'mac': {
                    'type': 'string',
                    'pattern': utils.MACADDR_REGEXP,
                },
                'fqdn': {'type': 'string'},
            },
            'required': ['ip', 'mac', 'fqdn'],
            'additionalProperties': False,
        },
        'minItems': 1,
    }

    def __init__(self, conf):
        self.hosts = [node_collection.Host(ip=host['ip'], mac=host['mac'],
                                           fqdn=host['fqdn']) for host in conf]

    def discover_hosts(self):
        """Discover hosts

        :returns: list of Host instances
        """
        return self.hosts
