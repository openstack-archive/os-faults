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
from os_faults.api import error


@six.add_metaclass(abc.ABCMeta)
class CloudManagement(base_driver.BaseDriver):
    SERVICE_NAME_TO_CLASS = {}
    SUPPORTED_SERVICES = []
    SUPPORTED_NETWORKS = []

    def __init__(self):
        self.power_management = None

    def set_power_management(self, power_management):
        self.power_management = power_management

    @abc.abstractmethod
    def verify(self):
        """Verify connection to the cloud.

        """

    @abc.abstractmethod
    def get_nodes(self, fqdns=None):
        """Get nodes in the cloud

        This function returns NodesCollection representing all nodes in the
        cloud or only those that has specified FQDNs.
        :param fqdns list of FQDNs or None to retrieve all nodes
        :return: NodesCollection
        """

    def get_service(self, name):
        """Get service with specified name

        :param name: name of the serives
        :return: Service
        """
        if name in self.SERVICE_NAME_TO_CLASS:
            klazz = self.SERVICE_NAME_TO_CLASS[name]
            return klazz(node_cls=self.NODE_CLS,
                         cloud_management=self,
                         power_management=self.power_management)
        raise error.ServiceError(
            '{} driver does not support {!r} service'.format(
                self.NAME.title(), name))

    @abc.abstractmethod
    def execute_on_cloud(self, hosts, task, raise_on_error=True):
        """Execute task on specified hosts within the cloud.

        :param hosts: List of host FQDNs
        :param task: Ansible task
        :param raise_on_error: throw exception in case of error
        :return: Ansible execution result (list of records)
        """

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
