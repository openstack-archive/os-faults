#!/bin/bash -x

KEY_FILE_NAME="${HOME}/.ssh/os_faults"
USERNAME="root"
HOST="172.18.171.149"

echo "removing old key if exist"
rm ${KEY_FILE_NAME} | true

echo "generating new key in ${KEY_FILE_NAME}"
ssh-keygen -b 4096 -f ${KEY_FILE_NAME} -q -t rsa -P ""

echo "copying the key to master node ${USERNAME}@${HOST}"
ssh-copy-id -i ${KEY_FILE_NAME} -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no ${USERNAME}@${HOST}

echo "get list of nodes in the cluster"

for NODE in `ssh -i ${KEY_FILE_NAME} -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no ${USERNAME}@${HOST} fuel2 node list -c ip -f value`; do
  echo "copying the key to node ${NODE}"
  ssh-copy-id -i ${KEY_FILE_NAME} -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o ProxyCommand="ssh -W %h:%p ${USERNAME}@${HOST}" root@${NODE}
  ssh -i ${KEY_FILE_NAME} -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o ProxyCommand="ssh -W %h:%p ${USERNAME}@${HOST}" root@${NODE} hostname
done

