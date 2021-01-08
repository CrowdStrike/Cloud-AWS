#!/bin/bash
# TODO: support of installation tokens
# TODO: test on oracle linux
# TODO: explore options for architecture support beyond x86_64
# TODO: Unify external variable names

print_usage() {
    cat <<EOF
Script to install and set-up CrowdStrike Falcon sensor from AWS SSM.

This script shall be issued automatically by amazon-ssm-agent. No arguments required.

Falcon credentials are needed to download falcon sensor. These may be supplied by
the way of env variables or in AWS SSM Parameter Store. Following variables may be used.

    - FalconCID
    - CS_API_GATEWAY_CLIENT_ID
    - CS_API_GATEWAY_CLIENT_SECRET
EOF
}


CS_API_BASE=${CS_API_BASE:-api.crowdstrike.com}

main() {
    if [ -n "$1" ]; then
        print_usage
        exit 1
    fi
    echo -n 'Falcon Sensor Install  ... '; cs_sensor_install;  echo '[ Ok ]'
    echo -n 'Falcon Sensor Register ... '; cs_sensor_register; echo '[ Ok ]'
    echo -n 'Falcon Sensor Restart  ... '; cs_sensor_restart;  echo '[ Ok ]'
    echo 'Falcon Sensor deployed successfully.'
}

cs_sensor_register() {
    /opt/CrowdStrike/falconctl -s --cid="${cs_falcon_cid}"
}

cs_sensor_restart() {
    if type service >/dev/null 2>&1; then
        service falcon-sensor restart
    elif type systemctl >/dev/null 2>&1; then
        systemctl restart falcon-sensor
    else
        die "Could not restart falcon sensor"
    fi
}

cs_sensor_install() {
    tempdir=$(mktemp -d)

    tempdir_cleanup() { rm -rf "$tempdir"; }; trap tempdir_cleanup EXIT

    package_name=$(cs_sensor_download "$tempdir")
    os_install_package "$package_name"

    tempdir_cleanup
}

cs_sensor_download() {
    destination_dir="$1"

    existing_installers=$(
        curl -s -L -G "https://$CS_API_BASE/sensors/combined/installers/v1" \
             --data-urlencode "filter=os:\"$cs_os_name\"" \
             -H "Authorization: Bearer $cs_falcon_oauth_token"
    )

    if echo "$existing_installers" | grep "denied"; then
        die "Invalid Access Token: $cs_falcon_oauth_token"
    fi

    sha_list=$(echo "$existing_installers" | json_value "sha256")
    if [ -z "$sha_list" ]; then
        die "No sensor found for with OS Name: $cs_os_name"
    fi

    INDEX=1
    if [ -n "$cs_os_version" ]; then
        found=0
        IFS='
'
        for l in $(echo "$existing_installers" | json_value "os_version"); do
            l=$(echo "$l" | sed 's/ *$//g' | sed 's/^ *//g')

            if echo "$l" | grep -q '/'; then
                # Sensor for Ubuntu has l="14/16/18/20"
                for v in $(echo "$l" | tr '/' '\n'); do
                    if [ "$v" -eq "$cs_os_version" ]; then
                        l="$v"
                        break
                    fi
                done
            fi

	          if [ "$l" = "$cs_os_version" ]; then
                found=1
                break
            fi
	          INDEX=$((INDEX+1))
        done
        if [ $found = 0 ]; then
            die "Unable to locate matching sensor: $cs_os_name@$cs_os_version"
        fi
    fi

    sha=$(echo "$existing_installers" | json_value "sha256" "$INDEX" \
              | sed 's/ *$//g' | sed 's/^ *//g')
    if [ -z "$sha" ]; then
        die "Unable to identify a sensor installer matching: $cs_os_name@$cs_os_version"
    fi
    file_type=$(echo "$existing_installers" | json_value "file_type" "$INDEX" | sed 's/ *$//g' | sed 's/^ *//g')

    installer="${destination_dir}/falcon-sensor.${file_type}"
    curl -s -L "https://$CS_API_BASE/sensors/entities/download-installer/v1?id=$sha" \
         -H "Authorization: Bearer $cs_falcon_oauth_token" -o "$installer"
    echo "$installer"
}

os_install_package() {
    pkg="$1"

    rpm_install_package() {
        pkg="$1"

        cs_falcon_gpg_import

        if type dnf > /dev/null 2>&1; then
            dnf install -q -y "$pkg" || rpm -ivh --nodeps "$pkg"
        elif type yum > /dev/null 2>&1; then
            yum install -q -y "$pkg" || rpm -ivh --nodeps "$pkg"
        elif type zypper > /dev/null 2>&1; then
            zypper --quiet install -y "$pkg" || rpm -ivh --nodeps "$pkg"
        else
            rpm -ivh --nodeps "$pkg"
        fi
    }

    case "${os_name}" in
        Amazon)
            rpm_install_package "$pkg"
            ;;
        CentOS)
            rpm_install_package "$pkg"
            ;;
        Debian)
            DEBIAN_FRONTEND=noninteractive apt-get -qq install -y "$pkg" > /dev/nul
            ;;
        Oracle)
            rpm_install_package "$pkg"
            ;;
        RHEL)
            rpm_install_package "$pkg"
            ;;
        SLES)
            rpm_install_package "$pkg"
            ;;
        Ubuntu)
            DEBIAN_FRONTEND=noninteractive apt-get -qq install -y "$pkg" > /dev/null
            ;;
        *)
            die "Unrecognized OS: ${os_name}";;
    esac
}

aws_ssm_parameter() {
    local param_name="$1"

    hmac_sha256() {
        key="$1"
        data="$2"
        echo -n "$data" | openssl dgst -sha256 -mac HMAC -macopt "$key" | sed 's/^.* //'
    }

    api_endpoint="AmazonSSM.GetParameters"
    iam_role="$(curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/)"
    _security_credentials=$(curl -s "http://169.254.169.254/latest/meta-data/iam/security-credentials/$iam_role")
    access_key_id="$(echo "$_security_credentials" | grep AccessKeyId | sed -e 's/  "AccessKeyId" : "//' -e 's/",$//')"
    access_key_secret="$(echo "$_security_credentials" | grep SecretAccessKey | sed -e 's/  "SecretAccessKey" : "//' -e 's/",$//')"
    security_token="$(echo "$_security_credentials" | grep Token | sed -e 's/  "Token" : "//' -e 's/",$//')"
    datetime=$(date -u +"%Y%m%dT%H%M%SZ")
    date=$(date -u +"%Y%m%d")
    request_data='{"Names":["'"${param_name}"'"]}'
    request_data_dgst=$(echo -n "$request_data" | openssl dgst -sha256 | awk -F' ' '{print $2}')
    request_dgst=$(
        cat <<EOF | head -c -1 | openssl dgst -sha256 | awk -F' ' '{print $2}'
POST
/

content-type:application/x-amz-json-1.1
host:ssm.${aws_my_region}.amazonaws.com
x-amz-date:$datetime
x-amz-security-token:$security_token
x-amz-target:$api_endpoint

content-type;host;x-amz-date;x-amz-security-token;x-amz-target
$request_data_dgst
EOF
    )
    dateKey=$(hmac_sha256 key:"AWS4$access_key_secret" "$date")
    dateRegionKey=$(hmac_sha256 "hexkey:$dateKey" "${aws_my_region}")
    dateRegionServiceKey=$(hmac_sha256 "hexkey:$dateRegionKey" ssm)
    hex_key=$(hmac_sha256 "hexkey:$dateRegionServiceKey" "aws4_request")

    signature=$(
        cat <<EOF | head -c -1 | openssl dgst -sha256 -mac HMAC -macopt "hexkey:$hex_key" | awk -F' ' '{print $2}'
AWS4-HMAC-SHA256
$datetime
$date/${aws_my_region}/ssm/aws4_request
$request_dgst
EOF
    )

    response=$(
        curl -s "https://ssm.${aws_my_region}.amazonaws.com/" \
            -H "Authorization: AWS4-HMAC-SHA256 \
            Credential=$access_key_id/$date/${aws_my_region}/ssm/aws4_request, \
            SignedHeaders=content-type;host;x-amz-date;x-amz-security-token;x-amz-target, \
            Signature=$signature" \
            -H "x-amz-security-token: $security_token" \
            -H "x-amz-target: $api_endpoint" \
            -H "content-type: application/x-amz-json-1.1" \
            -d "$request_data" \
            -H "x-amz-date: $datetime"
            )
    if ! echo "$response" | grep -q '^.*"InvalidParameters":\[\].*$'; then
        die "Unexpected response from AWS SSM Parameter Store: $response"
    elif ! echo "$response" | grep -q '^.*'"${param_name}"'.*$'; then
        die "Unexpected response from AWS SSM Parameter Store: $response"
    fi
    echo "$response"
}

json_value() {
    KEY=$1
    num=$2
    awk -F"[,:}]" '{for(i=1;i<=NF;i++){if($i~/'"$KEY"'\042/){print $(i+1)}}}' | tr -d '"' | sed -n "${num}p"
}

die() {
    echo "Fatal error: $*" >&2
    exit 1
}

cs_falcon_gpg_import() {
    tempfile=$(mktemp)
    cat > "$tempfile" <<EOF
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: GnuPG v2.0.22 (GNU/Linux)

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
OY0=
=rjt/
-----END PGP PUBLIC KEY BLOCK-----
EOF
    rpm --import "$tempfile"
    rm "$tempfile"
}


set -e


os_name=$(
    # returns either: Amazon, Ubuntu, CentOS, RHEL, or SLES
    # lsb_release is not always present
    name=$(cat /etc/*release | grep ^NAME= | awk -F'=' '{ print $2 }' | sed "s/\"//g;s/Red Hat.*/RHEL/g;s/ Linux$//g")
    if [ -z "$name" ]; then
        if lsb_release -s -i | grep -q ^RedHat; then
            name="RHEL"
        fi
    fi
    if [ -z "$name" ]; then
        die "Cannot recognise operating system"
    fi

    echo $name
)

os_version=$(
    version=$(cat /etc/*release | grep VERSION_ID= | awk '{ print $1 }' | awk -F'=' '{ print $2 }' | sed "s/\"//g")
    if [ -z "$version" ] && type rpm > /dev/null 2>&1; then
        # older systems may have *release files of different form
        version=$(rpm -qf /etc/redhat-release --queryformat '%{VERSION}' | sed 's/\([[:digit:]]\+\).*/\1/g')
    fi
    if [ -z "$version" ]; then
        cat /etc/*release >&2
        die "Could not determine distribution version"
    fi
    echo "$version"
)

cs_os_name=$(
    # returns OS name as recognised by CrowdStrike Falcon API
    case "${os_name}" in
        Amazon)  echo "Amazon Linux";;
        CentOS)  echo "RHEL/CentOS/Oracle";;
        Debian)  echo "Debian";;
        Oracle)  echo "RHEL/CentOS/Oracle";;
        RHEL)    echo "RHEL/CentOS/Oracle";;
        SLES)    echo "SLES";;
        Ubuntu)  echo "Ubuntu";;
        *)       die "Unrecognized OS: ${os_name}";;
    esac
)

cs_os_version=$(
    echo "$os_version" | awk -F'.' '{print $1}'
)

aws_my_region=$(
    curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone | sed s/.$//
)

cs_falcon_client_id=$(
    aws_ssm_parameter "CS_API_GATEWAY_CLIENT_ID" | json_value Value 1
)

cs_falcon_client_secret=$(
    aws_ssm_parameter "CS_API_GATEWAY_CLIENT_SECRET" | json_value Value 1
)

cs_falcon_cid=$(
    aws_ssm_parameter "FalconCID" | json_value Value 1
)

cs_falcon_oauth_token=$(
    token_result=$(curl -X POST -s -L "https://$CS_API_BASE/oauth2/token" \
                       -H 'Content-Type: application/x-www-form-urlencoded; charset=utf-8' \
                       -d "client_id=$cs_falcon_client_id&client_secret=$cs_falcon_client_secret")
    token=$(echo "$token_result" | json_value "access_token" | sed 's/ *$//g' | sed 's/^ *//g')
    if [ -z "$token" ]; then
        die "Unable to obtain CrowdStrike Falcon OAuth Token. Response was $token_result"
    fi
    echo "$token"
)


main "$@"
