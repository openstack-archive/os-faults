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


@six.add_metaclass(abc.ABCMeta)
class NodeCollection(object):

    @abc.abstractmethod
    def pick(self):
        """Pick one Node out of collection

        :return: NodeCollection consisting just one node
        """

    def reboot(self):
        """Reboot all nodes gracefully

        """
        raise NotImplementedError

    def oom(self):
        """Fill all node's RAM

        """
        raise NotImplementedError

    def poweroff(self):
        """Power off all nodes abruptly

        """
        raise NotImplementedError

    def poweron(self):
        """Power on all nodes abruptly

        """
        raise NotImplementedError

    def reset(self):
        """Reset (cold restart) all nodes

        """
        raise NotImplementedError

    def disable_network(self, network_name):
        """Disable network with name network_name on each of the nodes

        :param network_name: name of network
        """
        raise NotImplementedError

    def enable_network(self, network_name):
        """Enable network with name network_name on each of the nodes

        :param network_name: name of network
        """
        raise NotImplementedError
