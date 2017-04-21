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
from os_faults.api import node_collection
from os_faults.api import node_discover
from os_faults.common import service
from os_faults import error

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
    """Salt service

    Service that can be controled by `salt service.*` commands.

    **Example configuration:**

    .. code-block:: yaml

        services:
          app:
            driver: salt_service
            args:
              salt_service: app
              grep: my_app
              port: ['tcp', 4242]

    parameters:

    - **salt_service** - name of a service
    - **grep** - regexp for grep to find process PID
    - **port** - tuple with two values - potocol, port number (optional)

    """

    NAME = 'salt_service'
    DESCRIPTION = 'Service in salt'
    CONFIG_SCHEMA = {
        'type': 'object',
        'properties': {
            'salt_service': {'type': 'string'},
            'grep': {'type': 'string'},
            'port': service.PORT_SCHEMA,
        },
        'required': ['grep', 'salt_service'],
        'additionalProperties': False,
    }

    def __init__(self, *args, **kwargs):
        super(SaltService, self).__init__(*args, **kwargs)
        self.salt_service = self.config['salt_service']

        self.restart_cmd = SALT_RESTART.format(service=self.salt_service)
        self.terminate_cmd = SALT_TERMINATE.format(service=self.salt_service)
        self.start_cmd = SALT_START.format(service=self.salt_service)


class TCPCloudManagement(cloud_management.CloudManagement,
                         node_discover.NodeDiscover):
    """TCPCloud driver.

    Supports discovering of slave nodes.

    **Example configuration:**

    .. code-block:: yaml

        cloud_management:
          driver: tcpcloud
          args:
            address: 192.168.1.10
            username: root
            password: root_pass
            private_key_file: ~/.ssh/id_rsa_tcpcloud
            slave_username: ubuntu
            slave_password: ubuntu_pass
            master_sudo: False
            slave_sudo: True
            slave_name_regexp: ^(?!cfg|mon)
            slave_direct_ssh: True
            get_ips_cmd: pillar.get _param:single_address

    parameters:

    - **address** - ip address of salt config node
    - **username** - username for salt config node
    - **password** - password for salt config node (optional)
    - **private_key_file** - path to key file (optional)
    - **slave_username** - username for salt minions (optional) *username*
      will be used if *slave_username* not specified
    - **slave_password** - password for salt minions (optional) *password*
      will be used if *slave_password* not specified
    - **master_sudo** - Use sudo on salt config node (optional)
    - **slave_sudo** - Use sudi on salt minion nodes (optional)
    - **slave_name_regexp** - regexp for minion FQDNs (optional)
    - **slave_direct_ssh** - if *False* then salt master is used as ssh proxy
      (optional)
    - **get_ips_cmd** - salt command to get IPs of minions (optional)
    - **serial** - how many hosts Ansible should manage at a single time.
      (optional) default: 10
    """

    NAME = 'tcpcloud'
    DESCRIPTION = 'TCPCloud management driver'
    NODE_CLS = TCPCloudNodeCollection
    SERVICES = {
        'keystone': {
            'driver': 'salt_service',
            'args': {
                'grep': 'keystone-all',
                'salt_service': 'keystone',
            }
        },
        'horizon': {
            'driver': 'salt_service',
            'args': {
                'grep': 'apache2',
                'salt_service': 'apache2',
            }
        },
        'memcached': {
            'driver': 'salt_service',
            'args': {
                'grep': 'memcached',
                'salt_service': 'memcached',
            }
        },
        'mysql': {
            'driver': 'salt_service',
            'args': {
                'grep': 'mysqld',
                'salt_service': 'mysql',
                'port': ['tcp', 3307],
            }
        },
        'rabbitmq': {
            'driver': 'salt_service',
            'args': {
                'grep': 'beam\.smp .*rabbitmq_server',
                'salt_service': 'rabbitmq-server',
            }
        },
        'glance-api': {
            'driver': 'salt_service',
            'args': {
                'grep': 'glance-api',
                'salt_service': 'glance-api',
            }
        },
        'glance-registry': {
            'driver': 'salt_service',
            'args': {
                'grep': 'glance-registry',
                'salt_service': 'glance-registry',
            }
        },
        'nova-api': {
            'driver': 'salt_service',
            'args': {
                'grep': 'nova-api',
                'salt_service': 'nova-api',
            }
        },
        'nova-compute': {
            'driver': 'salt_service',
            'args': {
                'grep': 'nova-compute',
                'salt_service': 'nova-compute',
            }
        },
        'nova-scheduler': {
            'driver': 'salt_service',
            'args': {
                'grep': 'nova-scheduler',
                'salt_service': 'nova-scheduler',
            }
        },
        'nova-cert': {
            'driver': 'salt_service',
            'args': {
                'grep': 'nova-cert',
                'salt_service': 'nova-cert',
            }
        },
        'nova-conductor': {
            'driver': 'salt_service',
            'args': {
                'grep': 'nova-conductor',
                'salt_service': 'nova-conductor',
            }
        },
        'nova-consoleauth': {
            'driver': 'salt_service',
            'args': {
                'grep': 'nova-consoleauth',
                'salt_service': 'nova-consoleauth',
            }
        },
        'nova-novncproxy': {
            'driver': 'salt_service',
            'args': {
                'grep': 'nova-novncproxy',
                'salt_service': 'nova-novncproxy',
            }
        },
        'neutron-server': {
            'driver': 'salt_service',
            'args': {
                'grep': 'neutron-server',
                'salt_service': 'neutron-server',
            }
        },
        'neutron-dhcp-agent': {
            'driver': 'salt_service',
            'args': {
                'grep': 'neutron-dhcp-agent',
                'salt_service': 'neutron-dhcp-agent',
            }
        },
        'neutron-metadata-agent': {
            'driver': 'salt_service',
            'args': {
                'grep': 'neutron-metadata-agent',
                'salt_service': 'neutron-metadata-agent',
            }
        },
        'neutron-openvswitch-agent': {
            'driver': 'salt_service',
            'args': {
                'grep': 'neutron-openvswitch-agent',
                'salt_service': 'neutron-openvswitch-agent',
            }
        },
        'neutron-l3-agent': {
            'driver': 'salt_service',
            'args': {
                'grep': 'neutron-l3-agent',
                'salt_service': 'neutron-l3-agent',
            }
        },
        'heat-api': {
            'driver': 'salt_service',
            'args': {
                # space at the end filters heat-api-* services
                'grep': 'heat-api ',
                'salt_service': 'heat-api',
            }
        },
        'heat-engine': {
            'driver': 'salt_service',
            'args': {
                'grep': 'heat-engine',
                'salt_service': 'heat-engine',
            }
        },
        'cinder-api': {
            'driver': 'salt_service',
            'args': {
                'grep': 'cinder-api',
                'salt_service': 'cinder-api',
            }
        },
        'cinder-scheduler': {
            'driver': 'salt_service',
            'args': {
                'grep': 'cinder-scheduler',
                'salt_service': 'cinder-scheduler',
            }
        },
        'cinder-volume': {
            'driver': 'salt_service',
            'args': {
                'grep': 'cinder-volume',
                'salt_service': 'cinder-volume',
            }
        },
        'cinder-backup': {
            'driver': 'salt_service',
            'args': {
                'grep': 'cinder-backup',
                'salt_service': 'cinder-backup',
            }
        },
        'elasticsearch': {
            'driver': 'salt_service',
            'args': {
                'grep': 'java .*elasticsearch',
                'salt_service': 'elasticsearch',
            }
        },
        'grafana-server': {
            'driver': 'salt_service',
            'args': {
                'grep': 'grafana-server',
                'salt_service': 'grafana-server',
            }
        },
        'influxdb': {
            'driver': 'salt_service',
            'args': {
                'grep': 'influxd',
                'salt_service': 'influxdb',
            }
        },
        'kibana': {
            'driver': 'salt_service',
            'args': {
                'grep': 'kibana',
                'salt_service': 'kibana',
            }
        },
        'nagios3': {
            'driver': 'salt_service',
            'args': {
                'grep': 'nagios3',
                'salt_service': 'nagios3',
            }
        },
    }
    SUPPORTED_NETWORKS = []
    CONFIG_SCHEMA = {
        'type': 'object',
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'properties': {
            'address': {'type': 'string'},
            'username': {'type': 'string'},
            'password': {'type': 'string'},
            'private_key_file': {'type': 'string'},
            'slave_username': {'type': 'string'},
            'slave_password': {'type': 'string'},
            'master_sudo': {'type': 'boolean'},
            'slave_sudo': {'type': 'boolean'},
            'slave_name_regexp': {'type': 'string'},
            'slave_direct_ssh': {'type': 'boolean'},
            'get_ips_cmd': {'type': 'string'},
            'serial': {'type': 'integer', 'minimum': 1},
        },
        'required': ['address', 'username'],
        'additionalProperties': False,
    }

    def __init__(self, cloud_management_params):
        super(TCPCloudManagement, self).__init__()
        self.node_discover = self  # supports discovering

        self.master_node_address = cloud_management_params['address']
        self.username = cloud_management_params['username']
        self.slave_username = cloud_management_params.get(
            'slave_username', self.username)
        self.private_key_file = cloud_management_params.get('private_key_file')
        self.slave_direct_ssh = cloud_management_params.get(
            'slave_direct_ssh', False)
        use_jump = not self.slave_direct_ssh
        self.get_ips_cmd = cloud_management_params.get(
            'get_ips_cmd', 'pillar.get _param:single_address')
        self.serial = cloud_management_params.get('serial')

        password = cloud_management_params.get('password')
        self.master_node_executor = executor.AnsibleRunner(
            remote_user=self.username,
            password=password,
            private_key_file=self.private_key_file,
            become=cloud_management_params.get('master_sudo'))

        self.cloud_executor = executor.AnsibleRunner(
            remote_user=self.slave_username,
            password=cloud_management_params.get('slave_password', password),
            private_key_file=self.private_key_file,
            jump_host=self.master_node_address if use_jump else None,
            jump_user=self.username if use_jump else None,
            become=cloud_management_params.get('slave_sudo'),
            serial=self.serial)

        # get all nodes except salt master (that has cfg* hostname) by default
        self.slave_name_regexp = cloud_management_params.get(
            'slave_name_regexp', '^(?!cfg|mon)')

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

    def _run_salt(self, command):
        cmd = "salt -E '{}' {} --out=yaml".format(
            self.slave_name_regexp, command)
        result = self._execute_on_master_node({'command': cmd})
        return yaml.load(result[0].payload['stdout'])

    def discover_hosts(self):
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
            self.cached_cloud_hosts = sorted(self.cached_cloud_hosts)

        return self.cached_cloud_hosts

    def _execute_on_master_node(self, task):
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
