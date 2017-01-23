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

import json
import logging

from os_faults.ansible import executor
from os_faults.api import cloud_management
from os_faults.api import node_collection
from os_faults.api import node_discover
from os_faults.common import service
from os_faults import utils

LOG = logging.getLogger(__name__)


class FuelNodeCollection(node_collection.NodeCollection):

    def connect(self, network_name):
        LOG.info("Connect network '%s' on nodes: %s", network_name, self)
        task = {'fuel_network_mgmt': {
            'network_name': network_name,
            'operation': 'up',
        }}
        self.cloud_management.execute_on_cloud(self.get_ips(), task)

    def disconnect(self, network_name):
        LOG.info("Disconnect network '%s' on nodes: %s",
                 network_name, self)
        task = {'fuel_network_mgmt': {
            'network_name': network_name,
            'operation': 'down',
        }}
        self.cloud_management.execute_on_cloud(self.get_ips(), task)


class PcsService(service.ServiceAsProcess):

    @utils.require_variables('PCS_SERVICE')
    def __init__(self, *args, **kwargs):
        super(PcsService, self).__init__(*args, **kwargs)

        self.RESTART_CMD = 'pcs resource restart {} $(hostname)'.format(
            self.PCS_SERVICE)
        self.TERMINATE_CMD = 'pcs resource ban {} $(hostname)'.format(
            self.PCS_SERVICE)
        self.START_CMD = 'pcs resource clear {} $(hostname)'.format(
            self.PCS_SERVICE)


class PcsOrLinuxService(service.ServiceAsProcess):

    @utils.require_variables('PCS_SERVICE', 'LINUX_SERVICE')
    def __init__(self, *args, **kwargs):
        super(PcsOrLinuxService, self).__init__(*args, **kwargs)

        self.RESTART_CMD = (
            'if pcs resource show {pcs_service}; '
            'then pcs resource restart {pcs_service} $(hostname); '
            'else service {linux_service} restart; fi').format(
                linux_service=self.LINUX_SERVICE,
                pcs_service=self.PCS_SERVICE)
        self.TERMINATE_CMD = (
            'if pcs resource show {pcs_service}; '
            'then pcs resource ban {pcs_service} $(hostname); '
            'else service {linux_service} stop; fi').format(
                linux_service=self.LINUX_SERVICE,
                pcs_service=self.PCS_SERVICE)
        self.START_CMD = (
            'if pcs resource show {pcs_service}; '
            'then pcs resource clear {pcs_service} $(hostname); '
            'else service {linux_service} start; fi').format(
                linux_service=self.LINUX_SERVICE,
                pcs_service=self.PCS_SERVICE)


class KeystoneService(service.LinuxService):
    SERVICE_NAME = 'keystone'
    GREP = '[k]eystone'
    LINUX_SERVICE = 'apache2'


class HorizonService(service.LinuxService):
    SERVICE_NAME = 'horizon'
    GREP = '[a]pache2'
    LINUX_SERVICE = 'apache2'


class MemcachedService(service.LinuxService):
    SERVICE_NAME = 'memcached'
    GREP = '[m]emcached'
    LINUX_SERVICE = 'memcached'


class MySQLService(PcsService):
    SERVICE_NAME = 'mysql'
    GREP = '[m]ysqld'
    PCS_SERVICE = 'p_mysqld'
    PORT = ('tcp', 3307)


class RabbitMQService(PcsService):
    SERVICE_NAME = 'rabbitmq'
    GREP = '[r]abbit tcp_listeners'
    PCS_SERVICE = 'p_rabbitmq-server'


class GlanceAPIService(service.LinuxService):
    SERVICE_NAME = 'glance-api'
    GREP = '[g]lance-api'
    LINUX_SERVICE = 'glance-api'


class GlanceGlareService(service.LinuxService):
    SERVICE_NAME = 'glance-glare'
    GREP = '[g]lance-glare'
    LINUX_SERVICE = 'glance-glare'


class GlanceRegistryService(service.LinuxService):
    SERVICE_NAME = 'glance-registry'
    GREP = '[g]lance-registry'
    LINUX_SERVICE = 'glance-registry'


class NovaAPIService(service.LinuxService):
    SERVICE_NAME = 'nova-api'
    GREP = '[n]ova-api'
    LINUX_SERVICE = 'nova-api'


class NovaComputeService(service.LinuxService):
    SERVICE_NAME = 'nova-compute'
    GREP = '[n]ova-compute'
    LINUX_SERVICE = 'nova-compute'


class NovaSchedulerService(service.LinuxService):
    SERVICE_NAME = 'nova-scheduler'
    GREP = '[n]ova-scheduler'
    LINUX_SERVICE = 'nova-scheduler'


class NovaCertService(service.LinuxService):
    SERVICE_NAME = 'nova-cert'
    GREP = '[n]ova-cert'
    LINUX_SERVICE = 'nova-cert'


class NovaConductorService(service.LinuxService):
    SERVICE_NAME = 'nova-conductor'
    GREP = '[n]ova-conductor'
    LINUX_SERVICE = 'nova-conductor'


class NovaConsoleAuthService(service.LinuxService):
    SERVICE_NAME = 'nova-consoleauth'
    GREP = '[n]ova-consoleauth'
    LINUX_SERVICE = 'nova-consoleauth'


class NovaNoVNCProxyService(service.LinuxService):
    SERVICE_NAME = 'nova-novncproxy'
    GREP = '[n]ova-novncproxy'
    LINUX_SERVICE = 'nova-novncproxy'


class NeutronServerService(service.LinuxService):
    SERVICE_NAME = 'neutron-server'
    GREP = '[n]eutron-server'
    LINUX_SERVICE = 'neutron-server'


class NeutronDhcpAgentService(PcsService):
    SERVICE_NAME = 'neutron-dhcp-agent'
    GREP = '[n]eutron-dhcp-agent'
    PCS_SERVICE = 'neutron-dhcp-agent'


class NeutronMetadataAgentService(PcsOrLinuxService):
    SERVICE_NAME = 'neutron-metadata-agent'
    GREP = '[n]eutron-metadata-agent'
    PCS_SERVICE = 'neutron-metadata-agent'
    LINUX_SERVICE = 'neutron-metadata-agent'


class NeutronOpenvswitchAgentService(PcsOrLinuxService):
    SERVICE_NAME = 'neutron-openvswitch-agent'
    GREP = '[n]eutron-openvswitch-agent'
    PCS_SERVICE = 'neutron-openvswitch-agent'
    LINUX_SERVICE = 'neutron-openvswitch-agent'


class NeutronL3AgentService(PcsOrLinuxService):
    SERVICE_NAME = 'neutron-l3-agent'
    GREP = '[n]eutron-l3-agent'
    PCS_SERVICE = 'neutron-l3-agent'
    LINUX_SERVICE = 'neutron-l3-agent'


class HeatAPIService(service.LinuxService):
    SERVICE_NAME = 'heat-api'
    GREP = '[h]eat-api'
    LINUX_SERVICE = 'heat-api'


class HeatEngineService(PcsService):
    SERVICE_NAME = 'heat-engine'
    GREP = '[h]eat-engine'
    PCS_SERVICE = 'p_heat-engine'


class CinderAPIService(service.LinuxService):
    SERVICE_NAME = 'cinder-api'
    GREP = '[c]inder-api'
    LINUX_SERVICE = 'cinder-api'


class CinderSchedulerService(service.LinuxService):
    SERVICE_NAME = 'cinder-scheduler'
    GREP = '[c]inder-scheduler'
    LINUX_SERVICE = 'cinder-scheduler'


class CinderVolumeService(service.LinuxService):
    SERVICE_NAME = 'cinder-volume'
    GREP = '[c]inder-volume'
    LINUX_SERVICE = 'cinder-volume'


class CinderBackupService(service.LinuxService):
    SERVICE_NAME = 'cinder-backup'
    GREP = '[c]inder-backup'
    LINUX_SERVICE = 'cinder-backup'


class IronicApiService(service.LinuxService):
    SERVICE_NAME = 'ironic-api'
    GREP = '[i]ronic-api'
    LINUX_SERVICE = 'ironic-api'


class IronicConductorService(service.LinuxService):
    SERVICE_NAME = 'ironic-conductor'
    GREP = '[i]ronic-conductor'
    LINUX_SERVICE = 'ironic-conductor'


class SwiftAccountService(service.LinuxService):
    SERVICE_NAME = 'swift-account'
    GREP = '[s]wift-account'
    LINUX_SERVICE = 'swift-account'


class SwiftAccountAuditorService(service.LinuxService):
    SERVICE_NAME = 'swift-account-auditor'
    GREP = '[s]wift-account-auditor'
    LINUX_SERVICE = 'swift-account-auditor'


class SwiftAccountReaperService(service.LinuxService):
    SERVICE_NAME = 'swift-account-reaper'
    GREP = '[s]wift-account-reaper'
    LINUX_SERVICE = 'swift-account-reaper'


class SwiftAccountReplicatorService(service.LinuxService):
    SERVICE_NAME = 'swift-account-replicator'
    GREP = '[s]wift-account-replicator'
    LINUX_SERVICE = 'swift-account-replicator'


class SwiftContainerService(service.LinuxService):
    SERVICE_NAME = 'swift-container'
    GREP = '[s]wift-container'
    LINUX_SERVICE = 'swift-container'


class SwiftContainerAuditorService(service.LinuxService):
    SERVICE_NAME = 'swift-container-auditor'
    GREP = '[s]wift-container-auditor'
    LINUX_SERVICE = 'swift-container-auditor'


class SwiftContainerReplicatorService(service.LinuxService):
    SERVICE_NAME = 'swift-container-replicator'
    GREP = '[s]wift-container-replicator'
    LINUX_SERVICE = 'swift-container-replicator'


class SwiftContainerSyncService(service.LinuxService):
    SERVICE_NAME = 'swift-container-sync'
    GREP = '[s]wift-container-sync'
    LINUX_SERVICE = 'swift-container-sync'


class SwiftContainerUpdaterService(service.LinuxService):
    SERVICE_NAME = 'swift-container-updater'
    GREP = '[s]wift-container-updater'
    LINUX_SERVICE = 'swift-container-updater'


class SwiftObjectService(service.LinuxService):
    SERVICE_NAME = 'swift-object'
    GREP = '[s]wift-object'
    LINUX_SERVICE = 'swift-object'


class SwiftObjectAuditorService(service.LinuxService):
    SERVICE_NAME = 'swift-object-auditor'
    GREP = '[s]wift-object-auditor'
    LINUX_SERVICE = 'swift-object-auditor'


class SwiftObjectReplicatorService(service.LinuxService):
    SERVICE_NAME = 'swift-object-replicator'
    GREP = '[s]wift-object-replicator'
    LINUX_SERVICE = 'swift-object-replicator'


class SwiftObjectUpdaterService(service.LinuxService):
    SERVICE_NAME = 'swift-object-updater'
    GREP = '[s]wift-object-updater'
    LINUX_SERVICE = 'swift-object-updater'


class SwiftProxyService(service.LinuxService):
    SERVICE_NAME = 'swift-proxy'
    GREP = '[s]wift-proxy'
    LINUX_SERVICE = 'swift-proxy'


class FuelManagement(cloud_management.CloudManagement,
                     node_discover.NodeDiscover):
    NAME = 'fuel'
    DESCRIPTION = 'Fuel 9.x cloud management driver'
    NODE_CLS = FuelNodeCollection
    SERVICE_NAME_TO_CLASS = {
        'keystone': KeystoneService,
        'horizon': HorizonService,
        'memcached': MemcachedService,
        'mysql': MySQLService,
        'rabbitmq': RabbitMQService,
        'glance-api': GlanceAPIService,
        'glance-glare': GlanceGlareService,
        'glance-registry': GlanceRegistryService,
        'nova-api': NovaAPIService,
        'nova-compute': NovaComputeService,
        'nova-scheduler': NovaSchedulerService,
        'nova-cert': NovaCertService,
        'nova-conductor': NovaConductorService,
        'nova-consoleauth': NovaConsoleAuthService,
        'nova-novncproxy': NovaNoVNCProxyService,
        'neutron-server': NeutronServerService,
        'neutron-dhcp-agent': NeutronDhcpAgentService,
        'neutron-metadata-agent': NeutronMetadataAgentService,
        'neutron-openvswitch-agent': NeutronOpenvswitchAgentService,
        'neutron-l3-agent': NeutronL3AgentService,
        'heat-api': HeatAPIService,
        'heat-engine': HeatEngineService,
        'cinder-api': CinderAPIService,
        'cinder-scheduler': CinderSchedulerService,
        'cinder-volume': CinderVolumeService,
        'cinder-backup': CinderBackupService,
        'ironic-api': IronicApiService,
        'ironic-conductor': IronicConductorService,
        'swift-account': SwiftAccountService,
        'swift-account-auditor': SwiftAccountAuditorService,
        'swift-account-reaper': SwiftAccountReaperService,
        'swift-account-replicator': SwiftAccountReplicatorService,
        'swift-container': SwiftContainerService,
        'swift-container-auditor': SwiftContainerAuditorService,
        'swift-container-replicator': SwiftContainerReplicatorService,
        'swift-container-sync': SwiftContainerSyncService,
        'swift-container-updater': SwiftContainerUpdaterService,
        'swift-object': SwiftObjectService,
        'swift-object-auditor': SwiftObjectAuditorService,
        'swift-object-replicator': SwiftObjectReplicatorService,
        'swift-object-updater': SwiftObjectUpdaterService,
        'swift-proxy': SwiftProxyService,
    }
    SUPPORTED_SERVICES = list(SERVICE_NAME_TO_CLASS.keys())
    SUPPORTED_NETWORKS = ['management', 'private', 'public', 'storage']
    CONFIG_SCHEMA = {
        'type': 'object',
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'properties': {
            'address': {'type': 'string'},
            'username': {'type': 'string'},
            'private_key_file': {'type': 'string'},

        },
        'required': ['address', 'username'],
        'additionalProperties': False,
    }

    def __init__(self, cloud_management_params):
        super(FuelManagement, self).__init__()
        self.node_discover = self  # supports discovering

        self.master_node_address = cloud_management_params['address']
        self.username = cloud_management_params['username']
        self.private_key_file = cloud_management_params.get('private_key_file')

        self.master_node_executor = executor.AnsibleRunner(
            remote_user=self.username, private_key_file=self.private_key_file)

        self.cloud_executor = executor.AnsibleRunner(
            remote_user=self.username, private_key_file=self.private_key_file,
            jump_host=self.master_node_address)

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
            task = {'command': 'fuel node --json'}
            result = self._execute_on_master_node(task)
            for r in json.loads(result[0].payload['stdout']):
                host = node_collection.Host(ip=r['ip'], mac=r['mac'],
                                            fqdn=r['fqdn'])
                self.cached_cloud_hosts.append(host)

        return self.cached_cloud_hosts

    def _execute_on_master_node(self, task):
        """Execute task on Fuel master node.

        :param task: Ansible task
        :return: Ansible execution result (list of records)
        """
        return self.master_node_executor.execute(
            [self.master_node_address], task)

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
