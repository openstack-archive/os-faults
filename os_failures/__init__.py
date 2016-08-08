# -*- coding: utf-8 -*-

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

from os_failures.drivers import fuel

__version__ = pbr.version.VersionInfo(
    'os_failures').version_string()


def build_client(cloud_config):
    cloud_management = cloud_config.get('cloud_management') or {}
    if 'fuel' in cloud_management:
        return fuel.FuelClient(cloud_management['fuel'])
