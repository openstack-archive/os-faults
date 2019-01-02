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
import random

from os_faults.api import error
from os_faults.api.utils import public
from os_faults import utils

LOG = logging.getLogger(__name__)


class Host(utils.ComparableMixin, utils.ReprMixin):

    ATTRS = ('ip', 'mac', 'fqdn', 'libvirt_name')

    def __init__(self, ip, mac=None, fqdn=None, libvirt_name=None, auth=None):
        self.ip = ip
        self.mac = mac
        self.fqdn = fqdn
        self.libvirt_name = libvirt_name
        self.auth = auth


class NodeCollection(utils.ReprMixin):

    ATTRS = ('hosts', )

    def __init__(self, cloud_management=None, hosts=None):
        self.cloud_management = cloud_management
        self._hosts = set(hosts)

    @property
    def hosts(self):
        return sorted(self._hosts)

    def __len__(self):
        return len(self._hosts)

    def _check_nodes_types(self, other):
        if type(self) is not type(other):
            raise TypeError(
                'Unsupported operand types: {} and {}'.format(
                    type(self), type(other)))
        if self.cloud_management is not other.cloud_management:
            raise error.NodeCollectionError(
                'NodeCollections have different cloud_managements: '
                '{} and {}'.format(self.cloud_management,
                                   other.cloud_management))

    def __add__(self, other):
        return self.__or__(other)

    def __sub__(self, other):
        self._check_nodes_types(other)
        return self._make_instance(self._hosts - other._hosts)

    def __and__(self, other):
        self._check_nodes_types(other)
        return self._make_instance(self._hosts & other._hosts)

    def __or__(self, other):
        self._check_nodes_types(other)
        return self._make_instance(self._hosts | other._hosts)

    def __xor__(self, other):
        self._check_nodes_types(other)
        return self._make_instance(self._hosts ^ other._hosts)

    def __contains__(self, host):
        return host in self._hosts

    def __iter__(self):
        for host in self.hosts:
            yield host

    def __getitem__(self, item):
        return self.hosts[item]

    def _make_instance(self, hosts):
        return self.__class__(cloud_management=self.cloud_management,
                              hosts=hosts)

    def get_ips(self):
        return [host.ip for host in self.hosts]

    def get_macs(self):
        return [host.mac for host in self.hosts]

    def get_fqdns(self):
        return [host.fqdn for host in self.hosts]

    def pick(self, count=1):
        """Pick one Node out of collection

        :return: NodeCollection consisting just one node
        """
        if count > len(self._hosts):
            msg = 'Cannot pick {} from {} node(s)'.format(
                count, len(self._hosts))
            raise error.NodeCollectionError(msg)
        return self._make_instance(random.sample(self._hosts, count))

    def filter(self, criteria_fn):
        hosts = list(filter(criteria_fn, self._hosts))
        if hosts:
            return self._make_instance(hosts)
        else:
            raise error.NodeCollectionError(
                'No nodes found according to criterion')

    def run_task(self, task, raise_on_error=True):
        """Run ansible task on node colection

        :param task: ansible task as dict
        :param raise_on_error: throw exception in case of error
        :return: AnsibleExecutionRecord with results of task
        """
        LOG.info('Run task: %s on nodes: %s', task, self)
        return self.cloud_management.execute_on_cloud(
            self.hosts, task, raise_on_error=raise_on_error)

    @public
    def reboot(self):
        """Reboot all nodes gracefully

        """
        LOG.info('Reboot nodes: %s', self)
        task = {'command': 'reboot now'}
        self.cloud_management.execute_on_cloud(self.hosts, task)

    @public
    def oom(self):
        """Fill all node's RAM

        """
        raise NotImplementedError

    @public
    def poweroff(self):
        """Power off all nodes abruptly

        """
        LOG.info('Power off nodes: %s', self)
        self.cloud_management.power_manager.poweroff(self.hosts)

    @public
    def poweron(self):
        """Power on all nodes abruptly

        """
        LOG.info('Power on nodes: %s', self)
        self.cloud_management.power_manager.poweron(self.hosts)

    @public
    def reset(self):
        """Reset (cold restart) all nodes

        """
        LOG.info('Reset nodes: %s', self)
        self.cloud_management.power_manager.reset(self.hosts)

    @public
    def shutdown(self):
        """Shutdown all nodes gracefully

        """
        LOG.info('Shutdown nodes: %s', self)
        self.cloud_management.power_manager.shutdown(self.hosts)

    def snapshot(self, snapshot_name, suspend=True):
        """Create snapshot for all nodes

        """
        LOG.info('Create snapshot "%s" for nodes: %s', snapshot_name, self)
        self.cloud_management.power_manager.snapshot(
            self.hosts, snapshot_name, suspend)

    def revert(self, snapshot_name, resume=True):
        """Revert snapshot for all nodes

        """
        LOG.info('Revert snapshot "%s" for nodes: %s', snapshot_name, self)
        self.cloud_management.power_manager.revert(
            self.hosts, snapshot_name, resume)

    @public
    def disconnect(self, network_name):
        """Disconnect nodes from <network_name> network

        :param network_name: name of network
        """
        raise NotImplementedError

    @public
    def connect(self, network_name):
        """Connect nodes to <network_name> network

        :param network_name: name of network
        """
        raise NotImplementedError

    @public
    def stress(self, target, duration=None):
        """Stress node OS and hardware

        """
        duration = duration or 10  # defaults to 10 seconds
        LOG.info('Stress %s for %ss on nodes %s', target, duration, self)
        task = {'stress': {
            'target': target,
            'duration': duration,
        }}
        self.cloud_management.execute_on_cloud(self.hosts, task)
