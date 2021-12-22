#!/bin/bash
echo 'Uploading test files, please wait...'
for i in $(ls /home/ec2-user/testfiles)
do
    aws s3 cp /home/ec2-user/testfiles/$i s3://ebfbddee-s3-protected-bucket/$i
done
echo 'Upload complete. Check CloudWatch logs or use the get-findings command for scan results.'