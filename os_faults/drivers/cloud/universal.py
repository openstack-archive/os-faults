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

LOG = logging.getLogger(__name__)


class UniversalCloudManagement(cloud_management.CloudManagement):
    """Universal cloud management driver

    This driver is suitable for the most abstract (and thus universal) case.
    The driver does not have any built-in services nor node discovery
    capabilities. All services need to be listed explicitly in a config file.
    Node list is specified using `node_list` node discovery driver.

    **Example of multi-node configuration:**

    Note that in this configuration a node discovery driver is required.

    .. code-block:: yaml

        cloud_management:
          driver: universal

        node_discover:
          driver: node_list
          args:
            - ip: 192.168.5.149
              auth:
                username: developer
                private_key_file: cloud_key
                become_password: my_secret_password
            - ip: 192.168.5.150
              auth:
                username: developer
                private_key_file: cloud_key
                become_password: my_secret_password

    """

    NAME = 'universal'
    DESCRIPTION = 'Universal cloud management driver'
    CONFIG_SCHEMA = {
        'type': 'object',
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'properties': {},
        'additionalProperties': False,
    }

    def __init__(self, cloud_management_params):
        super(UniversalCloudManagement, self).__init__()

        self.cloud_executor = executor.AnsibleRunner()

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
