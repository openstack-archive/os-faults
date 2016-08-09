import abc


class ServiceCollection(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_nodes(self):
        pass

    @abc.abstractmethod
    def stop(self):
        pass
