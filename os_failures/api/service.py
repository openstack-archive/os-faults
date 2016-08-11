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
class Service(object):

    @abc.abstractmethod
    def get_nodes(self):
        """Get nodes where this Service is running

        :return: NodesCollection
        """
        pass

    def restart(self):
        """Restart the Service

        """
        raise NotImplementedError

    def terminate(self):
        """Terminate the Service gracefully

        """
        raise NotImplementedError

    def kill(self):
        """Terminate the Service abruptly

        """
        raise NotImplementedError

    def unplug(self):
        """Unplug the service out of network

        """
        raise NotImplementedError

    def plug(self):
        """Plug the service into network

        """
        raise NotImplementedError
