![CrowdStrike Logo (Light)](https://raw.githubusercontent.com/CrowdStrike/.github/main/assets/cs-logo-light-mode.png#gh-light-mode-only)
![CrowdStrike Logo (Dark)](https://raw.githubusercontent.com/CrowdStrike/.github/main/assets/cs-logo-dark-mode.png#gh-dark-mode-only)
# CrowdStrike Falcon on AWS PrivateLink

This guide explains how to connect AWS workloads to the CrowdStrike Falcon
sensor cloud over AWS PrivateLink using the newer cross-region connectivity
model. It replaces designs that previously required customer-managed
inter-region routing to reach Falcon PrivateLink services from workload Regions
outside the Falcon cloud home Region.

This repo showcases three small-scale labs that look at common cloud-native
architecture patterns unlocked by cross-region PrivateLink. Use them to
understand the network topology options and get ideas for scaling the pattern
into your own AWS environment. These examples are learning deployments, not
production-ready modules, and they are not the only valid designs.

## Table of contents

- [What PrivateLink provides](#what-privatelink-provides)
- [What cross-region connectivity changes](#what-cross-region-connectivity-changes)
- [Falcon cloud home Regions](#falcon-cloud-home-regions)
- [Design considerations](#design-considerations)
- [Lab guide index](#lab-guide-index)
- [Architecture picker](#architecture-picker)
- [Unsupported Regions](#unsupported-regions)

## What PrivateLink provides

AWS PrivateLink lets workloads in a VPC reach a provider service through
private interface endpoints instead of public internet paths. For Falcon
sensors, PrivateLink facilitates the core sensor communication needed for the
sensor to operate, including sensor telemetry. It does not provide private
connectivity for CrowdStrike APIs or other non-sensor telemetry flows.

## What cross-region connectivity changes

Historically, a PrivateLink consumer endpoint and the provider endpoint service
had to be in the same AWS Region. For CrowdStrike customers whose Falcon CID is
hosted in one Region but whose AWS workloads run elsewhere, customers needed
to establish inter-region routing to reach the PrivateLink endpoints. That made
networking designs more complicated, especially in multi-account and
multi-Region environments.

Cross-region PrivateLink removes the anchor VPC requirement for supported
Regions. Your Falcon CID still determines which CrowdStrike cloud and home
Region the endpoint service is hosted in. The difference is that customers can
now create PrivateLink connections to Falcon from any AWS commercial Region
where AWS supports cross-region connectivity.

## Falcon cloud home Regions

| Falcon cloud | Endpoint service home Region |
|---|---|
| US-1 | `us-west-1` |
| US-2 | `us-west-2` |
| EU-1 | `eu-central-1` |

Use the Falcon cloud that matches the CID you deploy sensors against. The
endpoint service home Region is not a deployment preference; it is determined
by the Falcon cloud for that CID.

The complete endpoint service and hostname matrix is in
[docs/vpc-endpoints-reference.md](docs/vpc-endpoints-reference.md).

## Design considerations

### AWS Region support

The Falcon platform provides PrivateLink connectivity for AWS commercial
Regions where AWS supports cross-region PrivateLink connectivity. This guide
focuses on those AWS commercial Regions. Falcon PrivateLink is not supported
in GovCloud today. See
[Unsupported Regions](#unsupported-regions) for the commercial Regions that
are not covered by this guide.

Some AWS Regions are opt-in Regions. If a deployment uses an opt-in Region, the
relevant AWS account must enable that Region before it can create or target
cross-region PrivateLink resources there.

### Availability

Use at least two Availability Zones for high availability. Deploying endpoint
network interfaces across multiple AZs gives workloads more than one private
path to the Falcon service if an AZ-level component becomes unavailable.

### DNS

PrivateLink is DNS-driven. Workloads must resolve the `cloudsink.net` Falcon
sensor hostnames to the private IP addresses of the correct interface
endpoints. Many customers use Route 53 private hosted zones with aliases to the
VPC endpoints for the three configured Falcon endpoints. This can also be done
in other ways for organizations that manage private DNS outside Route 53.

### Falcon sensor installation

In environments with no internet connectivity, traditional scripts that
download and install the Falcon sensor directly from CrowdStrike APIs will not
work from the private workload. Customers usually need a private installation
path, such as baking the sensor into golden image pipelines or seeding the
sensor installer into S3 buckets and downloading it over S3 endpoints.

### AWS account whitelisting

Customers need to raise a ticket with CrowdStrike support to have their AWS
account IDs whitelisted to their respective regional VPC endpoints before the
connection can be initiated. If the account is not whitelisted, the endpoint
service can appear unavailable when trying to initiate the connection.

### Quotas and cost

Cross-region endpoints count against the same interface endpoint quotas as
other interface endpoints in the VPC. They also incur interface endpoint hourly
and data processing charges.

### IAM and organization controls

Cross-region PrivateLink is gated by the `vpce:AllowMultiRegion`
permission-only action. A customer identity policy must allow it, and an AWS
Organizations service control policy must not deny it. If either layer blocks
the action, in-region PrivateLink can still work while cross-region endpoint
creation fails.

Customers can also use the `ec2:VpceServiceRegion` condition key to restrict
which remote service Regions an IAM principal may target when creating VPC
endpoints.

## Lab guide index

Each lab creates an Amazon Linux 2023 EC2 instance to demonstrate sensor
deployment in a private network. The instances have no internet gateway or NAT
gateway path, which shows how Falcon sensor connectivity can work in an
environment without internet egress.

These are three cloud-native examples to help you reason about common network
topologies. They are starting points for design, not limits on how PrivateLink
can be used.

### [Architecture 01 - Per-VPC endpoints](docs/architecture-01-per-vpc.md)

This design is for simpler, smaller-footprint environments that do not require
complicated network routing architecture. Each VPC initiates its own
PrivateLink connection to the Falcon platform.

Pick this when each VPC can own its own Falcon PrivateLink connection and the
resulting per-VPC AWS account whitelisting workflow is acceptable.

### [Architecture 02 - Shared VPC](docs/architecture-02-shared-vpc.md)

This design is for AWS environments that use a shared VPC architecture. A hub
or owner account initiates the PrivateLink connection, then shares subnets to
workload accounts using AWS Resource Access Manager. AWS documents this as
[VPC subnet sharing](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-sharing.html).
Workloads launched in the shared subnets can use the shared VPC's Falcon
PrivateLink connectivity.

Pick this when you are already running, or plan to run, the AWS shared VPC
pattern and want workload accounts to inherit centrally managed Falcon network
connectivity.

### [Architecture 03 - TGW + Route 53 Profiles](docs/architecture-03-tgw-profiles.md)

This design is for enterprise hub-and-spoke environments that use AWS Transit
Gateway for VPC-to-VPC routing. Spoke VPCs keep their own network ownership,
while a hub networking account owns the Falcon PrivateLink endpoints and shared
DNS.

Before cross-region PrivateLink, this pattern typically required inter-region
TGW or VPC peering back to an endpoint VPC in the Falcon home Region. With
cross-region PrivateLink, the hub endpoint VPC can live in the same Region as
the spokes, and PrivateLink handles the connection to the Falcon home Region.

Pick this when TGW is already your standard enterprise connectivity pattern and
you want to modernize it for cross-region Falcon PrivateLink.

## Architecture picker

| Question | Per-VPC | Shared VPC | TGW + Profiles |
|---|:---:|:---:|:---:|
| Small footprint or first proof of concept | Yes |  |  |
| Each VPC should own its PrivateLink connection | Yes |  |  |
| Workloads use shared VPC subnets |  | Yes |  |
| Workloads must stay in their own VPCs | Yes |  | Yes |
| Existing TGW hub-and-spoke network |  |  | Yes |
| Central network team owns Falcon connectivity |  | Yes | Yes |
| Reduce account whitelisting volume across many accounts |  | Yes | Yes |

## Unsupported Regions

The following commercial AWS Regions are not supported by this cross-region
PrivateLink guide as of May 2026:

| Region | Name |
|---|---|
| `ap-southeast-5` | Asia Pacific (Malaysia) |
| `ap-southeast-7` | Asia Pacific (Thailand) |
| `mx-central-1` | Mexico (Central) |

Workloads in unsupported Regions that require PrivateLink connectivity will
require inter-region routing configurations until AWS provides cross-region
PrivateLink support for these Regions and CrowdStrike follows suit by making
them available. Until then, we recommend raising a feature request with AWS to
help accelerate support for these Regions.
