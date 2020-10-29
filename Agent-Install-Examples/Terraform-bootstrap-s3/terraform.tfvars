#Used only if you do not have a AWS profile set (recommended to use a creds file or profile)
#Key variables are commented out of the network.tf file
#aws_access_key = "place access key here"
#aws_secret_key = "place secret key here"

VPCName = "CRWD-Test-VPC"

# Name to apply to the stack
StackName = "crwd-test-stack"

# CIDR of the VPC we will create
VPCCIDR = "10.0.0.0/16"

WebSRV1_AZ1_Trust = "10.0.2.50"
WebCIDR_TrustBlock1 = "10.0.2.0/24"
WebCIDR_UntrustBlock1 = "10.0.1.0/24"

aws_region = "Add Region"
# Name of the S3 Bucket that contains the falcon sensor installation package
bucket_name = "Add Unique s3 Bucket Name"

ServerKeyName = "Add Region Keypair"

crwd_cid = "Place CID Here"

#CrowdStrike Sensor Version (ex falcon-sensor_5.27.0-9104_amd64.deb)
crwd_sensor = "falcon-sensor_5.43.0-10803_amd64.deb"


