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


PORT_SCHEMA = {
    'type': 'array',
    'items': [
        {'enum': ['tcp', 'udp']},
        {'type': 'integer', 'minimum': 0, 'maximum': 65535},
    ],
    'minItems': 2,
    'maxItems': 2,
}

AUTH_SCHEMA = {
    'type': 'object',
    'properties': {
        'username': {'type': 'string'},
        'password': {'type': 'string'},
        'private_key_file': {'type': 'string'},
        'become_username': {'type': 'string'},
        'become_password': {'type': 'string'},
        'become_method': {'type': 'string'},
        'jump': {
            'type': 'object',
            'properties': {
                'host': {'type': 'string'},
                'username': {'type': 'string'},
                'private_key_file': {'type': 'string'},
            },
            'required': ['host'],
            'additionalProperties': False,
        },
    },
    'additionalProperties': False,
}

SERIAL = {'type': 'integer', 'minimum': 1}
