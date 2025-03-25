#!/bin/bash

export FALCON_CLIENT_ID="$(aws secretsmanager get-secret-value --secret-id "$SECRET_ID" --query SecretString --output text | jq -r .FALCON_CLIENT_ID)"
export FALCON_CLIENT_SECRET="$(aws secretsmanager get-secret-value --secret-id "$SECRET_ID" --query SecretString --output text | jq -r .FALCON_CLIENT_SECRET)"

curl -L https://raw.githubusercontent.com/crowdstrike/falcon-scripts/main/bash/install/falcon-linux-install.sh | bash
