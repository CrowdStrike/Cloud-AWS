#!/bin/bash

get_output () {
    echo $(/opt/CrowdStrike/falconctl -g --${1})
}

validate_param () {
    local param_name=$1
    local value=$2
    if [[ $(get_output ${param_name}) =~ =${value}\. ]]; then
        return 0
    fi
    echo "$param_name mismatch"
    return 1
}

validate_param tags ${SSM_AWS_ENVIRONMENT_TAG}