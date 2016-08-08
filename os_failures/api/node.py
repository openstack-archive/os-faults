import abc


class Node(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def kill_process(self, group):
        pass

    @abc.abstractmethod
    def oom(self, group):
        pass

    @abc.abstractmethod
    def reboot(self, group):
        pass
