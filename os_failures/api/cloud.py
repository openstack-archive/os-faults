import abc


class Cloud(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_nodes(self, role):
        pass
