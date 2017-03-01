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
from os_faults.api import error
from os_faults import utils


@six.add_metaclass(abc.ABCMeta)
class PowerDriver(base_driver.BaseDriver):

    @abc.abstractmethod
    def supports(host):
        """Returns True if host is supported by the power driver"""

    @abc.abstractmethod
    def poweroff(self, host):
        """Power off host abruptly"""

    @abc.abstractmethod
    def poweron(self, host):
        """Power on host"""

    @abc.abstractmethod
    def reset(self, host):
        """Reset host"""

    @abc.abstractmethod
    def shutdown(self, host):
        """Graceful shutdown host"""

    def snapshot(self, host, snapshot_name, suspend=True):
        raise NotImplementedError

    def revert(self, host, snapshot_name, resume=True):
        raise NotImplementedError


class PowerManager(object):

    def __init__(self):
        self.power_drivers = []

    def add_driver(self, driver):
        self.power_drivers.append(driver)

    def _map_hosts_to_driver(self, hosts):
        driver_host_pairs = []
        for host in hosts:
            for power_driver in self.power_drivers:
                if power_driver.supports(host):
                    driver_host_pairs.append((power_driver, host))
                    break
            else:
                raise error.PowerManagementError(
                    "No supported driver found for host {}".format(host))
        return driver_host_pairs

    def _run_command(self, cmd, hosts, **kwargs):
        driver_host_pairs = self._map_hosts_to_driver(hosts)
        tw = utils.ThreadsWrapper()
        for driver, host in driver_host_pairs:
            kwargs['host'] = host
            fn = getattr(driver, cmd)
            tw.start_thread(fn, **kwargs)
        tw.join_threads()
        if tw.errors:
            raise error.PowerManagementError(
                'There are some errors when working the driver. '
                'Please, check logs for more details.')

    def poweroff(self, hosts):
        self._run_command('poweroff', hosts)

    def poweron(self, hosts):
        self._run_command('poweron', hosts)

    def reset(self, hosts):
        self._run_command('reset', hosts)

    def shutdown(self, hosts):
        self._run_command('shutdown', hosts)

    def snapshot(self, hosts, snapshot_name, suspend=True):
        self._run_command('snapshot', hosts,
                          snapshot_name=snapshot_name, suspend=suspend)

    def revert(self, hosts, snapshot_name, resume=True):
        self._run_command('revert', hosts,
                          snapshot_name=snapshot_name, resume=resume)
