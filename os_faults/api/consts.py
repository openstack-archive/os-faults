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

SERVICE_GLANCE = 'glance'
SERVICE_KEYSTONE = 'keystone'
SERVICE_MEMCACHED = 'memcached'
SERVICE_MYSQL = 'mysql'
SERVICE_NOVA = 'nova'
SERVICE_NOVA_COMPUTE = 'nova-compute'
SERVICE_NOVA_SCHEDULER = 'nova-scheduler'
SERVICE_NEUTRON = 'neutron'
SERVICE_RABBITMQ = 'rabbitmq'

NETWORK_MANAGEMENT = 'management'
NETWORK_PRIVATE = 'private'
NETWORK_PUBLIC = 'public'
NETWORK_STORAGE = 'storage'

SERVICES = [eval(item) for item in dir() if item.startswith('SERVICE_')]
NETWORKS = [eval(item) for item in dir() if item.startswith('NETWORK_')]
