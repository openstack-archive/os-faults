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
        LOG.info("Connect network '%s' on nodes: %s", network_name, self)
        task = {'osa_network_mgmt': {
            'network_name': network_name,
            'operation': 'up',
        }}
        self.cloud_management.execute_on_cloud(self.get_ips(), task)

    def disconnect(self, network_name):
        LOG.info("Disconnect network '%s' on nodes: %s",
                 network_name, self)
        task = {'osa_network_mgmt': {
            'network_name': network_name,
            'operation': 'down',
        }}
        self.cloud_management.execute_on_cloud(self.get_ips(), task)


SALT_CALL = 'salt-call --local --retcode-passthrough '
SALT_RESTART = SALT_CALL + 'service.restart {service}'
SALT_TERMINATE = SALT_CALL + 'service.stop {service}'
SALT_START = SALT_CALL + 'service.start {service}'

BASH = 'bash -c "{}"'
FIND_Q = 'ps ax | grep -q {}'
FIND_E = 'ps ax | grep -e {}'
EXCLUDE = 'ps ax | grep -qv {}'


class SaltService(service.ServiceAsProcess):

    @utils.require_variables('SALT_SERVICE', 'SALT_FIND')
    def __init__(self, *args, **kwargs):
        super(SaltService, self).__init__(*args, **kwargs)

        self.RESTART_CMD = SALT_RESTART.format(service=self.SALT_SERVICE)
        self.TERMINATE_CMD = SALT_TERMINATE.format(service=self.SALT_SERVICE)
        self.START_CMD = SALT_START.format(service=self.SALT_SERVICE)
        self.FIND_CMD = self.SALT_FIND


class KeystoneService(SaltService):
    SERVICE_NAME = 'apache2'
    GREP = ['[k]eystone','[a]pache2']
    SALT_SERVICE = 'apache2'
    SALT_FIND = BASH.format(' && '.join([FIND_Q.format(g) for g in GREP[:-1]]) +
                            ' && ' + FIND_E.format(GREP[-1]))


class HorizonService(SaltService):
    SERVICE_NAME = 'horizon'
    GREP = '[a]pache2'
    IGNORE = '[k]eystone'
    SALT_SERVICE = 'apache2'
    SALT_FIND = BASH.format(FIND_Q.format(GREP) + ' && ' +
                            FIND_E.format(IGNORE) + ' | ' +
                            EXCLUDE.format(IGNORE))


class MemcachedService(SaltService):
    SERVICE_NAME = 'memcached'
    GREP = '[m]emcached'
    SALT_SERVICE = 'memcached'
    SALT_FIND = BASH.format(FIND_E.format(GREP))


class MySQLService(SaltService):
    SERVICE_NAME = 'mysql'
    GREP = '[m]ysqld'
    SALT_SERVICE = 'mysql'
    PORT = ('tcp', 3307)


class RabbitMQService(SaltService):
    SERVICE_NAME = 'rabbitmq'
    GREP = '[r]abbitmq-server'
    SALT_SERVICE = 'rabbitmq-server'
    SALT_FIND = BASH.format(FIND_E.format(GREP))


class NovaAPIService(SaltService):
    SERVICE_NAME = 'nova-api'
    GREP = '[n]ova-api'
    SALT_SERVICE = 'nova-api'


class GlanceAPIService(SaltService):
    SERVICE_NAME = 'glance-api'
    GREP = '[g]lance-api'
    SALT_SERVICE = 'glance-api'


class NovaComputeService(SaltService):
    SERVICE_NAME = 'nova-compute'
    GREP = '[n]ova-compute'
    SALT_SERVICE = 'nova-compute'
    SALT_FIND = BASH.format('initctl list | grep -e {}'.format(GREP))

class NovaSchedulerService(SaltService):
    SERVICE_NAME = 'nova-scheduler'
    GREP = '[n]ova-scheduler'
    SALT_SERVICE = 'nova-scheduler'
    SALT_FIND = BASH.format(FIND_E.format(GREP))


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
        'nova-api': NovaAPIService,
        'glance-api': GlanceAPIService,
        'nova-compute': NovaComputeService,
        'nova-scheduler': NovaSchedulerService,
        'heat-api': HeatAPIService,
        'heat-engine': HeatEngineService,
        'cinder-api': CinderAPIService,
        'cinder-scheduler': CinderSchedulerService,
        'cinder-volume': CinderVolumeService,
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

        },
        'required': ['address', 'username'],
        'additionalProperties': False,
    }

    def __init__(self, cloud_management_params):
        super(TCPCloudManagement, self).__init__()

        self.master_node_address = cloud_management_params['address']
        self.username = cloud_management_params['username']
        self.private_key_file = cloud_management_params.get('private_key_file')

        self.master_node_executor = executor.AnsibleRunner(
            remote_user=self.username, private_key_file=self.private_key_file)

        self.cloud_executor = executor.AnsibleRunner(
            remote_user=self.username, private_key_file=self.private_key_file,
            jump_host=self.master_node_address)

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

    def _get_cloud_hosts(self):
        if not self.cached_cloud_hosts:
            cmd = "salt -E '(infra*|compute*)' network.interfaces --out=yaml"
            result = self.execute_on_master_node({'command': cmd})
            stdout = result[0].payload['stdout']
            for fqdn, net_data in yaml.load(stdout).items():
                try:
                    host = node_collection.Host(
                        ip=net_data['eth1']['inet'][0]['address'],
                        mac=net_data['eth1']['hwaddr'],
                        fqdn=fqdn)
                except KeyError:
                    regex_ipaddr = '([0-9]{1,3}\.){3}[0-9]{1,3}'
                    regex_mac = '([0-9a-z]{2}\:){5}[0-9a-z]{2}'
                    ip_cmd = BASH.format(
                        'grep -w {} /etc/hosts | grep -oE \'{}\''.format(
                            fqdn.split('.')[0], regex_ipaddr
                        )
                    )
                    ip_res = self.execute_on_master_node({'command': ip_cmd})
                    ip_out = ip_res[0].payload['stdout']
                    mac_cmd = BASH.format(
                        'arp -an {} | grep -oE \'{}\''.format(
                            ip_out, regex_mac
                        )
                    )
                    mac_res = self.execute_on_master_node({'command': mac_cmd})
                    mac_out = mac_res[0].payload['stdout']
                    host = node_collection.Host(
                        ip=ip_out,
                        mac=mac_out,
                        fqdn=fqdn)
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
