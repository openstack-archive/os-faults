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

import collections
import logging
import random
import warnings

from os_faults.api import error
from os_faults.api.util import public

LOG = logging.getLogger(__name__)

Host = collections.namedtuple('Host', ['ip', 'mac', 'fqdn'])


class NodeCollection(object):

    def __init__(self, cloud_management=None, power_management=None,
                 hosts=None):
        self.cloud_management = cloud_management
        self.power_management = power_management
        self._hosts = set(hosts)

    @property
    def hosts(self):
        return sorted(self._hosts)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.hosts))

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
        if self.power_management is not other.power_management:
            raise error.NodeCollectionError(
                'NodeCollections have different power_managements: '
                '{} and {}'.format(self.power_management,
                                   other.power_management))

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

    def _make_instance(self, hosts):
        return self.__class__(cloud_management=self.cloud_management,
                              power_management=self.power_management,
                              hosts=hosts)

    def get_ips(self):
        return [host.ip for host in self.hosts]

    def get_macs(self):
        return [host.mac for host in self.hosts]

    def get_fqdns(self):
        return [host.fqdn for host in self.hosts]

    def iterate_hosts(self):
        warnings.warn('iterate_hosts is deprecated, use __iter__ instead',
                      DeprecationWarning, stacklevel=2)
        return self.__iter__()

    def pick(self, count=1):
        """Pick one Node out of collection

        :return: NodeCollection consisting just one node
        """
        if count > len(self._hosts):
            msg = 'Cannot pick {} from {} node(s)'.format(
                count, len(self._hosts))
            raise error.NodeCollectionError(msg)
        return self._make_instance(random.sample(self._hosts, count))

    def run_task(self, task, raise_on_error=True):
        """Run ansible task on node colection

        :param task: ansible task as dict
        :param raise_on_error: throw exception in case of error
        :return: AnsibleExecutionRecord with results of task
        """
        LOG.info('Run task: %s on nodes: %s', task, self)
        return self.cloud_management.execute_on_cloud(
            self.get_ips(), task, raise_on_error=raise_on_error)

    @public
    def reboot(self):
        """Reboot all nodes gracefully

        """
        LOG.info('Reboot nodes: %s', self)
        task = {'command': 'reboot now'}
        self.cloud_management.execute_on_cloud(self.get_ips(), task)

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
        self.power_management.poweroff(self.get_macs())

    @public
    def poweron(self):
        """Power on all nodes abruptly

        """
        LOG.info('Power on nodes: %s', self)
        self.power_management.poweron(self.get_macs())

    @public
    def reset(self):
        """Reset (cold restart) all nodes

        """
        LOG.info('Reset nodes: %s', self)
        self.power_management.reset(self.get_macs())

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
    def stresscpu(self):
        """Induces CPU stress

        """
        raise NotImplementedError

    @public
    def stressmem(self):
        """Induces Memory stress

        """
        raise NotImplementedError

    @public
    def stressdisk(self):
        """Induces Disk stress

        """
        raise NotImplementedError

