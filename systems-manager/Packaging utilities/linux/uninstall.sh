#!/bin/bash

main() {
    falcon_sensor_uninstall
    falcon_sensor_remove_cache
    # TODO: remove from falcon console
}

falcon_sensor_uninstall() {
    if type dnf > /dev/null 2>&1; then
        rpm -q --quiet falcon-sensor && dnf remove -q -y falcon-sensor
    elif type yum > /dev/null 2>&1; then
        rpm -q --quiet falcon-sensor && yum remove -y falcon-sensor
    elif type apt-get > /dev/null 2>&1; then
        apt-get -y purge falcon-sensor
    elif type zypper > /dev/null 2>&1; then
        zypper -n remove falcon-sensor
    elif type rpm > /dev/null 2>&1; then
        rpm -e falcon-sensor
    else
        die "Cannot uninstall package. Unrecognised packaging system"
    fi
}

falcon_sensor_remove_cache() {
    rm -rf /var/lib/amazon/ssm/packages/Crowd*
    rm -rf /var/lib/amazon/ssm/manifests/Crowd*
}

die() {
    echo "Fatal error: $*"
    exit 1
}

main "$@"
