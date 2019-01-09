#!/bin/bash
# DevStack extras script to install os-faults

# Save trace setting
XTRACE=$(set +o | grep xtrace)
set -o xtrace

source ${DEST}/os-faults/devstack/lib/os-faults

if [[ "$1" == "stack" && "$2" == "post-config" ]]; then
    echo_summary "Configuring OS-Faults"
    configure_os_faults
fi

# Restore xtrace
$XTRACE
