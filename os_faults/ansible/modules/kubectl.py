#!/usr/bin/python

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

from ansible.module_utils.basic import *  # noqa


def build_cmd(**params):
    cmd = 'kubectl -n %(namespace)s %(command)s' % params

    if params.get('resource'):
        cmd += ' %s' % params['resource']

    if params.get('selector'):
        cmd += ' -l %s' % params['selector']

    if params.get('nodes'):
        cmd += (' --template \'{{range .items}}'
                '{{if eq .spec.nodeName %s}}'
                '{{.metadata.name}}'
                '{{" "}}'
                '{{end}}'
                '{{end}}\''
                % ' '.join('"%s"' % n for n in params['nodes'])
                )

    if params.get('jsonpath'):
        cmd += ' -o jsonpath=%s' % params['jsonpath']

    if params.get('names'):
        cmd += ' ' + ' '.join(params['names'])

    if params.get('container'):
        cmd += ' -c %s' % params.get('container')

    return cmd


def get_pod_names(module, namespace, selector, nodes):
    cmd = build_cmd(namespace=namespace, command='get', resource='pod',
                    selector=selector, nodes=nodes)
    rc, stdout, stderr = module.run_command(cmd, check_rc=True)
    pod_names = stdout.split()

    return pod_names


def main():
    module = AnsibleModule(
        argument_spec=dict(
            namespace=dict(required=True, type='str'),
            command=dict(required=True, type='str'),
            resource=dict(type='str', default='pod'),
            selector=dict(type='str'),
            jsonpath=dict(type='str'),
            nodes=dict(type='list'),
            container=dict(type='str'),
            pod_action=dict(type='str', choices=['kill']),
            grep_process=dict(type='str'),
        ))

    params = module.params

    if params['command'] == 'exec':
        pod_names = get_pod_names(module, params['namespace'],
                                  params['selector'], params['nodes'])
        cmd = ''
        stdout = ''
        stderr = ''
        rc = 0

        try:
            for pod_name in pod_names:
                cmd2 = build_cmd(namespace=params['namespace'],
                                 command='exec',
                                 names=[pod_name],
                                 container=params['container'])
                if params['pod_action'] == 'kill':
                    kube_cmd = 'kubectl -n ccp exec %s' % pod_name
                    if params['container']:
                        kube_cmd += ' -c ' + params['container']

                    cmd2 = ('bash -c "' + cmd2 +
                            ' -- ps ax | grep %(grep_process)s | '
                            'awk \'{print $1}\' | '
                            'xargs %(kube_cmd)s '
                            '-- kill -9"' % dict(
                                grep_process=params['grep_process'],
                                kube_cmd=kube_cmd))

                    with open('/root/bbb', 'a') as fd:
                        fd.write(cmd2)
                        fd.write('\n')

                    cmd += cmd2

                    rc, stdout2, stderr2 = module.run_command(
                        cmd2, check_rc=True)

                    stdout += stdout2
                    stderr += stderr2
        except Exception as e:
            module.exit_json(cmd=cmd, rc=rc, stderr=stderr, stdout=stdout, e=e)

    elif params['command'] != 'get':
        # only 'get' supports filtering via --template
        # need to query resource first and then apply the action
        pod_names = get_pod_names(module, params['namespace'],
                                  params['selector'], params['nodes'])

        cmd = build_cmd(namespace=params['namespace'],
                        command=params['command'],
                        resource=params['resource'],
                        names=pod_names,
                        )
        rc, stdout, stderr = module.run_command(cmd, check_rc=True)
    else:
        cmd = build_cmd(**params)
        rc, stdout, stderr = module.run_command(cmd, check_rc=True)

    module.exit_json(cmd=cmd, rc=rc, stderr=stderr, stdout=stdout)


if __name__ == '__main__':
    main()
