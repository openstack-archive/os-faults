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

import os_failures


def main():
    cloud_config = {
        'auth': {
            'username': 'admin',
            'password': 'admin',
            'project_name': 'admin',
        },
        'region_name': 'RegionOne',
        'cloud_management': {
            'driver': 'fuel',
            'address': '172.18.171.149',
            'username': 'root',
            'password': 'r00tme',
        },
        'power_management': {
            'driver': 'kvm',
            'address': '172.18.171.5',
            'username': 'root',
        }
    }
    client = os_failures.build_client(cloud_config)
    service = client.get_service(name='keystone-api')
    print(service)
    service.stop()

    nodes = service.get_nodes()
    print(nodes)
    nodes.reboot()

    one = nodes.pick()
    one.poweroff()


if __name__ == '__main__':
    main()