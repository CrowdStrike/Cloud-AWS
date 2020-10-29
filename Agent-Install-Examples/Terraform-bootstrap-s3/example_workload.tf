resource "random_id" "bootstraprole" {
  byte_length = 3
}

resource "random_id" "bootstrappolicy" {
  byte_length = 3
}

resource "aws_iam_role" "workload-role" {
  name = "workload-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
      "Service": "ec2.amazonaws.com"
    },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "workload-policy" {
  #name = "workload-policy${random_id.bootstrappolicy.hex}"
  name = "CS-Workload-IAM-Policy"
  role = aws_iam_role.workload-role.id

  policy = <<EOF
{
  "Version" : "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObjectAcl",
                "s3:GetObject",
                "s3:ListBucket",
                "s3:GetBucketPolicy"]
      ,
      "Resource": [
        "arn:aws:s3:::${aws_s3_bucket.sensor-file-bucket.bucket}",
        "arn:aws:s3:::${aws_s3_bucket.sensor-file-bucket.bucket}/*"
      ]
    },
    {
    "Effect": "Allow",
    "Action": [
                "s3:GetAccessPoint",
                "s3:ListAccessPoints"
            ],
    "Resource": "*"
    }
  ]
}
EOF
}

#Security Group
resource "aws_security_group" "webserver" {
  name = "webserver"
  description = "linux web server"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port = "80"
    to_port = "80"
    protocol = "tcp"
    cidr_blocks = [
      "${var.VPCCIDR}"]
  }

  ingress {
    from_port = "443"
    to_port = "443"
    protocol = "tcp"
    cidr_blocks = [
      "${var.VPCCIDR}"]
  }

  ingress {
    from_port = "22"
    to_port = "22"
    protocol = "tcp"
    cidr_blocks = [
      "${var.VPCCIDR}"]
  }
  ingress {
    from_port = "22"
    to_port = "22"
    protocol = "tcp"
    cidr_blocks = [
      "0.0.0.0/0"]
  }

  egress {
    from_port = "0"
    to_port = "0"
    protocol = "-1"
    cidr_blocks = [
      "0.0.0.0/0"]
  }
}

resource "aws_iam_instance_profile" "workload-instanceprofile" {
  name = "workload-instanceprofile"
  role = aws_iam_role.workload-role.name
  path = "/"
}

resource "aws_vpc_endpoint" "private-s3" {
  vpc_id = aws_vpc.main.id
  #service_name = "com.amazonaws.us-west-1.s3"
  service_name = "com.amazonaws.${var.aws_region}.s3"
  route_table_ids = [
    "${aws_route_table.private.id}"]

  policy = <<POLICY
{
    "Statement": [
        {
            "Action": "*",
            "Effect": "Allow",
            "Resource": "*",
            "Principal": "*"
        }
    ]
}
POLICY
}


resource "aws_network_interface" "web1-int" {
  subnet_id = aws_subnet.AZ1-TRUST.id
  security_groups = [
    "${aws_security_group.webserver.id}"]
  source_dest_check = false
  private_ips = [
    "${var.WebSRV1_AZ1_Trust}"]
}


resource "aws_instance" "web1" {
  depends_on = [
    aws_s3_bucket_object.sensor-file]
  ami = var.UbuntuRegionMap[var.aws_region]
  iam_instance_profile = aws_iam_instance_profile.workload-instanceprofile.name
  instance_type = "t2.micro"
  key_name = var.ServerKeyName
  tags = {
    Name = "Svr-Falcon-From-S3"
  }
  monitoring = false



  network_interface {
    device_index = 0
    network_interface_id = aws_network_interface.web1-int.id
  }

  user_data = base64encode(join("", list(
  "#! /bin/bash\n",
  "exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1\n",
  "ls\n",
  "sudo apt-get update\n",
  "cd /home/ubuntu\n",
  "sudo apt install python-pip -y --force-yes\n",
  "sudo pip install awscli\n",
  "sudo aws s3 ls\n",
  "sudo aws s3 cp s3://${var.bucket_name}/sensor/${var.crwd_sensor} /home/ubuntu\n",
  "sudo dpkg -i ${var.crwd_sensor}\n",
  "sudo apt install -f -y\n",
  "sudo dpkg -i ${var.crwd_sensor}\n",
  "sudo /opt/CrowdStrike/falconctl -s --cid=${var.crwd_cid}\n",
  "sudo systemctl start falcon-sensor\n"
  )))
}