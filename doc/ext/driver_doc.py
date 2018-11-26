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

from docutils.parsers import rst
from os_faults import registry
from sphinx.util import docstrings

from ext import utils


class DriverDocDirective(rst.Directive):

    required_arguments = 1

    def run(self):
        drv_name = self.arguments[0]

        driver = registry.get_driver(drv_name)
        types = ', '.join(class_.__name__ for class_ in driver.__bases__)
        doc = '\n'.join(docstrings.prepare_docstring(driver.__doc__))

        subcat = utils.subcategory('{} [{}]'.format(drv_name, types))
        subcat.extend(utils.parse_text(doc))
        return [subcat]


class CloudDriverDocDirective(rst.Directive):

    required_arguments = 1

    def run(self):
        drv_name = self.arguments[0]

        driver = registry.get_driver(drv_name)
        types = ', '.join(class_.__name__ for class_ in driver.__bases__)
        services = sorted(driver.list_supported_services())
        doc = '\n'.join(docstrings.prepare_docstring(driver.__doc__))

        subcat = utils.subcategory('{} [{}]'.format(drv_name, types))
        subcat.extend(utils.parse_text(doc))
        if services:
            subcat.extend(utils.parse_text('**Default services:**'))
            subcat.extend(utils.rstlist(services))
        return [subcat]


def setup(app):
    app.add_directive('driver_doc', DriverDocDirective)
    app.add_directive('cloud_driver_doc', CloudDriverDocDirective)
