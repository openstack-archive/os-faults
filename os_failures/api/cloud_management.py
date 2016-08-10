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

import six


@six.add_metaclass(abc.ABCMeta)
class CloudManagement(object):
    def __init__(self):
        self.power_management = None

    def set_power_management(self, power_management):
        self.power_management = power_management

    @abc.abstractmethod
    def verify(self):
        pass

    @abc.abstractmethod
    def get_nodes(self):
        pass

    @abc.abstractmethod
    def get_service(self, name):
        pass
