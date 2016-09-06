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

import abc
import json
import logging
import random
import six

from os_faults.ansible import executor
from os_faults.api import cloud_management
from os_faults.api import error
from os_faults.api import node_collection
from os_faults.api import service


class FuelNodeCollection(node_collection.NodeCollection):
    def __init__(self, cloud_management=None, power_management=None,
                 hosts=None):
        self.cloud_management = cloud_management
        self.power_management = power_management
        self.hosts = hosts

    def __repr__(self):
        return ('FuelNodeCollection(%s)' %
                [dict(ip=h['ip'], mac=h['mac']) for h in self.hosts])

    def __len__(self):
        return len(self.hosts)

    def get_ips(self):
        return [n['ip'] for n in self.hosts]

    def get_macs(self):
        return [n['mac'] for n in self.hosts]

    def iterate_hosts(self):
        for host in self.hosts:
            try:
                yield host
            except GeneratorExit:
                break

    def filter(self, role):
        hosts = [h for h in self.hosts if role in h['roles']]
        return FuelNodeCollection(cloud_management=self.cloud_management,
                                  power_management=self.power_management,
                                  hosts=hosts)

    def pick(self):
        return FuelNodeCollection(cloud_management=self.cloud_management,
                                  power_management=self.power_management,
                                  hosts=[random.choice(self.hosts)])

    def reboot(self):
        raise NotImplementedError
        task = {
            'command': 'ps aux'
        }
        self.cloud_management.execute_on_cloud(self.get_ips(), task)

    def oom(self):
        raise NotImplementedError
        logging.info('Enforce nodes to run out of memory: %s', self)

    def poweroff(self):
        self.power_management.poweroff(self.get_macs())

    def poweron(self):
        self.power_management.poweron(self.get_macs())

    def reset(self):
        logging.info('Reset nodes: %s', self)
        self.power_management.reset(self.get_macs())

    def enable_network(self, network_name):
        logging.info('Enable network: %s on nodes: %s', network_name, self)
        task = {'fuel_network_mgmt': {
            'network_name': network_name,
            'operation': 'up',
        }}
        self.cloud_management.execute_on_cloud(self.get_ips(), task)

    def disable_network(self, network_name):
        logging.info('Disable network: %s on nodes: %s', network_name, self)
        task = {'fuel_network_mgmt': {
            'network_name': network_name,
            'operation': 'down',
        }}
        self.cloud_management.execute_on_cloud(self.get_ips(), task)


@six.add_metaclass(abc.ABCMeta)
class FuelService(service.Service):

    def __init__(self, cloud_management=None, power_management=None):
        self.cloud_management = cloud_management
        self.power_management = power_management

    def __repr__(self):
        return str(type(self))

    def _run_task(self, task, nodes=None):
        nodes = nodes or self.get_nodes()
        ips = nodes.get_ips()
        if not ips:
            raise error.FuelServiceError('Node collection is empty')

        results = self.cloud_management.execute_on_cloud(ips, task)
        err = False
        for result in results:
            if result.status != executor.STATUS_OK:
                logging.error('Task %s failed on node %s', task, result.host)
                err = True
        if err:
            raise error.FuelServiceError('Task failed on some nodes')
        return results

    def get_nodes(self):
        nodes = self.cloud_management.get_nodes()
        ips = nodes.get_ips()
        results = self.cloud_management.execute_on_cloud(
            ips, {'command': self.GET_NODES_CMD}, False)
        success_ips = [r.host for r in results
                       if r.status == executor.STATUS_OK]
        hosts = [h for h in nodes.hosts if h['ip'] in success_ips]
        return FuelNodeCollection(cloud_management=self.cloud_management,
                                  power_management=self.power_management,
                                  hosts=hosts)

    def restart(self, nodes=None):
        if not getattr(self, 'RESTART_CMD'):
            raise NotImplementedError('RESTART_CMD is undefined')
        nodes = nodes or self.get_nodes()
        task_result = self._run_task({'command': self.RESTART_CMD}, nodes)
        logging.info('Restart %s, result: %s', str(self.__class__),
                     task_result)

    def kill(self, nodes=None):
        nodes = nodes or self.get_nodes()
        task_result = self._run_task({'command': self.KILL_CMD}, nodes)
        logging.info('SIGKILL %s, result: %s', str(self.__class__),
                     task_result)

    def stop(self, nodes=None):
        nodes = nodes or self.get_nodes()
        task_result = self._run_task({'command': self.STOP_CMD}, nodes)
        logging.info('SIGSTOP %s, result: %s', str(self.__class__),
                     task_result)

    def stop_cont(self, nodes=None, sec=None):
        nodes = nodes or self.get_nodes()
        sec = str(sec) or '10'
        cmd = self.STOP_CONT_CMD.replace('$sec', sec)
        task_result = self._run_task({'command': cmd}, nodes)
        logging.info('SIGSTOP+SIGCONT %s, result: %s', str(self.__class__),
                     task_result)


class KeystoneService(FuelService):
    GET_NODES_CMD = 'bash -c "ps ax | grep \'[k]eystone-main\'"'
    KILL_CMD = ('bash -c "ps ax | grep [k]eystone'
                ' | awk {\'print $1\'} | xargs kill -9"')
    RESTART_CMD = 'service apache2 restart'
    STOP_CMD = ('bash -c "ps ax | grep [k]eystone'
                ' | awk {\'print $1\'} | xargs kill -19"')
    STOP_CONT_CMD = ('bash -c "tf=$(mktemp /tmp/script.XXXXXX);'
                     'echo -n \'#!\' > $tf; '
                     'echo -en \'/bin/bash\\npids=`ps ax | '
                     'grep [k]eystone | awk {\\047print $1\\047}`; '
                     'echo $pids | xargs kill -19; sleep $sec; '
                     'echo $pids | xargs kill -18; rm \' >> $tf; '
                     'echo -n $tf >> $tf; '
                     'chmod 770 $tf; nohup $tf &"')


class MySQLService(FuelService):
    GET_NODES_CMD = 'bash -c "netstat -tap | grep \'.*LISTEN.*mysqld\'"'
    KILL_CMD = ('bash -c "ps ax | grep [m]ysqld'
                ' | awk {\'print $1\'} | xargs kill -9"')
    STOP_CMD = ('bash -c "ps ax | grep [m]ysqld'
                ' | awk {\'print $1\'} | xargs kill -19"')
    STOP_CONT_CMD = ('bash -c "tf=$(mktemp /tmp/script.XXXXXX);'
                     'echo -n \'#!\' > $tf; '
                     'echo -en \'/bin/bash\\npids=`ps ax | '
                     'grep [m]ysqld | awk {\\047print $1\\047}`; '
                     'echo $pids | xargs kill -19; sleep $sec; '
                     'echo $pids | xargs kill -18; rm \' >> $tf; '
                     'echo -n $tf >> $tf; '
                     'chmod 770 $tf; nohup $tf &"')


class RabbitMQService(FuelService):
    GET_NODES_CMD = 'bash -c "rabbitmqctl status | grep \'pid,\'"'
    KILL_CMD = ('bash -c "ps ax | grep [r]abbitmq-server'
                ' | awk {\'print $1\'} | xargs kill -9"')
    STOP_CMD = ('bash -c "ps ax | grep [r]abbitmq-server'
                ' | awk {\'print $1\'} | xargs kill -19"')
    STOP_CONT_CMD = ('bash -c "tf=$(mktemp /tmp/script.XXXXXX);'
                     'echo -n \'#!\' > $tf; '
                     'echo -en \'/bin/bash\\npids=`ps ax | '
                     'grep [r]abbitmq-server | awk {\\047print $1\\047}`; '
                     'echo $pids | xargs kill -19; sleep $sec; '
                     'echo $pids | xargs kill -18; rm \' >> $tf; '
                     'echo -n $tf >> $tf; '
                     'chmod 770 $tf; nohup $tf &"')


class NovaAPIService(FuelService):
    GET_NODES_CMD = 'bash -c "ps ax | grep \'[n]ova-api\'"'
    KILL_CMD = ('bash -c "ps ax | grep [n]ova-api'
                ' | awk {\'print $1\'} | xargs kill -9"')
    STOP_CMD = ('bash -c "ps ax | grep [n]ova-api'
                ' | awk {\'print $1\'} | xargs kill -19"')
    STOP_CONT_CMD = ('bash -c "tf=$(mktemp /tmp/script.XXXXXX);'
                     'echo -n \'#!\' > $tf; '
                     'echo -en \'/bin/bash\\npids=`ps ax | '
                     'grep [n]ova-api | awk {\\047print $1\\047}`; '
                     'echo $pids | xargs kill -19; sleep $sec; '
                     'echo $pids | xargs kill -18; rm \' >> $tf; '
                     'echo -n $tf >> $tf; '
                     'chmod 770 $tf; nohup $tf &"')


class GlanceAPIService(FuelService):
    GET_NODES_CMD = 'bash -c "ps ax | grep \'[g]lance-api\'"'
    KILL_CMD = ('bash -c "ps ax | grep [g]lance-api'
                ' | awk {\'print $1\'} | xargs kill -9"')
    STOP_CMD = ('bash -c "ps ax | grep [g]lance-api'
                ' | awk {\'print $1\'} | xargs kill -19"')
    STOP_CONT_CMD = ('bash -c "tf=$(mktemp /tmp/script.XXXXXX);'
                     'echo -n \'#!\' > $tf; '
                     'echo -en \'/bin/bash\\npids=`ps ax | '
                     'grep [g]lance-api | awk {\\047print $1\\047}`; '
                     'echo $pids | xargs kill -19; sleep $sec; '
                     'echo $pids | xargs kill -18; rm \' >> $tf; '
                     'echo -n $tf >> $tf; '
                     'chmod 770 $tf; nohup $tf &"')


SERVICE_NAME_TO_CLASS = {
    'keystone': KeystoneService,
    'mysql': MySQLService,
    'rabbitmq': RabbitMQService,
    'nova-api': NovaAPIService,
    'glance-api': GlanceAPIService,
}


class FuelManagement(cloud_management.CloudManagement):
    def __init__(self, cloud_management_params):
        super(FuelManagement, self).__init__()

        self.master_node_address = cloud_management_params['address']
        self.username = cloud_management_params['username']

        self.master_node_executor = executor.AnsibleRunner(
            remote_user=self.username)

        self.cloud_executor = executor.AnsibleRunner(
            remote_user=self.username,
            ssh_common_args='-o ProxyCommand="ssh -W %%h:%%p %s@%s"' %
                            (self.username, self.master_node_address))

        self.cached_cloud_hosts = None
        self.fqdn_to_hosts = dict()

    def verify(self):
        """Verify connection to the cloud."""
        hosts = self._get_cloud_hosts()
        logging.debug('Cloud hosts: %s', hosts)

        task = {'command': 'hostname'}
        host_addrs = [n['ip'] for n in hosts]
        logging.debug('Cloud nodes hostnames: %s',
                      self.execute_on_cloud(host_addrs, task))

        logging.info('Connected to cloud successfully')

    def _get_cloud_hosts(self):
        if not self.cached_cloud_hosts:
            task = {'command': 'fuel2 node list -f json'}
            r = self.execute_on_master_node(task)
            self.cached_cloud_hosts = json.loads(r[0].payload['stdout'])
        return self.cached_cloud_hosts

    def execute_on_master_node(self, task):
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
        :return: Ansible execution result (list of records)
        """
        if raise_on_error:
            return self.cloud_executor.execute(hosts, task)
        else:
            return self.cloud_executor.execute(hosts, task, [])

    def _retrieve_hosts_fqdn(self):
        for host in self._get_cloud_hosts():
            task = {'command': 'fuel2 node show %s -f json' % host['id']}
            r = self.execute_on_master_node(task)
            host_ext = json.loads(r[0].payload['stdout'])
            self.fqdn_to_hosts[host_ext['fqdn']] = host_ext

    def get_nodes(self, fqdns=None):
        """Get nodes in the cloud

        This function returns NodesCollection representing all nodes in the
        cloud or only those that has specified FQDNs.
        :param fqdns: list of FQDNs or None to retrieve all nodes
        :return: NodesCollection
        """
        if not fqdns:
            # return all hosts
            hosts = self._get_cloud_hosts()
            return FuelNodeCollection(cloud_management=self,
                                      power_management=self.power_management,
                                      hosts=hosts)
        # return only specified
        if not self.fqdn_to_hosts:
            self._retrieve_hosts_fqdn()

        hosts = [self.fqdn_to_hosts[k] for k in fqdns]
        return FuelNodeCollection(cloud_management=self,
                                  power_management=self.power_management,
                                  hosts=hosts)

    def get_service(self, name):
        """Get service with specified name

        :param name: name of the serives
        :return: Service
        """
        if name in SERVICE_NAME_TO_CLASS:
            klazz = SERVICE_NAME_TO_CLASS[name]
            return klazz(cloud_management=self,
                         power_management=self.power_management)
