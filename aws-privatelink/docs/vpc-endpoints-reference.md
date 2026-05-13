![CrowdStrike Logo (Light)](https://raw.githubusercontent.com/CrowdStrike/.github/main/assets/cs-logo-light-mode.png#gh-light-mode-only)
![CrowdStrike Logo (Dark)](https://raw.githubusercontent.com/CrowdStrike/.github/main/assets/cs-logo-dark-mode.png#gh-dark-mode-only)
# VPC Endpoints Reference - CrowdStrike PrivateLink

Customers need to establish PrivateLink connectivity to the CrowdStrike Falcon
endpoint services in the commercial AWS Region that matches their Falcon cloud.
Use the Falcon cloud that matches the CID you deploy sensors against.

## Table of contents

- [Endpoint service matrix](#endpoint-service-matrix)

## Endpoint service matrix

| Cloud | DNS name | Service | VPC endpoint service name | Home Region |
|---|---|---|---|---|
| US-1 | `ts01-b.cloudsink.net` | Sensor proxy | `com.amazonaws.vpce.us-west-1.vpce-svc-08744dea97b26db5d` | `us-west-1` |
| US-1 | `lfodown01-b.cloudsink.net` | Download server | `com.amazonaws.vpce.us-west-1.vpce-svc-0f9d8ca86ddcb7106` | `us-west-1` |
| US-1 | `lfoup01-b.cloudsink.net` | Upload server | `com.amazonaws.vpce.us-west-1.vpce-svc-0fa888d7b9e4130f4` | `us-west-1` |
| US-2 | `ts01-gyr-maverick.cloudsink.net` | Sensor proxy | `com.amazonaws.vpce.us-west-2.vpce-svc-08a5bb05d337fd834` | `us-west-2` |
| US-2 | `lfodown01-gyr-maverick.cloudsink.net` | Download server | `com.amazonaws.vpce.us-west-2.vpce-svc-0e11def2d8620ae74` | `us-west-2` |
| US-2 | `lfoup01-gyr-maverick.cloudsink.net` | Upload server | `com.amazonaws.vpce.us-west-2.vpce-svc-074a82fde584744da` | `us-west-2` |
| EU-1 | `ts01-lanner-lion.cloudsink.net` | Sensor proxy | `com.amazonaws.vpce.eu-central-1.vpce-svc-0eb7b6ca4b7271385` | `eu-central-1` |
| EU-1 | `lfodown01-lanner-lion.cloudsink.net` | Download server | `com.amazonaws.vpce.eu-central-1.vpce-svc-0340142b9ab8fc564` | `eu-central-1` |
| EU-1 | `lfoup01-lanner-lion.cloudsink.net` | Upload server | `com.amazonaws.vpce.eu-central-1.vpce-svc-0148ff0159e9419dd` | `eu-central-1` |
