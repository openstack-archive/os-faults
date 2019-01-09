#!/bin/bash
# DevStack plugin to install os-faults

LIBDIR=${DEST}/os-faults/devstack/lib

source ${LIBDIR}/os-faults

if [[ "$1" == "stack" && "$2" == "install" ]]; then
    echo_summary "Installing OS-Faults"
    install_os_faults
elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
    echo_summary "Configuring OS-Faults"
    configure_os_faults
fi
