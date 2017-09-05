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

import six

from os_faults.api import base_driver
from os_faults.api.utils import public


@six.add_metaclass(abc.ABCMeta)
class Service(base_driver.BaseDriver):

    def __init__(self, service_name, config, node_cls, cloud_management,
                 hosts=None):
        self.service_name = service_name
        self.config = config
        self.node_cls = node_cls
        self.cloud_management = cloud_management
        self.hosts = hosts

    @abc.abstractmethod
    def discover_nodes(self):
        """Discover nodes where this Service is running

        :returns: NodesCollection
        """

    def get_nodes(self):
        """Get nodes where this Service is running

        :returns: NodesCollection
        """
        if self.hosts is not None:
            nodes = self.cloud_management.get_nodes()
            hosts = [h for h in nodes.hosts if h.ip in self.hosts]
            return self.node_cls(cloud_management=self.cloud_management,
                                 hosts=hosts)
        return self.discover_nodes()

    @public
    def restart(self, nodes=None):
        """Restart Service on all nodes or on particular subset

        :param nodes: NodesCollection
        """
        raise NotImplementedError

    @public
    def terminate(self, nodes=None):
        """Terminate Service gracefully on all nodes or on particular subset

        :param nodes: NodesCollection
        """
        raise NotImplementedError

    @public
    def start(self, nodes=None):
        """Start Service on all nodes or on particular subset

        :param nodes: NodesCollection
        """
        raise NotImplementedError

    @public
    def kill(self, nodes=None):
        """Terminate Service abruptly on all nodes or on particular subset

        :param nodes: NodesCollection
        """
        raise NotImplementedError

    @public
    def unplug(self, nodes=None):
        """Unplug Service out of network on all nodes or on particular subset

        :param nodes: NodesCollection
        """
        raise NotImplementedError

    @public
    def plug(self, nodes=None):
        """Plug Service into network on all nodes or on particular subset

        :param nodes: NodesCollection
        """
        raise NotImplementedError

    @public
    def freeze(self, nodes=None, sec=None):
        """Pause service execution

        Send SIGSTOP to Service into network on all nodes or on particular
        subset. If sec is defined - it mean Service will be stopped for
        a wile.

        :param nodes: NodesCollection
        :param sec: int
        """
        raise NotImplementedError

    @public
    def unfreeze(self, nodes=None):
        """Resume service execution

        Send SIGCONT to Service into network on all nodes or on particular
        subset.

        :param nodes: NodesCollection
        """
        raise NotImplementedError
