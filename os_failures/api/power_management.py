import abc

import six


@six.add_metaclass(abc.ABCMeta)
class PowerManagement(object):

    @abc.abstractmethod
    def poweroff(self, hosts):
        pass

    def reset(self, hosts):
        pass
