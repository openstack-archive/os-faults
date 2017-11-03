#!/bin/bash -x

# Distribute SSH keys on all nodes deployed by OpenStack Fuel

KEY_FILE_NAME="${HOME}/.ssh/os_faults"
HOST=${1:-fuel.local}
USERNAME=${2:-root}

echo "distributing keys to Fuel: ${USERNAME}@${HOST}"

if [ ! -f ${KEY_FILE_NAME} ]; then
  echo "generating new key in ${KEY_FILE_NAME}"
  ssh-keygen -b 4096 -f ${KEY_FILE_NAME} -q -t rsa -P ""
fi

echo "copying the key to master node ${USERNAME}@${HOST}"
ssh-copy-id -i ${KEY_FILE_NAME} -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no ${USERNAME}@${HOST}

echo "get list of nodes in the cluster"

for NODE in `ssh -i ${KEY_FILE_NAME} -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no ${USERNAME}@${HOST} fuel2 node list -c ip -f value`; do
  echo "copying the key to node ${NODE}"
  # ssh-copy-id does not copy the key over the hop when the destination is already reachable via its own key
  cat ${KEY_FILE_NAME}.pub | ssh -i ${KEY_FILE_NAME} ${USERNAME}@${HOST} ssh ${NODE} 'tee -a .ssh/authorized_keys'
  ssh -i ${KEY_FILE_NAME} -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -o ProxyCommand="ssh -i ${KEY_FILE_NAME} -W %h:%p ${USERNAME}@${HOST}" root@${NODE} hostname
done
