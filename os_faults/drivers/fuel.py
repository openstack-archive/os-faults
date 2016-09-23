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
            yield host

    def pick(self, count=1):
        if count > len(self.hosts):
            msg = 'Cannot pick {} from {} node(s)'.format(
                count, len(self.hosts))
            raise error.NodeCollectionError(msg)
        return FuelNodeCollection(cloud_management=self.cloud_management,
                                  power_management=self.power_management,
                                  hosts=random.sample(self.hosts, count))

    def reboot(self):
        raise NotImplementedError

    def oom(self):
        raise NotImplementedError

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

    def _run_task(self, task, nodes):
        ips = nodes.get_ips()
        if not ips:
            raise error.ServiceError('Node collection is empty')

        results = self.cloud_management.execute_on_cloud(ips, task)
        err = False
        for result in results:
            if result.status != executor.STATUS_OK:
                logging.error(
                    'Task {} failed on node {}'.format(task, result.host))
                err = True
        if err:
            raise error.ServiceError('Task failed on some nodes')
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
        nodes = nodes if nodes is not None else self.get_nodes()
        task_result = self._run_task({'command': self.RESTART_CMD}, nodes)
        logging.info('Restart %s, result: %s', str(self.__class__),
                     task_result)

    def kill(self, nodes=None):
        nodes = nodes if nodes is not None else self.get_nodes()
        task_result = self._run_task({'command': self.KILL_CMD}, nodes)
        logging.info('SIGKILL %s, result: %s', str(self.__class__),
                     task_result)

    def freeze(self, nodes=None, sec=None):
        nodes = nodes if nodes is not None else self.get_nodes()
        cmd = self.FREEZE_SEC_CMD.format(sec) if sec else self.FREEZE_CMD
        task_result = self._run_task({'command': cmd}, nodes)
        logging.info('FREEZE({0}) {1}, result: {2}'.format(sec or '',
                     self.__class__, task_result))

    def unfreeze(self, nodes=None):
        nodes = nodes if nodes is not None else self.get_nodes()
        task_result = self._run_task({'command': self.UNFREEZE_CMD}, nodes)
        logging.info('UNFREEZE %s, result: %s', str(self.__class__),
                     task_result)

    def plug(self, nodes=None):
        nodes = nodes if nodes is not None else self.get_nodes()
        task_result = self._run_task(
            {'command': self.PLUG_CMD.format(self.PORT)}, nodes)
        logging.info('Open port %s, result: %s', str(self.__class__),
                     task_result)

    def unplug(self, nodes=None):
        nodes = nodes if nodes is not None else self.get_nodes()
        task_result = self._run_task(
            {'command': self.UNPLUG_CMD.format(self.PORT)}, nodes)
        logging.info('Close port %s, result: %s', str(self.__class__),
                     task_result)


class KeystoneService(FuelService):
    GET_NODES_CMD = 'bash -c "ps ax | grep \'[k]eystone-main\'"'
    KILL_CMD = ('bash -c "ps ax | grep [k]eystone'
                ' | awk {\'print $1\'} | xargs kill -9"')
    RESTART_CMD = 'service apache2 restart'
    FREEZE_CMD = ('bash -c "ps ax | grep [k]eystone'
                  ' | awk {\'print $1\'} | xargs kill -19"')
    FREEZE_SEC_CMD = ('bash -c "tf=$(mktemp /tmp/script.XXXXXX);'
                      'echo -n \'#!\' > $tf; '
                      'echo -en \'/bin/bash\\npids=`ps ax | '
                      'grep [k]eystone | awk {{\\047print $1\\047}}`; '
                      'echo $pids | xargs kill -19; sleep {0}; '
                      'echo $pids | xargs kill -18; rm \' >> $tf; '
                      'echo -n $tf >> $tf; '
                      'chmod 770 $tf; nohup $tf &"')
    UNFREEZE_CMD = ('bash -c "ps ax | grep [k]eystone'
                    ' | awk {\'print $1\'} | xargs kill -18"')


class MemcachedService(FuelService):
    GET_NODES_CMD = 'bash -c "ps ax | grep \'[m]emcached\'"'
    KILL_CMD = ('bash -c "ps ax | grep [m]emcached'
                ' | awk {\'print $1\'} | xargs kill -9"')
    RESTART_CMD = 'service memcached restart'
    FREEZE_CMD = ('bash -c "ps ax | grep [m]emcached'
                  ' | awk {\'print $1\'} | xargs kill -19"')
    FREEZE_SEC_CMD = ('bash -c "tf=$(mktemp /tmp/script.XXXXXX);'
                      'echo -n \'#!\' > $tf; '
                      'echo -en \'/bin/bash\\npids=`ps ax | '
                      'grep [m]emcached | awk {{\\047print $1\\047}}`; '
                      'echo $pids | xargs kill -19; sleep {0}; '
                      'echo $pids | xargs kill -18; rm \' >> $tf; '
                      'echo -n $tf >> $tf; '
                      'chmod 770 $tf; nohup $tf &"')
    UNFREEZE_CMD = ('bash -c "ps ax | grep [m]emcached'
                    ' | awk {\'print $1\'} | xargs kill -18"')


class MySQLService(FuelService):
    GET_NODES_CMD = 'bash -c "netstat -tap | grep \'.*LISTEN.*mysqld\'"'
    KILL_CMD = ('bash -c "ps ax | grep [m]ysqld'
                ' | awk {\'print $1\'} | xargs kill -9"')
    FREEZE_CMD = ('bash -c "ps ax | grep [m]ysqld'
                  ' | awk {\'print $1\'} | xargs kill -19"')
    FREEZE_SEC_CMD = ('bash -c "tf=$(mktemp /tmp/script.XXXXXX);'
                      'echo -n \'#!\' > $tf; '
                      'echo -en \'/bin/bash\\npids=`ps ax | '
                      'grep [m]ysqld | awk {{\\047print $1\\047}}`; '
                      'echo $pids | xargs kill -19; sleep {0}; '
                      'echo $pids | xargs kill -18; rm \' >> $tf; '
                      'echo -n $tf >> $tf; '
                      'chmod 770 $tf; nohup $tf &"')
    UNFREEZE_CMD = ('bash -c "ps ax | grep [m]ysqld'
                    ' | awk {\'print $1\'} | xargs kill -18"')
    PORT = 3307
    PLUG_CMD = ('bash -c "rule=`iptables -L INPUT -n --line-numbers | '
                'grep \"MySQL_temporary_DROP\" | cut -d \' \' -f1`; '
                'for arg in $rule; do iptables -D INPUT -p tcp --dport {0} '
                '-j DROP -m comment --comment "MySQL_temporary_DROP"; done"')
    UNPLUG_CMD = ('bash -c "iptables -I INPUT 1 -p tcp --dport {0} -j DROP '
                  '-m comment --comment \"MySQL_temporary_DROP\""')


class RabbitMQService(FuelService):
    GET_NODES_CMD = 'bash -c "rabbitmqctl status | grep \'pid,\'"'
    KILL_CMD = ('bash -c "ps ax | grep \'[r]abbit tcp_listeners\''
                ' | awk {\'print $1\'} | xargs kill -9"')
    FREEZE_CMD = ('bash -c "ps ax | grep \'[r]abbit tcp_listeners\''
                  ' | awk {\'print $1\'} | xargs kill -19"')
    FREEZE_SEC_CMD = ('bash -c "tf=$(mktemp /tmp/script.XXXXXX);'
                      'echo -n \'#!\' > $tf; '
                      'echo -en \'/bin/bash\\npids=`ps ax | '
                      'grep \\047[r]abbit tcp_listeners\\047 | '
                      'awk {{\\047print $1\\047}}`; '
                      'echo $pids | xargs kill -19; sleep {0}; '
                      'echo $pids | xargs kill -18; rm \' >> $tf; '
                      'echo -n $tf >> $tf; '
                      'chmod 770 $tf; nohup $tf &"')
    UNFREEZE_CMD = ('bash -c "ps ax | grep \'[r]abbit tcp_listeners\''
                    ' | awk {\'print $1\'} | xargs kill -18"')


class NovaAPIService(FuelService):
    GET_NODES_CMD = 'bash -c "ps ax | grep \'[n]ova-api\'"'
    KILL_CMD = ('bash -c "ps ax | grep [n]ova-api'
                ' | awk {\'print $1\'} | xargs kill -9"')
    RESTART_CMD = 'service nova-api restart'
    FREEZE_CMD = ('bash -c "ps ax | grep [n]ova-api'
                  ' | awk {\'print $1\'} | xargs kill -19"')
    FREEZE_SEC_CMD = ('bash -c "tf=$(mktemp /tmp/script.XXXXXX);'
                      'echo -n \'#!\' > $tf; '
                      'echo -en \'/bin/bash\\npids=`ps ax | '
                      'grep [n]ova-api | awk {{\\047print $1\\047}}`; '
                      'echo $pids | xargs kill -19; sleep {0}; '
                      'echo $pids | xargs kill -18; rm \' >> $tf; '
                      'echo -n $tf >> $tf; '
                      'chmod 770 $tf; nohup $tf &"')
    UNFREEZE_CMD = ('bash -c "ps ax | grep [n]ova-api'
                    ' | awk {\'print $1\'} | xargs kill -18"')


class GlanceAPIService(FuelService):
    GET_NODES_CMD = 'bash -c "ps ax | grep \'[g]lance-api\'"'
    KILL_CMD = ('bash -c "ps ax | grep [g]lance-api'
                ' | awk {\'print $1\'} | xargs kill -9"')
    RESTART_CMD = 'service glance-api restart'
    FREEZE_CMD = ('bash -c "ps ax | grep [g]lance-api'
                  ' | awk {\'print $1\'} | xargs kill -19"')
    FREEZE_SEC_CMD = ('bash -c "tf=$(mktemp /tmp/script.XXXXXX);'
                      'echo -n \'#!\' > $tf; '
                      'echo -en \'/bin/bash\\npids=`ps ax | '
                      'grep [g]lance-api | awk {{\\047print $1\\047}}`; '
                      'echo $pids | xargs kill -19; sleep {0}; '
                      'echo $pids | xargs kill -18; rm \' >> $tf; '
                      'echo -n $tf >> $tf; '
                      'chmod 770 $tf; nohup $tf &"')
    UNFREEZE_CMD = ('bash -c "ps ax | grep [g]lance-api'
                    ' | awk {\'print $1\'} | xargs kill -18"')


class NovaComputeService(FuelService):
    GET_NODES_CMD = 'bash -c "ps ax | grep \'[n]ova-compute\'"'
    KILL_CMD = ('bash -c "ps ax | grep [n]ova-compute'
                ' | awk {\'print $1\'} | xargs kill -9"')
    RESTART_CMD = 'service nova-compute restart'
    FREEZE_CMD = ('bash -c "ps ax | grep [n]ova-compute'
                  ' | awk {\'print $1\'} | xargs kill -19"')
    FREEZE_SEC_CMD = ('bash -c "tf=$(mktemp /tmp/script.XXXXXX);'
                      'echo -n \'#!\' > $tf; '
                      'echo -en \'/bin/bash\\npids=`ps ax | '
                      'grep [n]ova-compute | awk {{\\047print $1\\047}}`; '
                      'echo $pids | xargs kill -19; sleep {0}; '
                      'echo $pids | xargs kill -18; rm \' >> $tf; '
                      'echo -n $tf >> $tf; '
                      'chmod 770 $tf; nohup $tf &"')
    UNFREEZE_CMD = ('bash -c "ps ax | grep [n]ova-compute'
                    ' | awk {\'print $1\'} | xargs kill -18"')


class NovaSchedulerService(FuelService):
    GET_NODES_CMD = 'bash -c "ps ax | grep \'[n]ova-scheduler\'"'
    KILL_CMD = ('bash -c "ps ax | grep [n]ova-scheduler'
                ' | awk {\'print $1\'} | xargs kill -9"')
    RESTART_CMD = 'service nova-scheduler restart'
    FREEZE_CMD = ('bash -c "ps ax | grep [n]ova-scheduler'
                  ' | awk {\'print $1\'} | xargs kill -19"')
    FREEZE_SEC_CMD = ('bash -c "tf=$(mktemp /tmp/script.XXXXXX);'
                      'echo -n \'#!\' > $tf; '
                      'echo -en \'/bin/bash\\npids=`ps ax | '
                      'grep [n]ova-scheduler | awk {{\\047print $1\\047}}`; '
                      'echo $pids | xargs kill -19; sleep {0}; '
                      'echo $pids | xargs kill -18; rm \' >> $tf; '
                      'echo -n $tf >> $tf; '
                      'chmod 770 $tf; nohup $tf &"')
    UNFREEZE_CMD = ('bash -c "ps ax | grep [n]ova-scheduler'
                    ' | awk {\'print $1\'} | xargs kill -18"')


class NeutronOpenvswitchAgentService(FuelService):
    GET_NODES_CMD = 'bash -c "ps ax | grep \'[n]eutron-openvswitch-agent\'"'
    KILL_CMD = ('bash -c "ps ax | grep [n]eutron-openvswitch-agent'
                ' | awk {\'print $1\'} | xargs kill -9"')
    RESTART_CMD = ('bash -c "if pcs resource show neutron-openvswitch-agent; '
                   'then pcs resource restart neutron-openvswitch-agent; '
                   'else service neutron-openvswitch-agent restart; fi"')
    FREEZE_CMD = ('bash -c "ps ax | grep [n]eutron-openvswitch-agent'
                  ' | awk {\'print $1\'} | xargs kill -19"')
    FREEZE_SEC_CMD = ('bash -c "tf=$(mktemp /tmp/script.XXXXXX);'
                      'echo -n \'#!\' > $tf; '
                      'echo -en \'/bin/bash\\npids=`ps ax | '
                      'grep [n]eutron-openvswitch-agent'
                      ' | awk {{\\047print $1\\047}}`; '
                      'echo $pids | xargs kill -19; sleep {0}; '
                      'echo $pids | xargs kill -18; rm \' >> $tf; '
                      'echo -n $tf >> $tf; '
                      'chmod 770 $tf; nohup $tf &"')
    UNFREEZE_CMD = ('bash -c "ps ax | grep [n]eutron-openvswitch-agent'
                    ' | awk {\'print $1\'} | xargs kill -18"')


class NeutronL3AgentService(FuelService):
    GET_NODES_CMD = 'bash -c "ps ax | grep \'[n]eutron-l3-agent\'"'
    KILL_CMD = ('bash -c "ps ax | grep [n]eutron-l3-agent'
                ' | awk {\'print $1\'} | xargs kill -9"')
    RESTART_CMD = ('bash -c "if pcs resource show neutron-l3-agent; '
                   'then pcs resource restart neutron-l3-agent; '
                   'else service neutron-l3-agent restart; fi"')
    FREEZE_CMD = ('bash -c "ps ax | grep [n]eutron-l3-agent'
                  ' | awk {\'print $1\'} | xargs kill -19"')
    FREEZE_SEC_CMD = ('bash -c "tf=$(mktemp /tmp/script.XXXXXX);'
                      'echo -n \'#!\' > $tf; '
                      'echo -en \'/bin/bash\\npids=`ps ax | '
                      'grep [n]eutron-l3-agent | awk {{\\047print $1\\047}}`; '
                      'echo $pids | xargs kill -19; sleep {0}; '
                      'echo $pids | xargs kill -18; rm \' >> $tf; '
                      'echo -n $tf >> $tf; '
                      'chmod 770 $tf; nohup $tf &"')
    UNFREEZE_CMD = ('bash -c "ps ax | grep [n]eutron-l3-agent'
                    ' | awk {\'print $1\'} | xargs kill -18"')


class HeatAPIService(FuelService):
    GET_NODES_CMD = 'bash -c "ps ax | grep \'[h]eat-api \'"'
    KILL_CMD = ('bash -c "ps ax | grep \'[h]eat-api \''
                ' | awk {\'print $1\'} | xargs kill -9"')
    RESTART_CMD = 'service heat-api restart'
    FREEZE_CMD = ('bash -c "ps ax | grep \'[h]eat-api \''
                  ' | awk {\'print $1\'} | xargs kill -19"')
    FREEZE_SEC_CMD = ('bash -c "tf=$(mktemp /tmp/script.XXXXXX);'
                      'echo -n \'#!\' > $tf; '
                      'echo -en \'/bin/bash\\npids=`ps ax | '
                      'grep \\047[h]eat-api \\047'
                      ' | awk {{\\047print $1\\047}}`; '
                      'echo $pids | xargs kill -19; sleep {0}; '
                      'echo $pids | xargs kill -18; rm \' >> $tf; '
                      'echo -n $tf >> $tf; '
                      'chmod 770 $tf; nohup $tf &"')
    UNFREEZE_CMD = ('bash -c "ps ax | grep \'[h]eat-api \''
                    ' | awk {\'print $1\'} | xargs kill -18"')


class HeatEngineService(FuelService):
    GET_NODES_CMD = 'bash -c "ps ax | grep [h]eat-engine"'
    KILL_CMD = ('bash -c "ps ax | grep [h]eat-engine'
                ' | awk {\'print $1\'} | xargs kill -9"')
    RESTART_CMD = 'pcs resource restart p_heat-engine'
    FREEZE_CMD = ('bash -c "ps ax | grep [h]eat-engine'
                  ' | awk {\'print $1\'} | xargs kill -19"')
    FREEZE_SEC_CMD = ('bash -c "tf=$(mktemp /tmp/script.XXXXXX);'
                      'echo -n \'#!\' > $tf; '
                      'echo -en \'/bin/bash\\npids=`ps ax | '
                      'grep [h]eat-engine | awk {{\\047print $1\\047}}`; '
                      'echo $pids | xargs kill -19; sleep {0}; '
                      'echo $pids | xargs kill -18; rm \' >> $tf; '
                      'echo -n $tf >> $tf; '
                      'chmod 770 $tf; nohup $tf &"')
    UNFREEZE_CMD = ('bash -c "ps ax | grep [h]eat-engine'
                    ' | awk {\'print $1\'} | xargs kill -18"')


SERVICE_NAME_TO_CLASS = {
    'keystone': KeystoneService,
    'memcached': MemcachedService,
    'mysql': MySQLService,
    'rabbitmq': RabbitMQService,
    'nova-api': NovaAPIService,
    'glance-api': GlanceAPIService,
    'nova-compute': NovaComputeService,
    'nova-scheduler': NovaSchedulerService,
    'neutron-openvswitch-agent': NeutronOpenvswitchAgentService,
    'neutron-l3-agent': NeutronL3AgentService,
    'heat-api': HeatAPIService,
    'heat-engine': HeatEngineService,
}


class FuelManagement(cloud_management.CloudManagement):
    def __init__(self, cloud_management_params):
        super(FuelManagement, self).__init__()

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
        logging.debug('Cloud nodes: %s', hosts)

        task = {'command': 'hostname'}
        host_addrs = [n['ip'] for n in hosts]
        task_result = self.execute_on_cloud(host_addrs, task)
        logging.debug('Hostnames of cloud nodes: %s',
                      [r.payload['stdout'] for r in task_result])

        logging.info('Connected to cloud successfully!')

    def _get_cloud_hosts(self):
        if not self.cached_cloud_hosts:
            task = {'command': 'fuel2 node list -f json'}
            result = self.execute_on_master_node(task)
            for r in json.loads(result[0].payload['stdout']):
                self.cached_cloud_hosts.append(
                    dict(ip=r['ip'], mac=r['mac'],
                         fqdn='node-%s.domain.tld' % r['id']))
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
            self.fqdn_to_hosts[host['fqdn']] = host

    def get_nodes(self, fqdns=None):
        """Get nodes in the cloud

        This function returns NodesCollection representing all nodes in the
        cloud or only those that has specified FQDNs.
        :param fqdns: list of FQDNs or None to retrieve all nodes
        :return: NodesCollection
        """
        if fqdns:
            # return only specified
            logging.debug('Trying to find nodes with FQDNs: %s', fqdns)
            if not self.fqdn_to_hosts:
                self._retrieve_hosts_fqdn()
            hosts = list()
            for fqdn in fqdns:
                if fqdn in self.fqdn_to_hosts:
                    hosts.append(self.fqdn_to_hosts[fqdn])
                else:
                    raise error.NodeCollectionError(
                        'Node with FQDN \'%s\' not found!' % fqdn)
            logging.debug('The following nodes were found: %s', hosts)
        else:
            # return all nodes
            hosts = self._get_cloud_hosts()
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
