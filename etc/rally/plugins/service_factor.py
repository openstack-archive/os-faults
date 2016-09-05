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

from rally.common import logging
from rally import consts
from rally.task import hook

import os_faults


LOG = logging.getLogger(__name__)


@hook.configure(name="service_factor")
class ServiceFactorHook(hook.Hook):
    """Runs service factor using os_faults library."""

    CONFIG_SCHEMA = {
        "type": "object",
        "$schema": consts.JSON_SCHEMA,
        "properties": {
            "verify": {"type": "boolean"},
            "method": {
                "enum": [
                    "kill",
                    "freeze",
                    "unfreeze",
                ]
            },
            "args": {"type": "object"},
            "service": {
                "enum": [
                    "keystone",
                    "mysql",
                    "rabbitmq",
                    "nova-api",
                    "glance-api",
                ]
            },
            "count": {"type": "integer"},
            "cloud_config": {
                "type": "object",
                "properties": {
                    "cloud_management": {"type": "object"},
                    "power_management": {"type": "object"},
                },
                "additionalProperties": False,
            },
        },
        "required": [
            "method",
            "service",
            "cloud_config",
        ],
        "additionalProperties": False,
    }

    def run(self):
        method_name = self.config["method"]
        method_args = self.config.get("args", {})
        service_name = self.config["service"]
        count = self.config.get("count")

        # connect to the cloud
        distractor = os_faults.connect(self.config["cloud_config"])

        # verify that all nodes are available
        if self.config.get("verify"):
            distractor.verify()

        # get service
        service = distractor.get_service(name=service_name)
        nodes = service.get_nodes()

        # apply count
        if count:
            nodes = nodes.pick(count=count)

        # get factor
        factor = getattr(service, method_name)
        method_args["nodes"] = nodes

        # run factor
        factor(**method_args)
        LOG.debug("Done %s(%s)", method_name, method_args)

        # return result
        result = {}
        result["action"] = "{} {} {}".format(
            method_name, count or "all", service_name)
        result["status"] = consts.HookStatus.SUCCESS
        return result
