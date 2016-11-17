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

from os_faults.api import base_driver


@six.add_metaclass(abc.ABCMeta)
class PowerManagement(base_driver.BaseDriver):

    @abc.abstractmethod
    def poweroff(self, hosts):
        pass

    @abc.abstractmethod
    def poweron(self, hosts):
        pass

    @abc.abstractmethod
    def reset(self, hosts):
        pass

    def snapshot(self, hosts, snapshot_name):
        raise NotImplementedError

    def revert(self, hosts, snapshot_name, resume=True):
        raise NotImplementedError
