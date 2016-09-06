# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import pbr.version

from os_faults.drivers import devstack
from os_faults.drivers import fuel
from os_faults.drivers import ipmi
from os_faults.drivers import libvirt_driver

__version__ = pbr.version.VersionInfo('os_faults').version_string()


def connect(cloud_config):
    cloud_management = None
    cloud_management_params = cloud_config.get('cloud_management') or {}

    if cloud_management_params.get('driver') == 'fuel':
        cloud_management = fuel.FuelManagement(cloud_management_params)
    elif cloud_management_params.get('driver') == 'devstack':
        cloud_management = devstack.DevStackManagement(cloud_management_params)

    power_management = None
    power_management_params = cloud_config.get('power_management') or {}

    if power_management_params.get('driver') == 'libvirt':
        power_management = libvirt_driver.LibvirtDriver(
            power_management_params)
    elif power_management_params.get('driver') == 'ipmi':
        power_management = ipmi.IPMIDriver(power_management_params)

    cloud_management.set_power_management(power_management)

    return cloud_management
