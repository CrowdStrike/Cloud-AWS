#Linux Cloud Workload Bootstrap Sensor S3
provider "aws" {
  profile = "default"
  #access_key = var.aws_access_key
  #secret_key = var.aws_secret_key
  region     = var.aws_region
}

resource "aws_vpc" "main" {
  cidr_block       = var.VPCCIDR
  instance_tenancy = "default"
  tags = {
    Name = "CRWD-Test-VPC"}
}

#Create Internet Gateway
resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id
  tags = {
    Name = "IGW CRWD Test"}

}
# Create NAT GW
resource "aws_nat_gateway" "nat_gw" {
  allocation_id = aws_eip.NAT_GW.id
  subnet_id     = aws_subnet.AZ1-UNTRUST.id
  depends_on    = [aws_internet_gateway.gw]

  tags = {
    Name = "gw NAT"
  }
}

# Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  tags = {
    Name = "Public"}

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id
  tags = {
    Name = "Private"}

  route {
    cidr_block     = "0.0.0.0/0"
    #nat_gateway_id = aws_nat_gateway.nat_gw.id
    gateway_id = aws_internet_gateway.gw.id

  }
}
resource "aws_route_table_association" "subnetroute5" {
  subnet_id      = aws_subnet.AZ1-TRUST.id
  route_table_id = aws_route_table.private.id
}

# Subnets
resource "aws_subnet" "AZ1-TRUST" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.WebCIDR_TrustBlock1
  availability_zone = data.aws_availability_zones.available.names[0]
  tags = {
    Name = "Trust"}
}
resource "aws_subnet" "AZ1-UNTRUST" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.WebCIDR_UntrustBlock1
  availability_zone = data.aws_availability_zones.available.names[0]
  tags = {
    Name = "Untrust"}

}

# NAT GW Public IP Association
resource "aws_eip" "NAT_GW" {
  vpc   = true
  depends_on = [aws_vpc.main, aws_internet_gateway.gw]
}

# Subnet Route Table Association

resource "aws_route_table_association" "subnetroute1" {
  subnet_id      = aws_subnet.AZ1-UNTRUST.id
  route_table_id = aws_route_table.public.id
}