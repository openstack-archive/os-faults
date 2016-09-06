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


@hook.configure(name="node_factor")
class NodeFactorHook(hook.Hook):
    """Runs node factor using os_faults library."""

    CONFIG_SCHEMA = {
        "type": "object",
        "$schema": consts.JSON_SCHEMA,
        "properties": {
            "verify": {"type": "boolean"},
            "method": {
                "enum": [
                    "poweroff",
                    "poweron",
                    "reset",
                ]
            },
            "args": {"type": "object"},
            "filter": {
                "oneOf": [
                    {
                        "properies": {
                            "service": {
                                "enum": [
                                    "keystone",
                                    "mysql",
                                    "rabbitmq",
                                    "nova-api",
                                    "glance-api",
                                ]
                            },
                        },
                        "required": ["service"]
                    },
                    {
                        "properies": {
                            "role": {"type": "string"}
                        },
                        "required": ["role"]
                    },
                    {
                        "properies": {
                            "fqdn": {"type": "string"}
                        },
                        "required": ["fqdn"]
                    },
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
            "cloud_config",
        ],
        "additionalProperties": False,
    }

    def run(self):
        method_name = self.config["method"]
        method_args = self.config.get("args", {})
        count = self.config.get("count")
        filter_conf = self.config.get("filter", {})
        service_name = filter_conf.get("service")
        fqdn = filter_conf.get("fqdn")
        role = filter_conf.get("role")

        # connect to the cloud
        distractor = os_faults.connect(self.config["cloud_config"])

        # verify that all nodes are available
        if self.config.get("verify"):
            distractor.verify()

        # get nodes
        if service_name:
            service = distractor.get_service(name=service_name)
            nodes = service.get_nodes()
        elif role:
            nodes = distractor.get_nodes().filter(role=role)
        elif fqdn:
            nodes = distractor.get_nodes(fqdn=fqdn)
        else:
            nodes = distractor.get_nodes()

        # apply count
        if count:
            nodes = nodes.pick(count=count)

        # get factor
        factor = getattr(nodes, method_name)

        # run factor
        factor(**method_args)
        LOG.debug("Done %s(%s)", method_name, method_args)

        # return result
        result = {}
        result["action"] = "{} {} {}".format(
            method_name, count or "all",
            service_name or role or fqdn or "node(s)")
        result["status"] = consts.HookStatus.SUCCESS
        return result
