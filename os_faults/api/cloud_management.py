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


@six.add_metaclass(abc.ABCMeta)
class CloudManagement(base_driver.BaseDriver):
    def __init__(self):
        self.power_management = None

    def set_power_management(self, power_management):
        self.power_management = power_management

    @abc.abstractmethod
    def verify(self):
        """Verify connection to the cloud.

        """
        pass

    @abc.abstractmethod
    def get_nodes(self, fqdns=None):
        """Get nodes in the cloud

        This function returns NodesCollection representing all nodes in the
        cloud or only those that has specified FQDNs.
        :param fqdns list of FQDNs or None to retrieve all nodes
        :return: NodesCollection
        """
        pass

    @abc.abstractmethod
    def get_service(self, name):
        """Get service with specified name

        :param name: name of the serives
        :return: Service
        """
        pass

    @classmethod
    def list_supported_services(cls):
        """Lists all services supported by this driver

        :return: [String] list of service names
        """
        return cls.SUPPORTED_SERVICES

    @classmethod
    def list_supported_networks(cls):
        """Lists all networks supported by nodes returned by this driver

        :return: [String] list of network names
        """
        return cls.SUPPORTED_NETWORKS
