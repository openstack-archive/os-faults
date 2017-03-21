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


class KeystoneService(service.ServiceInKubernetes):
    SERVICE_NAME = 'keystone'
    SELECTOR = 'app=keystone'
    GREP_PROCESS = 'apache2'


class MemcachedService(service.ServiceInKubernetes):
    SERVICE_NAME = 'memcached'
    SELECTOR = 'app=memcached'
    GREP_PROCESS = 'memcached'


class MysqlService(service.ServiceInKubernetes):
    SERVICE_NAME = 'mysql'
    SELECTOR = 'app=database'
    CONTAINER = 'galera'
    GREP_PROCESS = 'mysql'


class RabbitmqService(service.ServiceInKubernetes):
    SERVICE_NAME = 'rabbitmq'
    SELECTOR = 'app=rpc'
    CONTAINER = 'rabbitmq'
    GREP_PROCESS = 'erlang'


class FuelCCPManagement(cloud_management.CloudManagement,
                        node_discover.NodeDiscover):
    """Fuel-CCP Driver.

    Cloud deployed by fuel-ccp. Supports discovering of slave nodes.

    **Example configuration:**

    .. code-block:: yaml

        cloud_management:
          driver: fuel-ccp
          args:
            username: user
            password: pass
            jump_host: 192.168.1.40
            jump_user: ubuntu
            sudo: True

    parameters:

    - **username** - username for all nodes
    - **private_key_file** - path to key file (optional)
    - **password** - password for all nodes (optional)
    - **jump_host** - ssh proxy host (optional)
    - **jump_user** - ssh proxy user (optional)
    - **sudo** - Use sudo on all nodes (optional)

    """

    NAME = 'fuel-ccp'
    DESCRIPTION = 'Fuel-CCP cloud management driver'
    SERVICE_NAME_TO_CLASS = {
        'keystone': KeystoneService,
        'memcached': MemcachedService,
        'mysql': MysqlService,
        'rabbitmq': RabbitmqService,
    }
    SUPPORTED_SERVICES = list(SERVICE_NAME_TO_CLASS.keys())
    SUPPORTED_NETWORKS = []
    CONFIG_SCHEMA = {
        'type': 'object',
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'properties': {
            'username': {'type': 'string'},
            'password': {'type': 'string'},
            'private_key_file': {'type': 'string'},
            'jump_host': {'type': 'string'},
            'jump_user': {'type': 'string'},
            'sudo': {'type': 'boolean'},
        },
        'required': ['username'],
        'additionalProperties': False,
    }

    def __init__(self, cloud_management_params):
        super(FuelCCPManagement, self).__init__()
        self.node_discover = self  # supports discovering
        params = cloud_management_params

        self.cloud_executor = executor.AnsibleRunner(
            remote_user=params['username'],
            password=params.get('password'),
            private_key_file=params.get('private_key_file'),
            jump_host=params.get('jump_host'),
            jump_user=params.get('jump_user'),
            become=params.get('sudo', False))

        self.kubectl_host = params.get('jump_host')
        self.kubectl_node_executor = executor.AnsibleRunner(
            remote_user=params['username'],
            password=params.get('password'),
            private_key_file=params.get('private_key_file'),
            become=params.get('sudo', False))

        self.cached_cloud_hosts = list()

    def verify(self):
        """Verify connection to the cloud."""
        nodes = self.get_nodes()
        LOG.debug('Cloud nodes: %s', nodes)

        task = {'command': 'hostname'}
        task_result = self.execute_on_cloud(nodes.get_ips(), task)
        LOG.debug('Hostnames of cloud nodes: %s',
                  [r.payload['stdout'] for r in task_result])

        LOG.info('Connected to cloud successfully!')

    def discover_hosts(self):
        if not self.cached_cloud_hosts:
            task = {'kubernetes_get_nodes': {}}
            result = self.execute_on_kubernetes_node(task)

            kube_response = result[0].payload['response']
            for item in kube_response['items']:
                addresses_list = item['status']['addresses']
                r = dict((x['type'], x['address']) for x in addresses_list)

                host = node_collection.Host(ip=r['InternalIP'], mac='',
                                            fqdn=r['Hostname'])
                self.cached_cloud_hosts.append(host)

        return self.cached_cloud_hosts

    def execute_on_kubernetes_node(self, task):
        """Execute task on Kubernetes master node.

        :param task: Ansible task
        :return: Ansible execution result (list of records)
        """
        return self.kubectl_node_executor.execute([self.kubectl_host], task)

    def execute_on_cloud(self, hosts, task, raise_on_error=True):
        """Execute task on specified hosts within the cloud.

        :param hosts: List of host FQDNs
        :param task: Ansible task
        :param raise_on_error: throw exception in case of error
        :returns: Ansible execution result (list of records)
        """
        if raise_on_error:
            return self.cloud_executor.execute(hosts, task)
        else:
            return self.cloud_executor.execute(hosts, task, [])
