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

import os

import appdirs
import pbr.version
import yaml

from os_faults.api import error
from os_faults.api import human
from os_faults import registry

__version__ = pbr.version.VersionInfo('os_faults').version_string()


APPDIRS = appdirs.AppDirs(appname='openstack', appauthor='OpenStack')
UNIX_SITE_CONFIG_HOME = '/etc/openstack'
CONFIG_SEARCH_PATH = [
    os.getcwd(),
    APPDIRS.user_config_dir,
    UNIX_SITE_CONFIG_HOME,
]
CONFIG_FILES = [
    os.path.join(d, 'os-faults' + s)
    for d in CONFIG_SEARCH_PATH
    for s in ['.json', '.yaml', '.yml']
]


def _read_config(config_filename):
    os_faults_config = config_filename or os.environ.get('OS_FAULTS_CONFIG')
    if os_faults_config:
        CONFIG_FILES.insert(0, os_faults_config)

    for config_file in CONFIG_FILES:
        if os.path.exists(config_file):
            with open(config_file) as fd:
                return yaml.safe_load(fd.read())

    msg = 'Config file is not found on any of paths: {}'.format(CONFIG_FILES)
    raise error.OSFError(msg)


def _init_driver(params):
    all_drivers = registry.get_drivers()

    name = params.get('driver')
    if not name:
        return None

    if name not in all_drivers:
        raise error.OSFError('Driver %s is not found' % name)

    return all_drivers[name](params)


def connect(cloud_config=None, config_filename=None):
    if not cloud_config:
        cloud_config = _read_config(config_filename)

    cloud_management_params = cloud_config.get('cloud_management') or {}
    cloud_management = _init_driver(cloud_management_params)

    if not cloud_management:
        raise error.OSFError('Cloud management driver is required')

    power_management_params = cloud_config.get('power_management') or {}
    power_management = _init_driver(power_management_params)

    cloud_management.set_power_management(power_management)

    return cloud_management


def human_api(distractor, command):
    """Execute high-level text command with specified destructor

    :param destructor: library instance as returned by :connect: function
    :param command: text command
    """
    human.execute(distractor, command)
