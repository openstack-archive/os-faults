import abc


class NodeCollection(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def kill_process(self):
        pass

    @abc.abstractmethod
    def oom(self):
        pass

    @abc.abstractmethod
    def reboot(self):
        pass
