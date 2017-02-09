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
from os_faults.common import service

LOG = logging.getLogger(__name__)


class KeystoneService(service.ServiceInDocker):
    SERVICE_NAME = 'keystone'
    GREP_CONTAINER = 'keystone'
    GREP_PROCESS = 'apache2'


class HorizonService(service.ServiceInDocker):
    SERVICE_NAME = 'horizon'
    GREP_CONTAINER = 'horizon'
    GREP_PROCESS = 'apache2'


class MySQLService(service.ServiceInDocker):
    SERVICE_NAME = 'mysql'
    GREP_CONTAINER = 'mariadb'
    GREP_PROCESS = 'mysqld'


class MemcachedService(service.ServiceInDocker):
    SERVICE_NAME = 'memcached'
    GREP_CONTAINER = 'memcached'
    GREP_PROCESS = 'memcached'


class RabbitMQService(service.ServiceInDocker):
    SERVICE_NAME = 'rabbitmq'
    GREP_CONTAINER = 'rabbitmq'
    GREP_PROCESS = 'beam\.smp .*rabbitmq_server'


class GlanceAPIService(service.ServiceInDocker):
    SERVICE_NAME = 'glance-api'
    GREP_CONTAINER = 'glance-api'
    GREP_PROCESS = 'python .*/glance-api'


class GlanceRegistryService(service.ServiceInDocker):
    SERVICE_NAME = 'glance-registry'
    GREP_CONTAINER = 'glance-registry'
    GREP_PROCESS = 'python .*/glance-registry'


class HeatAPIService(service.ServiceInDocker):
    SERVICE_NAME = 'heat-api'
    GREP_CONTAINER = 'heat-api '
    GREP_PROCESS = 'python .*/heat-api'


class HeatAPICfnService(service.ServiceInDocker):
    SERVICE_NAME = 'heat-api-cfn'
    GREP_CONTAINER = 'heat-api-cfn'
    GREP_PROCESS = 'python .*/heat-api-cfn'


class HeatEngineService(service.ServiceInDocker):
    SERVICE_NAME = 'heat-engine'
    GREP_CONTAINER = 'heat-engine'
    GREP_PROCESS = 'python .*/heat-engine'


class NeutronDhcpAgentService(service.ServiceInDocker):
    SERVICE_NAME = 'neutron-dhcp-agent'
    GREP_CONTAINER = 'neutron-dhcp-agent'
    GREP_PROCESS = 'python .*/neutron-dhcp-agent'


class NeutronL3AgentService(service.ServiceInDocker):
    SERVICE_NAME = 'neutron-l3-agent'
    GREP_CONTAINER = 'neutron-l3-agent'
    GREP_PROCESS = 'python .*/neutron-l3-agent'


class NeutronMetadataAgentService(service.ServiceInDocker):
    SERVICE_NAME = 'neutron-metadata-agent'
    GREP_CONTAINER = 'neutron-metadata-agent'
    GREP_PROCESS = 'python .*/neutron-metadata-agent'


class NeutronOpenVSwitchAgentService(service.ServiceInDocker):
    SERVICE_NAME = 'neutron-openvswitch-agent'
    GREP_CONTAINER = 'neutron-openvswitch-agent'
    GREP_PROCESS = 'python .*/neutron-openvswitch-agent'


class NeutronServerService(service.ServiceInDocker):
    SERVICE_NAME = 'neutron-server'
    GREP_CONTAINER = 'neutron-server'
    GREP_PROCESS = 'python .*/neutron-server'


class NovaAPIService(service.ServiceInDocker):
    SERVICE_NAME = 'nova-api'
    GREP_CONTAINER = 'nova-api'
    GREP_PROCESS = 'python .*/nova-api'


class NovaComputeService(service.ServiceInDocker):
    SERVICE_NAME = 'nova-compute'
    GREP_CONTAINER = 'nova-compute'
    GREP_PROCESS = 'python .*/nova-compute'


class NovaConductorService(service.ServiceInDocker):
    SERVICE_NAME = 'nova-conductor'
    GREP_CONTAINER = 'nova-conductor'
    GREP_PROCESS = 'python .*/nova-conductor'


class NovaConsoleAuthService(service.ServiceInDocker):
    SERVICE_NAME = 'nova-consoleauth'
    GREP_CONTAINER = 'nova-consoleauth'
    GREP_PROCESS = 'python .*/nova-consoleauth'


class NovaLibvirtService(service.ServiceInDocker):
    SERVICE_NAME = 'nova-libvirt'
    GREP_CONTAINER = 'nova-libvirt'
    GREP_PROCESS = 'libvirtd'


class NovaNoVNCProxyService(service.ServiceInDocker):
    SERVICE_NAME = 'nova-novncproxy'
    GREP_CONTAINER = 'nova-novncproxy'
    GREP_PROCESS = 'python .*/nova-novncproxy'


class NovaSchedulerService(service.ServiceInDocker):
    SERVICE_NAME = 'nova-scheduler'
    GREP_CONTAINER = 'nova-scheduler'
    GREP_PROCESS = 'python .*/nova-scheduler'


class NovaVirtlogdService(service.ServiceInDocker):
    SERVICE_NAME = 'nova-virtlogd'
    GREP_CONTAINER = 'nova-virtlogd'
    GREP_PROCESS = 'virtlogd'


class OpenVSwitchDBService(service.ServiceInDocker):
    SERVICE_NAME = 'openvswitch-db'
    GREP_CONTAINER = 'openvswitch-db'
    GREP_PROCESS = 'ovsdb-server'


class OpenVSwitchVSwitchdService(service.ServiceInDocker):
    SERVICE_NAME = 'openvswitch-vswitchd'
    GREP_CONTAINER = 'openvswitch-vswitchd'
    GREP_PROCESS = 'ovs-vswitchd'


class MCPManagement(cloud_management.CloudManagement):
    """MCP Driver.

    Nodes for this driver must be provided by a node_discover driver such
    as node_list.

    **Example configuration:**

    cloud_management:
      driver: mcp
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

    NAME = 'mcp'
    DESCRIPTION = 'MCP cloud management driver'
    SERVICE_NAME_TO_CLASS = {
        'keystone': KeystoneService,
        'horizon': HorizonService,
        'mysql': MySQLService,
        'memcached': MemcachedService,
        'rabbitmq': RabbitMQService,
        'glance-api': GlanceAPIService,
        'glance-registry': GlanceRegistryService,
        'heat-api': HeatAPIService,
        'heat-api-cfn': HeatAPICfnService,
        'heat-engine': HeatEngineService,
        'neutron-dhcp-agent': NeutronDhcpAgentService,
        'neutron-l3-agent': NeutronL3AgentService,
        'neutron-metadata-agent': NeutronMetadataAgentService,
        'neutron-openvswitch-agent': NeutronOpenVSwitchAgentService,
        'neutron-server': NeutronServerService,
        'nova-api': NovaAPIService,
        'nova-compute': NovaComputeService,
        'nova-conductor': NovaConductorService,
        'nova-consoleauth': NovaConsoleAuthService,
        'nova-libvirt': NovaLibvirtService,
        'nova-novncproxy': NovaNoVNCProxyService,
        'nova-scheduler': NovaSchedulerService,
        'nova-virtlogd': NovaVirtlogdService,
        'openvswitch-db': OpenVSwitchDBService,
        'openvswitch-vswitchd': OpenVSwitchVSwitchdService,
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
        super(MCPManagement, self).__init__()
        params = cloud_management_params

        self.cloud_executor = executor.AnsibleRunner(
            remote_user=params['username'],
            password=params.get('password'),
            private_key_file=params.get('private_key_file'),
            jump_host=params.get('jump_host'),
            jump_user=params.get('jump_user'),
            become=params.get('sudo', False))

    def verify(self):
        """Verify connection to the cloud."""
        nodes = self.get_nodes()
        LOG.debug('Cloud nodes: %s', nodes)

        task = {'command': 'hostname'}
        task_result = self.execute_on_cloud(nodes.get_ips(), task)
        LOG.debug('Hostnames of cloud nodes: %s',
                  [r.payload['stdout'] for r in task_result])

        LOG.info('Connected to cloud successfully!')

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
