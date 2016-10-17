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

from os_faults.api import error
from os_faults.api.util import public

Host = collections.namedtuple('Host', ['ip', 'mac', 'fqdn'])


class NodeCollection(object):

    def __init__(self, cloud_management=None, power_management=None,
                 hosts=None):
        self.cloud_management = cloud_management
        self.power_management = power_management
        self.hosts = hosts

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.hosts))

    def __len__(self):
        return len(self.hosts)

    def get_ips(self):
        return [host.ip for host in self.hosts]

    def get_macs(self):
        return [host.mac for host in self.hosts]

    def iterate_hosts(self):
        for host in self.hosts:
            yield host

    def pick(self, count=1):
        """Pick one Node out of collection

        :return: NodeCollection consisting just one node
        """
        if count > len(self.hosts):
            msg = 'Cannot pick {} from {} node(s)'.format(
                count, len(self.hosts))
            raise error.NodeCollectionError(msg)
        return self.__class__(cloud_management=self.cloud_management,
                              power_management=self.power_management,
                              hosts=random.sample(self.hosts, count))

    def run_task(self, task, raise_on_error=True):
        """Run ansible task on node colection

        :param task: ansible task as dict
        :param raise_on_error: throw exception in case of error
        :return: AnsibleExecutionRecord with results of task
        """
        logging.info('Run task: %s on nodes: %s', task, self)
        return self.cloud_management.execute_on_cloud(
            self.get_ips(), task, raise_on_error=raise_on_error)

    @public
    def reboot(self):
        """Reboot all nodes gracefully

        """
        logging.info('Reboot nodes: %s', self)
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
        logging.info('Power off nodes: %s', self)
        self.power_management.poweroff(self.get_macs())

    @public
    def poweron(self):
        """Power on all nodes abruptly

        """
        logging.info('Power on nodes: %s', self)
        self.power_management.poweron(self.get_macs())

    @public
    def reset(self):
        """Reset (cold restart) all nodes

        """
        logging.info('Reset nodes: %s', self)
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
