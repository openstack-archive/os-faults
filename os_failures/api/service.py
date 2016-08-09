import abc

import six


@six.add_metaclass(abc.ABCMeta)
class Service(object):

    @abc.abstractmethod
    def get_nodes(self):
        pass

    @abc.abstractmethod
    def stop(self):
        pass
