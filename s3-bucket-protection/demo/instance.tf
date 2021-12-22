data "aws_ami" "amazon-linux-2" {
 most_recent = true
 owners = ["amazon"]

 filter {
   name   = "owner-alias"
   values = ["amazon"]
 }

 filter {
   name   = "name"
   values = ["amzn2-ami-hvm*"]
 }
}

resource "aws_instance" "amzn_instance" {
	ami = data.aws_ami.amazon-linux-2.id
	instance_type = var.instance_type
	iam_instance_profile = aws_iam_instance_profile.ec2-ssm-role-profile.name
	key_name = var.instance_key_name
	vpc_security_group_ids = [aws_security_group.sg_22.id]
	subnet_id = aws_subnet.subnet_public.id
	user_data = <<-EOF
        #!/bin/bash
        TESTS="/home/ec2-user/testfiles"
        echo "export BUCKET=s3://${aws_s3_bucket.bucket.id}" >> /etc/profile
        echo 'figlet -w 220 -f cricket CrowdStrike' >> /home/ec2-user/.bash_profile
        echo 'echo -e "Welcome to the CrowdStrike Falcon S3 Bucket Protection demo environment!\n"' >> /home/ec2-user/.bash_profile
        echo 'echo -e "The name of your test bucket is ${aws_s3_bucket.bucket.id} and is\navailable in the environment variable BUCKET.\n"' >> /home/ec2-user/.bash_profile
        echo 'echo -e "There are test files in the testfiles folder. \nUse these to test the lambda trigger on bucket uploads. \nNOTICE: Files labeled \`malicious\` are DANGEROUS!\n"' >> /home/ec2-user/.bash_profile
        echo 'echo -e "Use the command \`upload\` to upload all of the test files to your demo bucket.\n"' >> /home/ec2-user/.bash_profile
        echo 'echo -e "You can view the contents of your bucket with the command \`list-bucket\`.\n"' >> /home/ec2-user/.bash_profile
        echo 'echo -e "Use the command \`get-findings\` to view all findings for your demo bucket.\n"' >> /home/ec2-user/.bash_profile
        amazon-linux-extras install epel -y
        yum install -y figlet jq
        cd /home/ec2-user
        mkdir $TESTS
        wget -O /usr/share/figlet/cricket.flf https://raw.githubusercontent.com/adamchainz/SublimeFiglet/main/pyfiglet/fonts/cricket.flf
        # SAFE EXAMPLES
        wget -O $TESTS/unscannable1.png https://adversary.crowdstrike.com/assets/images/Adversaries_Ocean_Buffalo.png
        wget -O $TESTS/unscannable2.jpg https://www.crowdstrike.com/blog/wp-content/uploads/2018/04/April-Adversary-Stardust.jpg
        cp /usr/bin/whoami $TESTS/safe1.bin
        cp /usr/sbin/ifconfig $TESTS/safe2.bin
        # MALICIOUS EXAMPLES
        wget -O malqueryinator.py https://raw.githubusercontent.com/CrowdStrike/falconpy/main/samples/malquery/malqueryinator.py
        python3 -m pip install crowdstrike-falconpy
        python3 malqueryinator.py -v "%s?action=CmdRes&u=%I64u&err=kill" -t wide -f malicious.zip -e 3 -k ${var.falcon_client_id} -s ${var.falcon_client_secret}
        unzip -d $TESTS -P infected malicious.zip
        C=0
        for f in $(ls $TESTS --hide=**.*)
        do
          ((C=C+1))
          mv $TESTS/$f $TESTS/malicious$C.bin
        done
        rm malicious.zip
        chown -R ec2-user:ec2-user $TESTS
        rm malicious.zip
        rm malqueryinator.py
        # HELPER SCRIPTS
        wget -O /usr/local/bin/get-findings https://raw.githubusercontent.com/CrowdStrike/Cloud-AWS/main/s3-bucket-protection/bin/get-findings.sh
        wget -O /usr/local/bin/upload https://raw.githubusercontent.com/CrowdStrike/Cloud-AWS/main/s3-bucket-protection/bin/upload.sh
        wget -O /usr/local/bin/list-bucket https://raw.githubusercontent.com/CrowdStrike/Cloud-AWS/main/s3-bucket-protection/bin/list-bucket.sh
        chmod +x /usr/local/bin/*
		EOF
 tags = {
	Name = "CrowdStrike S3 Bucket Protection Demo" 
  }
}
