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

from os_faults.api.util import public


@six.add_metaclass(abc.ABCMeta)
class Service(object):

    @abc.abstractmethod
    def get_nodes(self):
        """Get nodes where this Service is running

        :return: NodesCollection
        """

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


    @public
    def stresscpu(self, nodes=None):
        """Induce CPU stress

        Call 'stress -c'

        :param nodes: NodesCollection
        """
        raise NotImplementedError

    @public
    def stressmem(self, nodes=None):
        """Induce Memory stress

        Call 'stress -m'

        :param nodes: NodesCollection
        """
        raise NotImplementedError

    @public
    def stressdisk(self, nodes=None):
        """Induce Disk stress

        Call 'stress -d'

        :param nodes: NodesCollection
        """
        raise NotImplementedError
