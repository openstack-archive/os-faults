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


class OSFException(Exception):
    """Base Exception class"""


class OSFError(OSFException):
    """Base Error class"""


class PowerManagementError(OSFError):
    """Base Error class for Power Management API"""


class CloudManagementError(OSFError):
    """Base Error class for Cloud Management API"""


class ServiceError(OSFError):
    """Base Error class for Service API"""


class ContainerError(OSFError):
    """Base Error class for Container API"""


class NodeCollectionError(OSFError):
    """Base Error class for NodeCollection API"""


class OSFDriverNotFound(OSFError):
    """Driver Not Found by os-faults registry"""


class OSFDriverWithSuchNameExists(OSFError):
    """Driver with such name already exists in os-faults registry"""
