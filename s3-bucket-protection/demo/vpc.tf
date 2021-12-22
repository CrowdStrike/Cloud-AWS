#resources
resource "aws_vpc" "vpc" {
  cidr_block = var.cidr_vpc
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = {
    "Environment" = "${var.environment_tag} (${var.unique_id})" 
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.vpc.id
  tags = {
    "Environment" = "${var.environment_tag} (${var.unique_id})"
  }
}

resource "aws_subnet" "subnet_public" {
  vpc_id = aws_vpc.vpc.id
  cidr_block = var.cidr_subnet
  map_public_ip_on_launch = "true"
  availability_zone = "${var.region}a"
  tags = {
    "Environment" = "${var.environment_tag} (${var.unique_id})" 
  }
}

resource "aws_route_table" "rtb_public" {
  vpc_id = aws_vpc.vpc.id

  route {
      cidr_block = "0.0.0.0/0"
      gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    "Environment" = "${var.environment_tag} (${var.unique_id})" 
  }
}

resource "aws_route_table_association" "rta_subnet_public" {
  subnet_id      = aws_subnet.subnet_public.id
  route_table_id = aws_route_table.rtb_public.id
}

resource "aws_security_group" "sg_22" {
  name = "${var.unique_id}_${var.ssh_group_name}"
  vpc_id = aws_vpc.vpc.id

  # SSH access from the VPC
  ingress {
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = [var.trusted_ip]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    "Environment" = "${var.environment_tag} (${var.unique_id})"
  }
}

