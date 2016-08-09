import abc

import six


@six.add_metaclass(abc.ABCMeta)
class CloudManagement(object):
    def __init__(self):
        self.power_management = None

    @abc.abstractmethod
    def get_nodes(self):
        pass

    @abc.abstractmethod
    def get_service(self, name):
        pass

    def set_power_management(self, power_management):
        self.power_management = power_management
