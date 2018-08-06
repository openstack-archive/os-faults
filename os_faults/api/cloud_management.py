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
import copy
import logging

import jsonschema
import six

from os_faults.api import base_driver
from os_faults.api import error
from os_faults.api import node_collection
from os_faults.api import power_management
from os_faults import registry

LOG = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class CloudManagement(base_driver.BaseDriver):
    SERVICES = {}
    CONTAINERS = {}
    SUPPORTED_NETWORKS = []
    NODE_CLS = node_collection.NodeCollection

    def __init__(self):
        self.power_manager = power_management.PowerManager()
        self.node_discover = None
        self.services = copy.deepcopy(self.SERVICES)
        self.containers = copy.deepcopy(self.CONTAINERS)

    def add_power_management(self, driver):
        self.power_manager.add_driver(driver)

    def set_node_discover(self, node_discover):
        self.node_discover = node_discover

    def update_services(self, services):
        self.services.update(services)

    def update_containers(self, containers):
        self.containers.update(containers)

    def validate_services(self):
        for service_name, serive_conf in self.services.items():
            serive_cls = registry.get_driver(serive_conf["driver"])
            jsonschema.validate(serive_conf['args'], serive_cls.CONFIG_SCHEMA)

    def validate_containers(self):
        for container_name, container_conf in self.containers.items():
            container_cls = registry.get_driver(container_conf["driver"])
            jsonschema.validate(container_conf['args'],
                                container_cls.CONFIG_SCHEMA)

    @abc.abstractmethod
    def verify(self):
        """Verify connection to the cloud.

        """

    def get_nodes(self, fqdns=None):
        """Get nodes in the cloud

        This function returns NodesCollection representing all nodes in the
        cloud or only those that has specified FQDNs.
        :param fqdns list of FQDNs or None to retrieve all nodes
        :return: NodesCollection
        """

        if self.node_discover is None:
            raise error.OSFError(
                'node_discover is not specified and "{}" '
                'driver does not support discovering'.format(self.NAME))
        hosts = self.node_discover.discover_hosts()
        nodes = self.NODE_CLS(cloud_management=self, hosts=hosts)

        if fqdns:
            LOG.debug('Trying to find nodes with FQDNs: %s', fqdns)
            nodes = nodes.filter(lambda node: node.fqdn in fqdns)
            LOG.debug('The following nodes were found: %s', nodes.hosts)
        return nodes

    def get_service(self, name):
        """Get service with specified name

        :param name: name of the service
        :return: Service
        """
        if name not in self.services:
            raise error.ServiceError(
                '{} driver does not support {!r} service'.format(
                    self.NAME.title(), name))

        config = self.services[name]
        klazz = registry.get_driver(config["driver"])
        return klazz(node_cls=self.NODE_CLS, cloud_management=self,
                     service_name=name, config=config["args"],
                     hosts=config.get('hosts'))

    def get_container(self, name):
        """Get container with specified name

        :param name: name of the container
        :return: Container
        """
        if name not in self.containers:
            raise error.ContainerError(
                '{} driver does not support {!r} container'.format(
                    self.NAME.title(), name))

        config = self.containers[name]
        klazz = registry.get_driver(config["driver"])
        return klazz(node_cls=self.NODE_CLS, cloud_management=self,
                     container_name=name, config=config["args"],
                     hosts=config.get('hosts'))

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
        return cls.SERVICES.keys()

    @classmethod
    def list_supported_networks(cls):
        """Lists all networks supported by nodes returned by this driver

        :return: [String] list of network names
        """
        return cls.SUPPORTED_NETWORKS
