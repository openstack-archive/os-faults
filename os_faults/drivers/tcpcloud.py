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

import yaml

from os_faults.ansible import executor
from os_faults.api import cloud_management
from os_faults.api import error
from os_faults.api import node_collection
from os_faults.common import service
from os_faults import utils

LOG = logging.getLogger(__name__)


class TCPCloudNodeCollection(node_collection.NodeCollection):

    def connect(self, network_name):
        raise NotImplementedError

    def disconnect(self, network_name):
        raise NotImplementedError


SALT_CALL = 'salt-call --local --retcode-passthrough '
SALT_RESTART = SALT_CALL + 'service.restart {service}'
SALT_TERMINATE = SALT_CALL + 'service.stop {service}'
SALT_START = SALT_CALL + 'service.start {service}'


class SaltService(service.ServiceAsProcess):

    @utils.require_variables('SALT_SERVICE')
    def __init__(self, *args, **kwargs):
        super(SaltService, self).__init__(*args, **kwargs)

        self.RESTART_CMD = SALT_RESTART.format(service=self.SALT_SERVICE)
        self.TERMINATE_CMD = SALT_TERMINATE.format(service=self.SALT_SERVICE)
        self.START_CMD = SALT_START.format(service=self.SALT_SERVICE)


class KeystoneService(SaltService):
    SERVICE_NAME = 'keystone'
    GREP = '[k]eystone-all'
    SALT_SERVICE = 'keystone'


class HorizonService(SaltService):
    SERVICE_NAME = 'horizon'
    GREP = '[a]pache2'
    SALT_SERVICE = 'apache2'


class MemcachedService(SaltService):
    SERVICE_NAME = 'memcached'
    GREP = '[m]emcached'
    SALT_SERVICE = 'memcached'


class MySQLService(SaltService):
    SERVICE_NAME = 'mysql'
    GREP = '[m]ysqld'
    SALT_SERVICE = 'mysql'
    PORT = ('tcp', 3307)


class RabbitMQService(SaltService):
    SERVICE_NAME = 'rabbitmq'
    GREP = 'beam\.smp .*rabbitmq_server'
    SALT_SERVICE = 'rabbitmq-server'


class GlanceAPIService(SaltService):
    SERVICE_NAME = 'glance-api'
    GREP = '[g]lance-api'
    SALT_SERVICE = 'glance-api'


class GlanceRegistryService(SaltService):
    SERVICE_NAME = 'glance-registry'
    GREP = '[g]lance-registry'
    SALT_SERVICE = 'glance-registry'


class NovaAPIService(SaltService):
    SERVICE_NAME = 'nova-api'
    GREP = '[n]ova-api'
    SALT_SERVICE = 'nova-api'


class NovaComputeService(SaltService):
    SERVICE_NAME = 'nova-compute'
    GREP = '[n]ova-compute'
    SALT_SERVICE = 'nova-compute'


class NovaSchedulerService(SaltService):
    SERVICE_NAME = 'nova-scheduler'
    GREP = '[n]ova-scheduler'
    SALT_SERVICE = 'nova-scheduler'


class NovaCertService(SaltService):
    SERVICE_NAME = 'nova-cert'
    GREP = '[n]ova-cert'
    SALT_SERVICE = 'nova-cert'


class NovaConductorService(SaltService):
    SERVICE_NAME = 'nova-conductor'
    GREP = '[n]ova-conductor'
    SALT_SERVICE = 'nova-conductor'


class NovaConsoleAuthService(SaltService):
    SERVICE_NAME = 'nova-consoleauth'
    GREP = '[n]ova-consoleauth'
    SALT_SERVICE = 'nova-consoleauth'


class NovaNoVNCProxyService(SaltService):
    SERVICE_NAME = 'nova-novncproxy'
    GREP = '[n]ova-novncproxy'
    SALT_SERVICE = 'nova-novncproxy'


class NeutronServerService(SaltService):
    SERVICE_NAME = 'neutron-server'
    GREP = '[n]eutron-server'
    SALT_SERVICE = 'neutron-server'


class NeutronDhcpAgentService(SaltService):
    SERVICE_NAME = 'neutron-dhcp-agent'
    GREP = '[n]eutron-dhcp-agent'
    SALT_SERVICE = 'neutron-dhcp-agent'


class NeutronMetadataAgentService(SaltService):
    SERVICE_NAME = 'neutron-metadata-agent'
    GREP = '[n]eutron-metadata-agent'
    SALT_SERVICE = 'neutron-metadata-agent'


class NeutronOpenvswitchAgentService(SaltService):
    SERVICE_NAME = 'neutron-openvswitch-agent'
    GREP = '[n]eutron-openvswitch-agent'
    SALT_SERVICE = 'neutron-openvswitch-agent'


class NeutronL3AgentService(SaltService):
    SERVICE_NAME = 'neutron-l3-agent'
    GREP = '[n]eutron-l3-agent'
    SALT_SERVICE = 'neutron-l3-agent'


class HeatAPIService(SaltService):
    SERVICE_NAME = 'heat-api'
    GREP = '[h]eat-api '
    SALT_SERVICE = 'heat-api'


class HeatEngineService(SaltService):
    SERVICE_NAME = 'heat-engine'
    GREP = '[h]eat-engine'
    SALT_SERVICE = 'heat-engine'


class CinderAPIService(SaltService):
    SERVICE_NAME = 'cinder-api'
    GREP = '[c]inder-api'
    SALT_SERVICE = 'cinder-api'


class CinderSchedulerService(SaltService):
    SERVICE_NAME = 'cinder-scheduler'
    GREP = '[c]inder-scheduler'
    SALT_SERVICE = 'cinder-scheduler'


class CinderVolumeService(SaltService):
    SERVICE_NAME = 'cinder-volume'
    GREP = '[c]inder-volume'
    SALT_SERVICE = 'cinder-volume'


class CinderBackupService(SaltService):
    SERVICE_NAME = 'cinder-backup'
    GREP = '[c]inder-backup'
    SALT_SERVICE = 'cinder-backup'


class TCPCloudManagement(cloud_management.CloudManagement):
    NAME = 'tcpcloud'
    DESCRIPTION = 'TCPCloud management driver'
    NODE_CLS = TCPCloudNodeCollection
    SERVICE_NAME_TO_CLASS = {
        'keystone': KeystoneService,
        'horizon': HorizonService,
        'memcached': MemcachedService,
        'mysql': MySQLService,
        'rabbitmq': RabbitMQService,
        'glance-api': GlanceAPIService,
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
    }
    SUPPORTED_SERVICES = list(SERVICE_NAME_TO_CLASS.keys())
    SUPPORTED_NETWORKS = []
    CONFIG_SCHEMA = {
        'type': 'object',
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'properties': {
            'address': {'type': 'string'},
            'username': {'type': 'string'},
            'private_key_file': {'type': 'string'},
            'slave_username': {'type': 'string'},
            'master_sudo': {'type': 'boolean'},
            'slave_sudo': {'type': 'boolean'},
            'slave_name_regexp': {'type': 'string'},
            'slave_direct_ssh': {'type': 'boolean'},
            'get_ips_cmd': {'type': 'string'},
        },
        'required': ['address', 'username'],
        'additionalProperties': False,
    }

    def __init__(self, cloud_management_params):
        super(TCPCloudManagement, self).__init__()

        self.master_node_address = cloud_management_params['address']
        self.username = cloud_management_params['username']
        self.slave_username = cloud_management_params.get(
            'slave_username', self.username)
        self.private_key_file = cloud_management_params.get('private_key_file')
        self.slave_direct_ssh = cloud_management_params.get(
            'slave_direct_ssh', False)
        use_jump = self.slave_direct_ssh
        self.get_ips_cmd = cloud_management_params.get(
            'get_ips_cmd', 'pillar.get _param:single_address')

        self.master_node_executor = executor.AnsibleRunner(
            remote_user=self.username,
            private_key_file=self.private_key_file,
            become=cloud_management_params.get('master_sudo'))

        self.cloud_executor = executor.AnsibleRunner(
            remote_user=self.slave_username,
            private_key_file=self.private_key_file,
            jump_host=self.master_node_address if use_jump else None,
            jump_user=self.username if use_jump else None,
            become=cloud_management_params.get('slave_sudo'))

        # get all nodes except salt master (that has cfg* hostname) by default
        self.slave_name_regexp = cloud_management_params.get(
            'slave_name_regexp', '^(?!cfg|mon)')

        self.cached_cloud_hosts = list()
        self.fqdn_to_hosts = dict()

    def verify(self):
        """Verify connection to the cloud."""
        hosts = self._get_cloud_hosts()
        LOG.debug('Cloud nodes: %s', hosts)

        task = {'command': 'hostname'}
        host_addrs = [host.ip for host in hosts]
        task_result = self.execute_on_cloud(host_addrs, task)
        LOG.debug('Hostnames of cloud nodes: %s',
                  [r.payload['stdout'] for r in task_result])

        LOG.info('Connected to cloud successfully!')

    def _run_salt(self, command):
        cmd = "salt -E '{}' {} --out=yaml".format(
            self.slave_name_regexp, command)
        result = self.execute_on_master_node({'command': cmd})
        return yaml.load(result[0].payload['stdout'])

    def _get_cloud_hosts(self):
        if not self.cached_cloud_hosts:
            interfaces = self._run_salt("network.interfaces")
            ips = self._run_salt(self.get_ips_cmd)

            for fqdn, ip in ips.items():
                node_ifaces = interfaces[fqdn]

                mac = None
                for iface_name, net_data in node_ifaces.items():
                    iface_ips = [data['address']
                                 for data in net_data.get('inet', [])]
                    if ip in iface_ips:
                        mac = net_data['hwaddr']
                        break
                else:
                    raise error.CloudManagementError(
                        "Can't find ip {} on node {} with node_ifaces:\n{}"
                        "".format(ip, fqdn, yaml.dump(node_ifaces)))

                host = node_collection.Host(ip=ip, mac=mac, fqdn=fqdn)
                self.cached_cloud_hosts.append(host)
                self.fqdn_to_hosts[host.fqdn] = host
            self.cached_cloud_hosts = sorted(self.cached_cloud_hosts)

        return self.cached_cloud_hosts

    def execute_on_master_node(self, task):
        """Execute task on salt master node.

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

    def get_nodes(self, fqdns=None):
        """Get nodes in the cloud

        This function returns NodesCollection representing all nodes in the
        cloud or only those that were specified by FQDNs.
        :param fqdns: list of FQDNs or None to retrieve all nodes
        :return: NodesCollection
        """
        hosts = self._get_cloud_hosts()

        if fqdns:
            LOG.debug('Trying to find nodes with FQDNs: %s', fqdns)
            hosts = []
            for fqdn in fqdns:
                if fqdn in self.fqdn_to_hosts:
                    hosts.append(self.fqdn_to_hosts[fqdn])
                else:
                    raise error.NodeCollectionError(
                        'Node with FQDN \'%s\' not found!' % fqdn)
            LOG.debug('The following nodes were found: %s', hosts)

        return self.NODE_CLS(cloud_management=self,
                             power_management=self.power_management,
                             hosts=hosts)
