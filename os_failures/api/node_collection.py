import abc

import six


@six.add_metaclass(abc.ABCMeta)
class NodeCollection(object):

    @abc.abstractmethod
    def oom(self):
        pass

    @abc.abstractmethod
    def reboot(self):
        pass

    @abc.abstractmethod
    def pick(self):
        pass

    @abc.abstractmethod
    def poweroff(self):
        pass
