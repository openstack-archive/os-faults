import abc


class Client(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_cloud(self):
        pass
